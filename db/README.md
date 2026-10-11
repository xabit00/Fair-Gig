# FairGig database

The shared PostgreSQL schema is the contract between all FairGig services.

## Windows setup

From the repository root in PowerShell:

```powershell
createdb -U postgres fairgig
psql -U postgres -d fairgig -f db/schema.sql
py -m venv db/.venv
db/.venv/Scripts/python -m pip install -r db/requirements.txt
Copy-Item .env.example .env
db/.venv/Scripts/python db/seed.py
```

Set `DATABASE_URL` in `.env` if your PostgreSQL username, password, host, port, or database name differs.

The seed resets FairGig tables, then creates 40 workers, two staff accounts, 90 days of shifts, commission changes, income drops, and grievances. All seeded accounts use `FairGig123!`.
