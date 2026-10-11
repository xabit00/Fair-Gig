# FairGig anomaly service

FastAPI service with a working first-pass anomaly detector. It flags deduction amounts above the worker history mean plus two population standard deviations and month-on-month net-income drops greater than 20%.

## Run on Windows

```powershell
cd anomaly-service
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8003
```

Open `http://localhost:8003/docs` to test `/detect` with an access token.

## Test

```powershell
cd anomaly-service
.venv/Scripts/python -m pytest
```
