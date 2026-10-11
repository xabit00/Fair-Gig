const { Pool } = require("pg");
const { databaseUrl } = require("./config");

module.exports = new Pool({ connectionString: databaseUrl, max: 5 });

