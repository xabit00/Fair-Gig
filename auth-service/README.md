# FairGig auth service

FastAPI service for worker registration, login, refresh-token rotation, current-user lookup, and advocate-managed roles. It signs the JWT used by every FairGig service.

## Run on Windows

```powershell
cd auth-service
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8001
```

Open `http://localhost:8001/docs` for Swagger UI. The service reads `DATABASE_URL`, `JWT_SECRET`, token lifetimes, and `CORS_ORIGINS` from the root `.env` file.

## Test

```powershell
cd auth-service
.venv/Scripts/python -m pytest
```
