# Analytics Service

## Purpose
FastAPI service boundary providing K-anonymous aggregate earnings metrics, platform breakdowns, and vulnerability analytics.

## Env vars
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/fairgig`)
- `JWT_SECRET`: Secret key for HS256 JWT verification
- `FRONTEND_ORIGIN`: Allowed CORS origin (default: `http://localhost:5173`)
- `K_ANONYMITY_MIN_GROUP`: Minimum group size threshold for K-anonymity (default: `5`)

## Install
```bash
pip install -r requirements.txt
```

## Start command
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8005
```

## Endpoints table
| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | `/health` | Public | Service health check |
| GET | `/analytics/overview` | advocate | Aggregate overview metrics for date range |
| GET | `/analytics/earnings-trends` | advocate | Monthly aggregated earnings trend (min 5 workers) |
| GET | `/analytics/platforms` | advocate | Platform-level worker net earnings (min 5 workers) |
| GET | `/analytics/zones` | advocate | City zone worker net earnings (min 5 workers) |
| GET | `/analytics/grievances` | advocate | Grievances aggregated by category (min 5 workers) |
| GET | `/analytics/vulnerability` | advocate | Declining worker counts by platform and zone |

## Auth requirements
Requires `Authorization: Bearer <token>` signed with `JWT_SECRET` (HS256) with role `advocate`.

## Curl examples
```bash
# Health Check
curl http://localhost:8005/health

# Analytics Overview
curl "http://localhost:8005/analytics/overview?from=2026-01-01&to=2026-01-31" \
  -H "Authorization: Bearer $TOKEN"

# Earnings Trends
curl "http://localhost:8005/analytics/earnings-trends?group=month" \
  -H "Authorization: Bearer $TOKEN"

# Platform Breakdown
curl http://localhost:8005/analytics/platforms -H "Authorization: Bearer $TOKEN"

# Vulnerability Analysis
curl "http://localhost:8005/analytics/vulnerability?months=2" -H "Authorization: Bearer $TOKEN"
```

## How to run tests
```bash
python -m py_compile app/main.py && bash test/smoke.sh
```
