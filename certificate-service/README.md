# Certificate Service

## Purpose
Express service boundary generating verified income summaries and downloadable income certificates for gig workers.

## Env vars
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/fairgig`)
- `JWT_SECRET`: Secret key for HS256 JWT verification
- `FRONTEND_ORIGIN`: Allowed CORS origin (default: `http://localhost:5173`)
- `PORT`: Service port (default: `8006`)

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
| GET | `/certificates/income/summary` | worker | Income aggregate summary JSON (max 12 months) |
| GET | `/certificates/income` | worker | Download verified income certificate PDF |
| POST | `/certificates/preview` | worker | Render HTML preview of certificate |
| GET | `/certificates/:workerId/summary` | worker (own) | Legacy summary stub |

## Auth requirements
Requires `Authorization: Bearer <token>` signed with `JWT_SECRET` (HS256) with role `worker`. Workers can only access their own data.

## Curl examples
```bash
# Health Check
curl http://localhost:8006/health

# Income Summary JSON
curl "http://localhost:8006/certificates/income/summary?from=2026-01-01&to=2026-06-30" \
  -H "Authorization: Bearer $TOKEN"

# Download Certificate PDF
curl "http://localhost:8006/certificates/income?from=2026-01-01&to=2026-06-30" \
  -H "Authorization: Bearer $TOKEN" \
  -o certificate.pdf

# Certificate Preview HTML
curl -X POST http://localhost:8006/certificates/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"period":"2026-01-01 to 2026-06-30","net_income":45000}'
```

## How to run tests
```bash
npm run check && bash test/smoke.sh
```
