const path = require("node:path");
const dotenv = require("dotenv");

dotenv.config({ path: path.resolve(__dirname, "../../.env") });

module.exports = {
  port: Number(process.env.CERTIFICATE_SERVICE_PORT || 8006),
  databaseUrl:
    process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/fairgig",
  jwtSecret: process.env.JWT_SECRET || "change-this-development-secret-now",
};

