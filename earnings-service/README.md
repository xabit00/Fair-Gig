# FairGig earnings service

Level 1 FastAPI boundary for shift entry, CSV import, screenshot references, and verifier decisions. The endpoints currently return contract-shaped stub responses and verify shared JWTs.

## Run on Windows

```powershell
cd earnings-service
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8002
```

Open `http://localhost:8002/docs` for Swagger UI. A running PostgreSQL database is required by `/health`.
