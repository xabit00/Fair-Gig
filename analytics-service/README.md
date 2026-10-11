# FairGig analytics service

FastAPI advocate analytics boundary. Its Level 1 endpoints already query the seeded PostgreSQL data for overall, platform, and city-zone aggregates. Every grouped result uses `HAVING COUNT(DISTINCT worker_id) >= 5`; smaller groups are never returned.

## Run on Windows

```powershell
cd analytics-service
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8005
```

Open `http://localhost:8005/docs` for Swagger UI. The three analytics routes require an advocate access token.
