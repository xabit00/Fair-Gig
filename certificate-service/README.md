# FairGig certificate service

Express service boundary for income certificates. Level 1 includes an authenticated print-friendly A4 HTML preview and a stable summary contract; verified database totals are reserved for Level 2.

## Run on Windows

```powershell
cd certificate-service
npm install
npm start
```

The service listens on `http://localhost:8006` and reads the root `.env` file.

## Check JavaScript syntax

```powershell
cd certificate-service
npm run check
```
