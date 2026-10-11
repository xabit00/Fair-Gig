const express = require("express");
const authenticate = require("./auth");
const { port } = require("./config");
const pool = require("./db");
const renderCertificate = require("./template");

const app = express();
app.use(express.json({ limit: "256kb" }));

app.get("/health", async (_req, res, next) => {
  try {
    await pool.query("SELECT 1");
    res.json({ service: "certificate-service", status: "ok", database: "connected" });
  } catch (error) {
    next(error);
  }
});

app.post("/certificates/preview", authenticate, (req, res) => {
  const workerId = req.body.worker_id || req.identity.sub;
  if (req.identity.role === "worker" && workerId !== req.identity.sub) {
    return res.status(403).json({ detail: "Workers can only preview their own certificate" });
  }
  return res.type("html").send(renderCertificate({ ...req.body, worker_id: workerId }));
});

app.get("/certificates/:workerId/summary", authenticate, (req, res) => {
  if (req.identity.role === "worker" && req.params.workerId !== req.identity.sub) {
    return res.status(403).json({ detail: "Workers can only view their own certificate" });
  }
  return res.json({
    stub: true,
    worker_id: req.params.workerId,
    status: "preview_available",
    message: "Verified database totals and certificate references are scheduled for Level 2.",
  });
});

app.use((error, _req, res, _next) => {
  console.error(error);
  res.status(503).json({ detail: "Service dependency unavailable" });
});

const server = app.listen(port, () => {
  console.log(`certificate-service listening on http://localhost:${port}`);
});

async function shutdown() {
  server.close();
  await pool.end();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

