const { Pool } = require("pg");
const { databaseUrl } = require("./config");

const pool = new Pool({ connectionString: databaseUrl, max: 5 });

module.exports = pool;

