# FairGig

FairGig is a service-oriented foundation for gig-worker income records, verification, certificates, grievances, anomaly detection, and k-anonymous advocate analytics.

## Repository structure

```text
fairgig/
|-- auth-service/          FastAPI, port 8001
|-- earnings-service/      FastAPI, port 8002
|-- anomaly-service/       FastAPI, port 8003
|-- grievance-service/     Express, port 8004
|-- analytics-service/     FastAPI, port 8005
|-- certificate-service/   Express, port 8006
|-- frontend/              Vite and React, port 5173
|-- db/                    PostgreSQL schema and seed
|-- docs/                  API contracts
|-- scripts/               Cross-platform start-all launcher
|-- .env.example
`-- package.json
```

## Prerequisites on Windows

- Python 3.11 or newer, available as `py`
- Node.js 20.19 or newer with npm
- Access to the existing FairGig Neon PostgreSQL project

## First-time setup in PowerShell

Run these commands from the repository root:

```powershell
Copy-Item .env.example .env
# Edit .env and provide the pooled Neon DATABASE_URL and shared JWT_SECRET.

py -m venv auth-service/.venv
auth-service/.venv/Scripts/python -m pip install -r auth-service/requirements.txt
py -m venv earnings-service/.venv
earnings-service/.venv/Scripts/python -m pip install -r earnings-service/requirements.txt
py -m venv anomaly-service/.venv
anomaly-service/.venv/Scripts/python -m pip install -r anomaly-service/requirements.txt
py -m venv analytics-service/.venv
analytics-service/.venv/Scripts/python -m pip install -r analytics-service/requirements.txt

npm install --prefix grievance-service
npm install --prefix certificate-service
npm install --prefix frontend
```

Use the pooled Neon connection string for normal application traffic. Do not run `db/seed.py` against the shared database during ordinary setup: it truncates and recreates FairGig data.

## Start each service with one command

Open a PowerShell tab for each command and run it from the repository root:

```powershell
auth-service/.venv/Scripts/python -m uvicorn app.main:app --app-dir auth-service --reload --port 8001
earnings-service/.venv/Scripts/python -m uvicorn app.main:app --app-dir earnings-service --reload --port 8002
anomaly-service/.venv/Scripts/python -m uvicorn app.main:app --app-dir anomaly-service --reload --port 8003
npm start --prefix grievance-service
analytics-service/.venv/Scripts/python -m uvicorn app.main:app --app-dir analytics-service --reload --port 8005
npm start --prefix certificate-service
npm run dev --prefix frontend
```

To launch all seven processes after setup:

```powershell
npm run start-all
```

Press `Ctrl+C` once to stop the launcher and its child processes.

## Useful URLs

- Frontend: `http://localhost:5173`
- Auth docs: `http://localhost:8001/docs`
- Earnings docs: `http://localhost:8002/docs`
- Anomaly docs: `http://localhost:8003/docs`
- Analytics docs: `http://localhost:8005/docs`

All seeded accounts use `FairGig123!`. Staff logins are `verifier@fairgig.test` and `advocate@fairgig.test`. Worker emails follow the form `ahsan.raza@example.com`.

## Security and privacy baseline

- Public registration can only create workers.
- Only advocates can change account roles.
- Passwords use bcrypt.
- Access tokens expire after 15 minutes by default.
- Refresh tokens are hashed in PostgreSQL and rotate on use.
- Every service validates the same issuer, audience, algorithm, and `JWT_SECRET`.
- Analytics groups smaller than five distinct workers are suppressed in SQL.
- `.env`, local environments, dependencies, and build output are ignored by Git.

## Level 2 ownership for three teammates

### Frontend

- Connect the worker dashboard, earnings form, CSV import, grievance form, verifier queue, analytics charts, and certificate preview to their services.
- Add field-level validation, optimistic states where safe, accessible tables, and API error handling.
- Keep role navigation and route protection aligned with `docs/API_CONTRACTS.md`.

### Backend services

- Implement earnings CRUD, screenshot storage, CSV parsing, and verifier audit notes.
- Persist grievance tags, clusters, status history, and escalation actions.
- Generate certificates from confirmed shifts with a stable certificate ID and verification URL.
- Add service-level tests for authorization, invalid input, ownership, and persistence.

### Integration and lead

- Add database migrations, request IDs, structured logs, and a repeatable demo reset.
- Wire anomaly detection to stored earnings and schedule advocate summaries.
- Run end-to-end role flows, confirm CORS and environment handling, and guard every aggregate with the five-worker rule.
- Prepare the competition demo script, fallback screenshots, and deployment configuration.

Level 1 intentionally stops at these boundaries. Do not add Level 2 persistence to the stub services until endpoint ownership is assigned.
