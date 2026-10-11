from contextlib import asynccontextmanager
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import Depends, FastAPI, status
from pydantic import BaseModel, Field
from psycopg import Connection

from .auth import require_roles
from .db import get_connection, pool


class ShiftDraft(BaseModel):
    platform: str = Field(min_length=2, max_length=80)
    date: date
    hours_worked: float = Field(gt=0, le=24)
    gross_earned: float = Field(ge=0)
    deductions: float = Field(ge=0)
    net_received: float = Field(ge=0)
    screenshot_url: str | None = None


class CsvImportRequest(BaseModel):
    csv_text: str = Field(min_length=1)
    platform: str = Field(min_length=2, max_length=80)


class VerificationUpdate(BaseModel):
    verification_status: Literal["confirmed", "discrepancy_flagged", "unverifiable"]
    note: str | None = Field(default=None, max_length=500)


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="FairGig Earnings Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health(connection: Connection = Depends(get_connection)) -> dict:
    connection.execute("SELECT 1")
    return {"service": "earnings-service", "status": "ok", "database": "connected"}


@app.post("/shifts", status_code=status.HTTP_201_CREATED)
def create_shift(payload: ShiftDraft, identity: dict = Depends(require_roles("worker"))) -> dict:
    return {
        "stub": True,
        "message": "Shift accepted by the Level 1 contract; persistence is scheduled for Level 2.",
        "shift": {
            "id": "00000000-0000-0000-0000-000000000000",
            "worker_id": identity["sub"],
            **payload.model_dump(mode="json"),
            "verification_status": "pending",
        },
    }


@app.post("/shifts/import-csv", status_code=status.HTTP_202_ACCEPTED)
def import_csv(payload: CsvImportRequest, identity: dict = Depends(require_roles("worker"))) -> dict:
    row_count = max(len([line for line in payload.csv_text.splitlines() if line.strip()]) - 1, 0)
    return {
        "stub": True,
        "worker_id": identity["sub"],
        "platform": payload.platform,
        "rows_detected": row_count,
        "message": "CSV validation and persistence are scheduled for Level 2.",
    }


@app.patch("/shifts/{shift_id}/verification")
def update_verification(
    shift_id: UUID,
    payload: VerificationUpdate,
    identity: dict = Depends(require_roles("verifier")),
) -> dict:
    return {
        "stub": True,
        "shift_id": shift_id,
        "verification_status": payload.verification_status,
        "note": payload.note,
        "verified_by": identity["sub"],
    }

