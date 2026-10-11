from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from psycopg import Connection

from .auth import require_roles
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
    earnings: list[EarningRecord] = Field(min_length=1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(
    title="FairGig Anomaly Service",
    version="1.0.0",
    description="Flags unusual deductions and month-on-month net income drops.",
    lifespan=lifespan,
)


@app.get("/health")
def health(connection: Connection = Depends(get_connection)) -> dict:
    connection.execute("SELECT 1")
    return {"service": "anomaly-service", "status": "ok", "database": "connected"}


@app.get("/rules")
def rules(_: dict = Depends(require_roles("worker", "verifier", "advocate"))) -> dict:
    return {
        "rules": [
            {"id": "high_deduction", "condition": "deduction > mean + 2 population standard deviations"},
            {"id": "monthly_income_drop", "condition": "month-on-month net income drop > 20%"},
        ]
    }


@app.post("/detect")
def detect(
    payload: DetectionRequest,
    _: dict = Depends(require_roles("worker", "verifier", "advocate")),
) -> dict:
    records = [record.model_dump() for record in payload.earnings]
    anomalies = detect_anomalies(records)
    return {
        "worker_id": payload.worker_id,
        "records_analysed": len(records),
        "anomalies": anomalies,
        "summary": f"Found {len(anomalies)} item(s) that may need review.",
    }

