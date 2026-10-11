from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .auth import require_roles
from .config import settings
from .db import pool
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
        return {"service": "anomaly-service", "status": "ok", "database": "connected"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"service": "anomaly-service", "status": "unhealthy", "database": "unavailable"}


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
