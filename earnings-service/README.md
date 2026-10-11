# FairGig Earnings Service

FastAPI service for worker shift management, earnings tracking, and anomaly detection.

## Run on Windows

```powershell
cd earnings-service
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8002
```

Open `http://localhost:8002/docs` for Swagger UI. A running PostgreSQL database is required by `/health`.

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fairgig
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
```

## API Endpoints

All endpoints (except `/health`) require a valid JWT Bearer token.

### Health Check
```bash
curl -X GET http://localhost:8002/health
```
Response:
```json
{
  "status": "healthy",
  "service": "earnings-service",
  "database": "connected"
}
```

### Create Shift
```bash
curl -X POST http://localhost:8002/shifts \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Foodpanda",
    "work_date": "2026-10-11",
    "start_time": "09:00:00",
    "end_time": "17:30:00",
    "hours_worked": 8.5,
    "gross_earned": 5000.0,
    "deductions": 200.0,
    "commission": 500.0,
    "net_received": 4300.0,
    "status": "pending"
  }'
```

### List Shifts (with filters)
```bash
# All shifts
curl -X GET http://localhost:8002/shifts \
  -H "Authorization: Bearer <TOKEN>"

# Filter by platform
curl -X GET "http://localhost:8002/shifts?platform=Uber" \
  -H "Authorization: Bearer <TOKEN>"

# Filter by date range
curl -X GET "http://localhost:8002/shifts?start_date=2026-10-01&end_date=2026-10-31" \
  -H "Authorization: Bearer <TOKEN>"
```

### Get Single Shift
```bash
curl -X GET http://localhost:8002/shifts/<SHIFT_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

### Update Shift
```bash
curl -X PUT http://localhost:8002/shifts/<SHIFT_ID> \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"platform": "Updated Platform", "status": "confirmed"}'
```

### Delete Shift
```bash
curl -X DELETE http://localhost:8002/shifts/<SHIFT_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

### Earnings Summary
```bash
curl -X GET http://localhost:8002/earnings/summary \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
{
  "total_hours": 160.5,
  "total_gross": 100000.0,
  "total_deductions": 4000.0,
  "total_commission": 10000.0,
  "total_net": 86000.0,
  "total_shifts": 20,
  "effective_hourly_rate": 535.83
}
```

## Validation Rules

| Field | Constraint |
|-------|------------|
| `hours_worked` | > 0 (must be positive) |
| `gross_earned` | >= 0 |
| `deductions` | >= 0 |
| `commission` | >= 0 |
| `net_received` | >= 0 |
| Business rule | `net_received` <= `gross_earned` |

Invalid requests return `422 Unprocessable Entity` (Pydantic validation) or `400 Bad Request` (business logic).

## Run Tests

```powershell
cd earnings-service
.venv/Scripts/python -m pytest tests/ -v
```