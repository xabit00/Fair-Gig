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

app.get("/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", service: "grievance-service", database: "connected" });
  } catch (_error) {
    res.status(503).json({ status: "unhealthy", service: "grievance-service", database: "unavailable" });
  }
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
          SELECT g.id, g.platform, g.category, g.description, g.status, g.cluster_id, g.created_at,
                 COALESCE((SELECT json_agg(gt.tag ORDER BY gt.tag)
                           FROM grievance_tags gt WHERE gt.grievance_id = g.id), '[]'::json) AS tags
          FROM grievances g
          WHERE g.worker_id = $1
          ORDER BY g.created_at DESC
          LIMIT 100
        `;
        queryParams = [user.sub];
      } else if (user.role === "verifier" || user.role === "advocate") {
        queryText = `
          SELECT g.id, g.platform, g.category, g.description, g.status, g.cluster_id, g.created_at,
                 COALESCE((SELECT json_agg(gt.tag ORDER BY gt.tag)
                           FROM grievance_tags gt WHERE gt.grievance_id = g.id), '[]'::json) AS tags
          FROM grievances g
          ORDER BY g.created_at DESC
          LIMIT 100
        `;
        queryParams = [];
      } else {
        return res.status(403).json({ detail: "Insufficient role" });
      }

      const result = await pool.query(queryText, queryParams);
      return res.json({ grievances: result.rows });
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
  async (req, res, next) => {
    const { status, cluster_id: clusterId = null, tags = [] } = req.body;
    const allowedStatuses = ["submitted", "reviewing", "escalated", "resolved", "closed"];
    if (!allowedStatuses.includes(status)) {
      return res.status(422).json({ detail: "A valid workflow status is required" });
    }
    if (!Array.isArray(tags) || tags.some((tag) => typeof tag !== "string" || !tag.trim() || tag.length > 60)) {
      return res.status(422).json({ detail: "Tags must be non-empty strings up to 60 characters" });
    }

    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const existing = await client.query("SELECT * FROM grievances WHERE id = $1 FOR UPDATE", [req.params.id]);
      if (existing.rows.length === 0) {
        await client.query("ROLLBACK");
        return res.status(404).json({ detail: "Grievance not found" });
      }

      let resolvedClusterId = null;
      if (clusterId) {
        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (uuidPattern.test(clusterId)) {
          const cluster = await client.query("SELECT id FROM grievance_clusters WHERE id = $1", [clusterId]);
          if (cluster.rows.length === 0) {
            await client.query("ROLLBACK");
            return res.status(422).json({ detail: "Cluster does not exist" });
          }
          resolvedClusterId = clusterId;
        } else {
          const row = existing.rows[0];
          const cluster = await client.query(
            `SELECT id FROM grievance_clusters
             WHERE title = $1 AND platform = $2 AND category = $3
             ORDER BY created_at LIMIT 1`,
            [clusterId, row.platform, row.category]
          );
          if (cluster.rows.length) {
            resolvedClusterId = cluster.rows[0].id;
          } else {
            const created = await client.query(
              `INSERT INTO grievance_clusters (title, platform, category)
               VALUES ($1, $2, $3) RETURNING id`,
              [clusterId, row.platform, row.category]
            );
            resolvedClusterId = created.rows[0].id;
          }
        }
      }

      const updated = await client.query(
        `UPDATE grievances SET status = $1, cluster_id = $2
         WHERE id = $3 RETURNING *`,
        [status, resolvedClusterId, req.params.id]
      );
      await client.query("DELETE FROM grievance_tags WHERE grievance_id = $1", [req.params.id]);
      for (const tag of [...new Set(tags.map((value) => value.trim()))]) {
        await client.query(
          "INSERT INTO grievance_tags (grievance_id, tag) VALUES ($1, $2)",
          [req.params.id, tag]
        );
      }
      await client.query("COMMIT");
      return res.json({ ...updated.rows[0], tags: [...new Set(tags.map((value) => value.trim()))] });
    } catch (error) {
      await client.query("ROLLBACK");
      return next(error);
    } finally {
      client.release();
    }
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
