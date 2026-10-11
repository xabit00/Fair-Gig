
from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from psycopg import Connection

from .auth import require_roles, verify_token
from .config import settings
from .db import get_connection, pool
from .detector import detect_anomalies


class EarningRecord(BaseModel):
    date: date
    platform: str = Field(min_length=2, max_length=80)
    gross_earned: float = Field(ge=0)
    deductions: float = Field(ge=0)
    net_received: float = Field(ge=0)


class DetectionRequest(BaseModel):
    worker_id: UUID
    earnings: list[EarningRecord] = Field(default_factory=list)


class DetectionResponse(BaseModel):
    worker_id: str
    analysis_period: dict
    records_analysed: int
    anomalies: list[dict]
    summary: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="FairGig Anomaly Service",
    version="1.0.0",
    description="Flags unusual deductions and month-on-month net income drops.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(response: Response) -> dict:
    try:
        with pool.connection() as connection:
            connection.execute("SELECT 1")
        return {
            "service": "anomaly-service",
            "status": "ok",
            "database": "connected",
        }
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "service": "anomaly-service",
            "status": "unhealthy",
            "database": "unavailable",
        }


@app.get("/rules")
def rules(
    _: dict = Depends(require_roles("worker", "verifier", "advocate"))
) -> dict:
    return {
        "rules": [
            {
                "id": "high_deduction",
                "condition": "deduction > mean + 2 population standard deviations",
            },
            {
                "id": "monthly_income_drop",
                "condition": "month-on-month net income drop > 20%",
            },
        ]
    }


def _fetch_worker_earnings(
    worker_id: str,
    conn: Connection,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    with conn.cursor() as cur:
        query = """
            SELECT work_date AS date,
                   platform,
                   gross_earned,
                   deductions,
                   net_received
            FROM shifts
            WHERE worker_id = %s
        """
        params = [worker_id]

        if start_date:
            query += " AND work_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND work_date <= %s"
            params.append(end_date)

        query += " ORDER BY work_date"
        cur.execute(query, params)
        rows = cur.fetchall()

    return [
        {
            "date": row["date"],
            "platform": row["platform"],
            "gross_earned": float(row["gross_earned"]),
            "deductions": float(row["deductions"]),
            "net_received": float(row["net_received"]),
        }
        for row in rows
    ]


def _build_detection_response(
    worker_id: str,
    records: list[dict],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    if not records:
        return {
            "worker_id": worker_id,
            "analysis_period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "records_analysed": 0,
            "anomalies": [],
            "summary": "No earnings records found for the specified period.",
        }

    anomalies = detect_anomalies(records)
    dates = [record["date"] for record in records]

    return {
        "worker_id": worker_id,
        "analysis_period": {
            "start_date": min(dates).isoformat(),
            "end_date": max(dates).isoformat(),
        },
        "records_analysed": len(records),
        "anomalies": anomalies,
        "summary": (
            f"Found {len(anomalies)} anomaly(ies) "
            f"in {len(records)} records."
        ),
    }


@app.get("/detect/me", response_model=DetectionResponse)
def detect_my_anomalies(
    token_data: dict = Depends(verify_token),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> dict:
    if token_data.get("role") != "worker":
        raise HTTPException(status_code=403, detail="Worker access required")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Invalid date range")

    worker_id = str(token_data["sub"])

    with get_connection() as conn:
        records = _fetch_worker_earnings(
            worker_id, conn, start_date, end_date
        )

    return _build_detection_response(
        worker_id, records, start_date, end_date
    )


@app.post("/detect", response_model=DetectionResponse)
def detect_worker_anomalies(
    payload: DetectionRequest,
    token_data: dict = Depends(require_roles("verifier", "advocate")),
) -> dict:
    worker_id = str(payload.worker_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE id = %s",
                (worker_id,),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Worker not found",
                )

        records = _fetch_worker_earnings(worker_id, conn)

    return _build_detection_response(worker_id, records)

