# FairGig earnings service

FastAPI service for authenticated worker shift CRUD and earnings summaries. It uses the shared PostgreSQL `shifts` table and verifies access tokens issued by auth-service.

## Run on Windows PowerShell

Set the same Neon URL and JWT secret used by auth-service, then start the service:

```powershell
cd earnings-service
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "<pooled Neon PostgreSQL URL>"
$env:JWT_SECRET = "<same JWT_SECRET as auth-service>"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8002
```

The service also loads an optional `.env` from `earnings-service/` or the repository root. Do not commit secrets.

Open `http://localhost:8002/docs` for Swagger UI.

## Endpoints

- `GET /health` is public and verifies PostgreSQL connectivity.
- `POST /shifts` creates a worker-owned shift.
- `GET /shifts` lists the signed-in worker's shifts, with optional platform and date filters.
- `GET /shifts/{shift_id}` returns one owned shift.
- `PATCH|PUT /shifts/{shift_id}` updates one owned shift.
- `DELETE /shifts/{shift_id}` deletes one owned shift.
- `GET /earnings/summary` returns totals and the effective hourly rate.
- `POST /shifts/import-csv` is an explicit Level 1 validation stub and does not persist rows yet.

The shift payload uses `date`, `hours_worked`, `gross_earned`, `deductions`, `net_received`, and optional `screenshot_url`. Net income cannot exceed gross income.

## Test

```powershell
cd earnings-service
.\.venv\Scripts\python.exe -m pytest tests -q
```
