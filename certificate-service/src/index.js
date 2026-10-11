const express = require("express");
const authenticate = require("./auth");
const { port, FRONTEND_ORIGIN, frontendOrigin } = require("./config");
const pool = require("./db");
const renderCertificate = require("./template");

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

app.use(express.json({ limit: "256kb" }));

const requireAuth = (req, res, next) => {
  authenticate(req, res, (err) => {
    if (err) return next(err);
    if (!req.user && req.identity) {
      req.user = req.identity;
    }
    next();
  });
};

const requireRole = (role) => (req, res, next) => {
  const user = req.user || req.identity;
  if (!user || user.role !== role) {
    return res.status(403).json({ detail: "Insufficient role" });
  }
  next();
};

function validateDateRange(from, to) {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!from || !to || !dateRegex.test(from) || !dateRegex.test(to)) {
    return { valid: false, error: "from and to dates are required in YYYY-MM-DD format" };
  }

  const fromDate = new Date(`${from}T00:00:00Z`);
  const toDate = new Date(`${to}T00:00:00Z`);

  if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
    return { valid: false, error: "Invalid date values" };
  }

  if (from > to) {
    return { valid: false, error: "from date must be less than or equal to to date" };
  }

  const maxToDate = new Date(fromDate);
  maxToDate.setUTCFullYear(maxToDate.getUTCFullYear() + 1);
  if (toDate > maxToDate) {
    return { valid: false, error: "Date range cannot exceed 12 months" };
  }

  return { valid: true, fromDate, toDate };
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "certificate" });
});

async function buildIncomeSummary(dbPool, workerId, from, to) {
  const result = await dbPool.query(
    `SELECT 
       COALESCE(SUM(gross_earned), 0) AS total_gross,
       COALESCE(SUM(deductions), 0) AS total_deductions,
       COALESCE(SUM(net_received), 0) AS total_net,
       COALESCE(SUM(hours_worked), 0) AS total_hours,
       COALESCE(SUM(CASE WHEN verification_status = 'confirmed' OR verification_status = 'verified' THEN net_received ELSE 0 END), 0) AS verified_net,
       COALESCE(SUM(CASE WHEN verification_status IS NULL OR (verification_status != 'confirmed' AND verification_status != 'verified') THEN net_received ELSE 0 END), 0) AS worker_reported_net
     FROM shifts
     WHERE worker_id = $1 AND date >= $2 AND date <= $3`,
    [workerId, from, to]
  );

  const row = result.rows[0] || {};

  return {
    worker_id: workerId,
    period: { from, to },
    total_gross: Number(row.total_gross || 0),
    total_deductions: Number(row.total_deductions || 0),
    total_net: Number(row.total_net || 0),
    total_hours: Number(row.total_hours || 0),
    verified_net: Number(row.verified_net || 0),
    worker_reported_net: Number(row.worker_reported_net || 0),
  };
}

async function getWorkerName(dbPool, workerId) {
  try {
    const res = await dbPool.query("SELECT name FROM workers WHERE id = $1", [workerId]);
    if (res.rows.length > 0 && res.rows[0].name) return res.rows[0].name;
  } catch (_e) {
    // workers table might not exist, fall back to users table
  }
  try {
    const res = await dbPool.query("SELECT name FROM users WHERE id = $1", [workerId]);
    if (res.rows.length > 0 && res.rows[0].name) return res.rows[0].name;
  } catch (_e) {}
  return "FairGig Worker";
}

app.get(
  "/certificates/income/summary",
  requireAuth,
  requireRole("worker"),
  async (req, res, next) => {
    try {
      const { from, to } = req.query;
      const validation = validateDateRange(from, to);
      if (!validation.valid) {
        return res.status(400).json({ detail: validation.error });
      }

      const workerId = (req.user && req.user.sub) || (req.identity && req.identity.sub);
      const summary = await buildIncomeSummary(pool, workerId, from, to);
      return res.json(summary);
    } catch (error) {
      next(error);
    }
  }
);

app.get(
  "/certificates/income",
  requireAuth,
  requireRole("worker"),
  async (req, res, next) => {
    try {
      const { from, to } = req.query;
      const validation = validateDateRange(from, to);
      if (!validation.valid) {
        return res.status(400).json({ detail: validation.error });
      }

      const workerId = (req.user && req.user.sub) || (req.identity && req.identity.sub);
      const summary = await buildIncomeSummary(pool, workerId, from, to);
      const workerName = await getWorkerName(pool, workerId);

      const verifiedStatus =
        summary.verified_net > 0 && summary.worker_reported_net === 0
          ? "Verified"
          : summary.verified_net > 0
          ? "Partially Verified"
          : "Worker Reported";

      const payload = {
        name: workerName,
        worker_id: workerId,
        period: `${from} to ${to}`,
        gross: summary.total_gross,
        deductions: summary.total_deductions,
        net: summary.total_net,
        hours: summary.total_hours,
        verified_status: verifiedStatus,
        generated_at: new Date().toISOString(),
      };

      const pdfContent = renderCertificate(payload);

      res.setHeader("Content-Type", "application/pdf");
      res.setHeader(
        "Content-Disposition",
        `attachment; filename="FairGig-Income-${from}_${to}.pdf"`
      );
      return res.send(Buffer.from(pdfContent));
    } catch (error) {
      next(error);
    }
  }
);

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

module.exports = app;
