const express = require("express");
const pool = require("./db");
const { port, FRONTEND_ORIGIN, frontendOrigin } = require("./config");
const auth = require("./auth");

const authenticate = auth.authenticate;
const requireRoles = auth.requireRoles;
const requireAuth =
  auth.requireAuth ||
  ((req, res, next) => {
    authenticate(req, res, (err) => {
      if (err) return next(err);
      if (!req.user && req.identity) {
        req.user = req.identity;
      }
      next();
    });
  });
const requireRole =
  auth.requireRole ||
  ((role) => (req, res, next) => {
    const user = req.user || req.identity;
    if (!user || user.role !== role) {
      return res.status(403).json({ detail: "Insufficient role" });
    }
    next();
  });

const app = express();

const allowedOrigin = FRONTEND_ORIGIN || frontendOrigin || "http://localhost:5173";

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (!origin || origin === allowedOrigin) {
    res.setHeader("Access-Control-Allow-Origin", allowedOrigin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  }
  if (req.method === "OPTIONS") {
    return res.sendStatus(origin && origin !== allowedOrigin ? 403 : 204);
  }
  next();
});

app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "grievance" });
});

app.post(
  "/grievances",
  requireAuth,
  requireRole("worker"),
  async (req, res, next) => {
    try {
      const { platform, category, description } = req.body;
      if (!platform || !category || !description) {
        return res.status(422).json({ detail: "platform, category, and description are required" });
      }

      const user = req.user || req.identity;
      const result = await pool.query(
        `INSERT INTO grievances (worker_id, platform, category, description, status, created_at)
         VALUES ($1, $2, $3, $4, 'submitted', NOW())
         RETURNING id, status, created_at`,
        [user.sub, platform, category, description]
      );

      return res.status(201).json(result.rows[0]);
    } catch (error) {
      next(error);
    }
  }
);

app.get(
  "/grievances",
  requireAuth,
  async (req, res, next) => {
    try {
      const user = req.user || req.identity;
      let queryText;
      let queryParams;

      if (user.role === "worker") {
        queryText = `
          SELECT id, platform, category, status, created_at
          FROM grievances
          WHERE worker_id = $1
          ORDER BY created_at DESC
          LIMIT 100
        `;
        queryParams = [user.sub];
      } else if (user.role === "verifier" || user.role === "advocate") {
        queryText = `
          SELECT id, platform, category, status, created_at
          FROM grievances
          ORDER BY created_at DESC
          LIMIT 100
        `;
        queryParams = [];
      } else {
        return res.status(403).json({ detail: "Insufficient role" });
      }

      const result = await pool.query(queryText, queryParams);
      return res.json(result.rows);
    } catch (error) {
      next(error);
    }
  }
);

app.get(
  "/grievances/:id",
  requireAuth,
  async (req, res, next) => {
    try {
      const user = req.user || req.identity;
      const result = await pool.query(
        "SELECT * FROM grievances WHERE id = $1",
        [req.params.id]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({ detail: "Grievance not found" });
      }

      const row = result.rows[0];

      if (user.role === "worker") {
        if (row.worker_id !== user.sub) {
          return res.status(403).json({ detail: "Forbidden" });
        }
      } else if (user.role !== "verifier" && user.role !== "advocate") {
        return res.status(403).json({ detail: "Insufficient role" });
      }

      return res.json(row);
    } catch (error) {
      if (error.code === "22P02") {
        return res.status(404).json({ detail: "Grievance not found" });
      }
      next(error);
    }
  }
);

app.patch(
  "/grievances/:id",
  requireAuth,
  async (req, res, next) => {
    try {
      const user = req.user || req.identity;
      const { status, description } = req.body;

      const existing = await pool.query(
        "SELECT * FROM grievances WHERE id = $1",
        [req.params.id]
      );

      if (existing.rows.length === 0) {
        return res.status(404).json({ detail: "Grievance not found" });
      }

      const row = existing.rows[0];

      if (description !== undefined) {
        if (user.role !== "worker" || row.worker_id !== user.sub) {
          return res.status(403).json({ detail: "Only the owning worker may update description" });
        }
        if (row.status !== "submitted") {
          return res.status(400).json({ detail: "Description can only be updated while status is submitted" });
        }
      }

      if (status !== undefined) {
        if (user.role !== "verifier" && user.role !== "advocate") {
          return res.status(403).json({ detail: "Only verifiers and advocates may change status" });
        }
        const allowedStatuses = ["submitted", "reviewing", "escalated", "resolved", "closed"];
        if (!allowedStatuses.includes(status)) {
          return res.status(422).json({ detail: "Invalid status value" });
        }
      }

      const updates = [];
      const values = [];
      let paramIndex = 1;

      if (description !== undefined) {
        updates.push(`description = $${paramIndex++}`);
        values.push(description);
      }

      if (status !== undefined) {
        updates.push(`status = $${paramIndex++}`);
        values.push(status);
      }

      if (updates.length === 0) {
        return res.json(row);
      }

      values.push(req.params.id);
      const updateResult = await pool.query(
        `UPDATE grievances
         SET ${updates.join(", ")}
         WHERE id = $${paramIndex}
         RETURNING *`,
        values
      );

      return res.json(updateResult.rows[0]);
    } catch (error) {
      if (error.code === "22P02") {
        return res.status(404).json({ detail: "Grievance not found" });
      }
      next(error);
    }
  }
);

app.patch(
  "/grievances/:id/workflow",
  requireRoles("advocate"),
  (req, res) => {
    const { status, cluster_id: clusterId = null, tags = [] } = req.body;
    const allowedStatuses = ["submitted", "reviewing", "escalated", "resolved", "closed"];
    if (!allowedStatuses.includes(status)) {
      return res.status(422).json({ detail: "A valid workflow status is required" });
    }
    return res.json({
      stub: true,
      grievance_id: req.params.id,
      status,
      cluster_id: clusterId,
      tags,
      updated_by: req.identity.sub,
    });
  },
);

app.use((error, _req, res, _next) => {
  console.error(error);
  res.status(503).json({ detail: "Service dependency unavailable" });
});

const server = app.listen(port, () => {
  console.log(`grievance-service listening on http://localhost:${port}`);
  require("./schema").getGrievanceColumns().then((cols) => console.log("grievances cols:", cols)).catch(console.error);
});

async function shutdown() {
  server.close();
  await pool.end();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

module.exports = app;
