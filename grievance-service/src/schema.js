const pool = require("./db");

async function getGrievanceColumns() {
  const result = await pool.query(
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'grievances' ORDER BY ordinal_position"
  );
  const cols = result.rows.map((row) => row.column_name);
  return cols;
}

module.exports = { getGrievanceColumns };
