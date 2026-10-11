from contextlib import asynccontextmanager
import csv
from datetime import date
import io
from typing import Literal, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from psycopg.errors import UniqueViolation

from .auth import require_roles
from .config import settings
from .db import get_connection, pool


class ShiftCreate(BaseModel):
    platform: str = Field(min_length=2, max_length=80)
    date: date
    hours_worked: float = Field(gt=0, le=24)
    gross_earned: float = Field(ge=0)
    deductions: float = Field(ge=0)
    net_received: float = Field(ge=0)
    screenshot_url: Optional[str] = None


class ShiftUpdate(BaseModel):
    platform: Optional[str] = Field(default=None, min_length=2, max_length=80)
    date: Optional[date] = None
    hours_worked: Optional[float] = Field(default=None, gt=0, le=24)
    gross_earned: Optional[float] = Field(default=None, ge=0)
    deductions: Optional[float] = Field(default=None, ge=0)
    net_received: Optional[float] = Field(default=None, ge=0)
    screenshot_url: Optional[str] = None


class CsvImportRequest(BaseModel):
    csv_text: str = Field(min_length=1)
    platform: str = Field(min_length=2, max_length=80)


class VerificationUpdate(BaseModel):
    verification_status: Literal["confirmed", "discrepancy_flagged", "unverifiable"]
    note: Optional[str] = Field(default=None, max_length=500)


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="FairGig Earnings Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_net(gross_earned: float, net_received: float) -> None:
    if net_received > gross_earned:
        raise HTTPException(status_code=400, detail="Net received cannot exceed gross earned.")


@app.get("/health")
def health_check(response: Response) -> dict:
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return {"status": "healthy", "service": "earnings-service", "database": "connected"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "service": "earnings-service", "database": "unavailable"}


@app.post("/shifts", status_code=status.HTTP_201_CREATED)
def create_shift(shift: ShiftCreate, identity: dict = Depends(require_roles("worker"))) -> dict:
    validate_net(shift.gross_earned, shift.net_received)
    try:
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO shifts
                    (worker_id, platform, date, hours_worked, gross_earned, deductions,
                     net_received, screenshot_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    UUID(identity["sub"]),
                    shift.platform,
                    shift.date,
                    shift.hours_worked,
                    shift.gross_earned,
                    shift.deductions,
                    shift.net_received,
                    shift.screenshot_url,
                ),
            ).fetchone()
            connection.commit()
            return row
    except UniqueViolation as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A shift for this platform and date already exists.",
        ) from error


@app.get("/shifts")
def list_shifts(
    platform: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    identity: dict = Depends(require_roles("worker")),
) -> dict:
    query = "SELECT * FROM shifts WHERE worker_id = %s"
    params: list = [UUID(identity["sub"])]
    if platform:
        query += " AND platform = %s"
        params.append(platform)
    if start_date:
        query += " AND date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND date <= %s"
        params.append(end_date)
    query += " ORDER BY date DESC, created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return {"shifts": rows, "count": len(rows)}


@app.post("/shifts/import-csv", status_code=status.HTTP_202_ACCEPTED)
def import_csv(payload: CsvImportRequest, identity: dict = Depends(require_roles("worker"))) -> dict:
    rows = list(csv.DictReader(io.StringIO(payload.csv_text)))
    return {
        "stub": True,
        "worker_id": identity["sub"],
        "platform": payload.platform,
        "rows_detected": len(rows),
        "message": "CSV import is not persisted yet.",
    }


@app.get("/shifts/verification-queue")
def verification_queue(
    verification_status: Optional[
        Literal["pending", "confirmed", "discrepancy_flagged", "unverifiable"]
    ] = None,
    _: dict = Depends(require_roles("verifier")),
) -> dict:
    query = """
        SELECT s.*, u.name AS worker_name
        FROM shifts s
        JOIN users u ON u.id = s.worker_id
    """
    params: list = []
    if verification_status:
        query += " WHERE s.verification_status = %s"
        params.append(verification_status)
    query += " ORDER BY s.created_at DESC LIMIT 100"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return {"shifts": rows, "count": len(rows)}


@app.patch("/shifts/{shift_id}/verification")
def verify_shift(
    shift_id: UUID,
    payload: VerificationUpdate,
    identity: dict = Depends(require_roles("verifier")),
) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE shifts
            SET verification_status = %s
            WHERE id = %s
            RETURNING *
            """,
            (payload.verification_status, shift_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Shift not found")
        connection.commit()
    return {
        **row,
        "verified_by": identity["sub"],
        "note": payload.note,
        "note_persisted": False,
    }


@app.get("/shifts/{shift_id}")
def get_shift(shift_id: UUID, identity: dict = Depends(require_roles("worker"))) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM shifts WHERE id = %s AND worker_id = %s",
            (shift_id, UUID(identity["sub"])),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return row


@app.put("/shifts/{shift_id}")
@app.patch("/shifts/{shift_id}")
def update_shift(
    shift_id: UUID,
    shift: ShiftUpdate,
    identity: dict = Depends(require_roles("worker")),
) -> dict:
    worker_id = UUID(identity["sub"])
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM shifts WHERE id = %s AND worker_id = %s",
            (shift_id, worker_id),
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Shift not found")

        update_data = shift.model_dump(exclude_unset=True)
        if not update_data:
            return existing
        validate_net(
            update_data.get("gross_earned", existing["gross_earned"]),
            update_data.get("net_received", existing["net_received"]),
        )
        assignments = ", ".join(f"{column} = %s" for column in update_data)
        params = [*update_data.values(), shift_id, worker_id]
        try:
            row = connection.execute(
                f"UPDATE shifts SET {assignments} WHERE id = %s AND worker_id = %s RETURNING *",
                params,
            ).fetchone()
            connection.commit()
            return row
        except UniqueViolation as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A shift for this platform and date already exists.",
            ) from error


@app.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(shift_id: UUID, identity: dict = Depends(require_roles("worker"))) -> Response:
    with get_connection() as connection:
        deleted = connection.execute(
            "DELETE FROM shifts WHERE id = %s AND worker_id = %s RETURNING id",
            (shift_id, UUID(identity["sub"])),
        ).fetchone()
        if deleted is None:
            raise HTTPException(status_code=404, detail="Shift not found")
        connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/earnings/summary")
def earnings_summary(identity: dict = Depends(require_roles("worker"))) -> dict:
    with get_connection() as connection:
        summary = connection.execute(
            """
            SELECT
                COALESCE(SUM(hours_worked), 0) AS total_hours,
                COALESCE(SUM(gross_earned), 0) AS total_gross,
                COALESCE(SUM(deductions), 0) AS total_deductions,
                COALESCE(SUM(net_received), 0) AS total_net,
                COUNT(*) AS total_shifts
            FROM shifts
            WHERE worker_id = %s
            """,
            (UUID(identity["sub"]),),
        ).fetchone()
    total_hours = summary["total_hours"]
    hourly_rate = summary["total_net"] / total_hours if total_hours else 0
    return {**summary, "effective_hourly_rate": round(hourly_rate, 2)}
