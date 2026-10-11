const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const PORT = Number(process.env.PORT || process.env.GRIEVANCE_SERVICE_PORT || 8004);
const DATABASE_URL =
  process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/fairgig";
const JWT_SECRET = process.env.JWT_SECRET || "change-this-development-secret-now";
const FRONTEND_ORIGIN =
  process.env.FRONTEND_ORIGIN || process.env.CORS_ORIGINS || "http://localhost:5173";

module.exports = {
  PORT,
  port: PORT,
  DATABASE_URL,
  databaseUrl: DATABASE_URL,
  JWT_SECRET,
  jwtSecret: JWT_SECRET,
  FRONTEND_ORIGIN,
  frontendOrigin: FRONTEND_ORIGIN,
};
