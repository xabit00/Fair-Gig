# FairGig anomaly service

FastAPI service that flags deductions above the worker-history mean plus two population standard deviations and month-on-month net-income drops greater than 20%.

## Run on Windows PowerShell

```powershell
cd anomaly-service
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "<pooled Neon PostgreSQL URL>"
$env:JWT_SECRET = "<same JWT_SECRET as auth-service>"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8003
```

The service also loads an optional `.env` from `anomaly-service/` or the repository root. Do not commit secrets.

Open `http://localhost:8003/docs` for Swagger UI. `GET /health` is public; `GET /rules` and `POST /detect` require an auth-service access token.

## Test

```powershell
cd anomaly-service
.\.venv\Scripts\python.exe -m pytest tests -q
```
