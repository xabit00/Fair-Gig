const express = require("express");
const pool = require("./db");
const { port } = require("./config");
const { requireRoles } = require("./auth");

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", async (_req, res, next) => {
  try {
    await pool.query("SELECT 1");
    res.json({ service: "grievance-service", status: "ok", database: "connected" });
  } catch (error) {
    next(error);
  }
});

app.get(
  "/grievances",
  requireRoles("worker", "advocate"),
  (req, res) => {
    res.json({
      stub: true,
      viewer: req.identity.sub,
      grievances: [
        {
          id: "00000000-0000-0000-0000-000000000000",
          platform: "Foodpanda",
          category: "commission",
          description: "The weekly statement shows a higher platform fee.",
          status: "reviewing",
          cluster_id: null,
          tags: ["unexpected-deduction"],
        },
      ],
    });
  },
);

app.post(
  "/grievances",
  requireRoles("worker"),
  (req, res) => {
    const { platform, category, description } = req.body;
    if (!platform || !category || !description) {
      return res.status(422).json({ detail: "platform, category, and description are required" });
    }
    return res.status(201).json({
      stub: true,
      grievance: {
        id: "00000000-0000-0000-0000-000000000000",
        worker_id: req.identity.sub,
        platform,
        category,
        description,
        status: "submitted",
        cluster_id: null,
        tags: [],
      },
    });
  },
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
});

async function shutdown() {
  server.close();
  await pool.end();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

