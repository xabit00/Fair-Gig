const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const PORT = Number(process.env.PORT || process.env.CERTIFICATE_SERVICE_PORT || 8006);
const DATABASE_URL =
  process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/fairgig";
const JWT_SECRET = process.env.JWT_SECRET || "change-this-development-secret-now";
const FRONTEND_ORIGIN =
  process.env.FRONTEND_ORIGIN || process.env.CORS_ORIGINS || "http://localhost:5173";

module.exports = {
  port: PORT,
  PORT,
  databaseUrl: DATABASE_URL,
  DATABASE_URL,
  jwtSecret: JWT_SECRET,
  JWT_SECRET,
  frontendOrigin: FRONTEND_ORIGIN,
  FRONTEND_ORIGIN,
};
