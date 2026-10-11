# Grievance Service

## Purpose
Express service boundary managing worker complaint logging, status workflow tracking, and advocate resolution.

## Env vars
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/fairgig`)
- `JWT_SECRET`: Secret key for HS256 JWT verification
- `FRONTEND_ORIGIN`: Allowed CORS origin (default: `http://localhost:5173`)
- `PORT`: Service port (default: `8004`)

## Install
```bash
npm install
```

## Start command
```bash
npm start
```

## Endpoints table
| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | `/health` | Public | Service health check |
| POST | `/grievances` | worker | Create a new grievance |
| GET | `/grievances` | worker, verifier, advocate | List grievances (worker scoped to own) |
| GET | `/grievances/:id` | worker (own), verifier, advocate | Retrieve single grievance details |
| PATCH | `/grievances/:id` | worker (own), verifier, advocate | Update description (worker) or status (verifier/advocate) |

## Auth requirements
Requires `Authorization: Bearer <token>` signed with `JWT_SECRET` (HS256) containing `sub` (worker ID) and `role` (`worker`, `verifier`, or `advocate`).

## Curl examples
```bash
# Health Check
curl http://localhost:8004/health

# Submit Grievance (Worker)
curl -X POST http://localhost:8004/grievances \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"platform":"Foodpanda","category":"commission","description":"Unfair deduction"}'

# List Grievances
curl http://localhost:8004/grievances -H "Authorization: Bearer $TOKEN"

# Get Grievance by ID
curl http://localhost:8004/grievances/11111111-1111-1111-1111-111111111111 -H "Authorization: Bearer $TOKEN"

# Update Grievance Status (Advocate/Verifier)
curl -X PATCH http://localhost:8004/grievances/11111111-1111-1111-1111-111111111111 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"reviewing"}'
```

## How to run tests
```bash
npm run check && bash test/smoke.sh
```
