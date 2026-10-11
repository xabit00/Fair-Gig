const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

module.exports = {
  port: Number(process.env.GRIEVANCE_SERVICE_PORT || 8004),
  databaseUrl:
    process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/fairgig",
  jwtSecret: process.env.JWT_SECRET || "change-this-development-secret-now",
};

