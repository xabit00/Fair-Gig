# FairGig grievance service

Express service boundary for complaint creation, tags, clustering, and advocate escalation workflow. Level 1 routes validate shared JWTs and return stable stub response shapes.

## Run on Windows

```powershell
cd grievance-service
npm install
npm start
```

The service listens on `http://localhost:8004` and reads the root `.env` file.

## Check JavaScript syntax

```powershell
cd grievance-service
npm run check
```
