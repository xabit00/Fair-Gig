from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time
from .db import get_connection
from .auth import verify_token

app = FastAPI(title="FairGig Earnings Service", version="1.0.0")

class ShiftCreate(BaseModel):
    platform: str
    work_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours_worked: float = Field(..., gt=0)
    gross_earned: float = Field(..., ge=0)
    deductions: float = Field(..., ge=0)
    commission: float = Field(0.0, ge=0)
    net_received: float = Field(..., ge=0)
    status: str = "pending"

class ShiftUpdate(BaseModel):
    platform: Optional[str] = None
    work_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours_worked: Optional[float] = None
    gross_earned: Optional[float] = None
    deductions: Optional[float] = None
    commission: Optional[float] = None
    net_received: Optional[float] = None
    status: Optional[str] = None

def _validate_shift_state(
    hours_worked: float,
    gross_earned: float,
    deductions: float,
    commission: float,
    net_received: float
) -> None:
    """Validate complete shift financial state."""
    if hours_worked <= 0:
        raise HTTPException(status_code=400, detail="Hours worked must be greater than 0.")
    if gross_earned < 0:
        raise HTTPException(status_code=400, detail="Gross earned cannot be negative.")
    if deductions < 0:
        raise HTTPException(status_code=400, detail="Deductions cannot be negative.")
    if commission < 0:
        raise HTTPException(status_code=400, detail="Commission cannot be negative.")
    if net_received < 0:
        raise HTTPException(status_code=400, detail="Net received cannot be negative.")
    if net_received > gross_earned:
        raise HTTPException(status_code=400, detail="Net received cannot exceed gross earned.")

@app.get("/health")
def health_check():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "service": "earnings-service", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "earnings-service", "error": str(e)}

@app.post("/shifts", status_code=status.HTTP_201_CREATED)
def create_shift(shift: ShiftCreate, token_data: dict = Depends(verify_token)):
    worker_id = token_data["sub"]
    
    _validate_shift_state(
        shift.hours_worked, shift.gross_earned, shift.deductions,
        shift.commission, shift.net_received
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shifts (worker_id, platform, work_date, start_time, end_time, hours_worked, gross_earned, deductions, commission, net_received, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING shift_id, worker_id, platform, work_date, hours_worked, gross_earned, deductions, commission, net_received, status, created_at
                """,
                (
                    worker_id, shift.platform, shift.work_date, shift.start_time, shift.end_time,
                    shift.hours_worked, shift.gross_earned, shift.deductions, shift.commission,
                    shift.net_received, shift.status
                )
            )
            new_shift = cur.fetchone()
            conn.commit()
            return new_shift

@app.get("/shifts")
def list_shifts(
    platform: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    token_data: dict = Depends(verify_token)
):
    worker_id = token_data["sub"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = "SELECT * FROM shifts WHERE worker_id = %s"
            params = [worker_id]

            if platform:
                query += " AND platform = %s"
                params.append(platform)
            if start_date:
                query += " AND work_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND work_date <= %s"
                params.append(end_date)

            query += " ORDER BY work_date DESC"
            cur.execute(query, params)
            shifts = cur.fetchall()
            return {"shifts": shifts, "count": len(shifts)}

@app.get("/shifts/{shift_id}")
def get_shift(shift_id: str, token_data: dict = Depends(verify_token)):
    worker_id = token_data["sub"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM shifts WHERE shift_id = %s AND worker_id = %s",
                (shift_id, worker_id)
            )
            shift = cur.fetchone()
            if not shift:
                raise HTTPException(status_code=404, detail="Shift not found or unauthorized")
            return shift

@app.put("/shifts/{shift_id}")
def update_shift(shift_id: str, shift: ShiftUpdate, token_data: dict = Depends(verify_token)):
    worker_id = token_data["sub"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM shifts WHERE shift_id = %s AND worker_id = %s", (shift_id, worker_id))
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Shift not found or unauthorized")

            update_data = shift.model_dump(exclude_unset=True)
            if not update_data:
                return existing

            # Build final state by merging existing with updates
            final_hours = update_data.get("hours_worked", existing["hours_worked"])
            final_gross = update_data.get("gross_earned", existing["gross_earned"])
            final_deductions = update_data.get("deductions", existing["deductions"])
            final_commission = update_data.get("commission", existing["commission"])
            final_net = update_data.get("net_received", existing["net_received"])

            # Validate complete final state
            _validate_shift_state(final_hours, final_gross, final_deductions, final_commission, final_net)

            set_clauses = []
            params = []
            for key, val in update_data.items():
                set_clauses.append(f"{key} = %s")
                params.append(val)
            
            params.extend([shift_id, worker_id])
            query = f"UPDATE shifts SET {', '.join(set_clauses)} WHERE shift_id = %s AND worker_id = %s RETURNING *"
            
            cur.execute(query, params)
            updated = cur.fetchone()
            conn.commit()
            return updated

@app.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(shift_id: str, token_data: dict = Depends(verify_token)):
    worker_id = token_data["sub"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM shifts WHERE shift_id = %s AND worker_id = %s RETURNING shift_id", (shift_id, worker_id))
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Shift not found or unauthorized")
            conn.commit()

@app.get("/earnings/summary")
def earnings_summary(token_data: dict = Depends(verify_token)):
    worker_id = token_data["sub"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    COALESCE(SUM(hours_worked), 0) as total_hours,
                    COALESCE(SUM(gross_earned), 0) as total_gross,
                    COALESCE(SUM(deductions), 0) as total_deductions,
                    COALESCE(SUM(commission), 0) as total_commission,
                    COALESCE(SUM(net_received), 0) as total_net,
                    COUNT(*) as total_shifts
                FROM shifts 
                WHERE worker_id = %s
                """,
                (worker_id,)
            )
            summary = cur.fetchone()
            total_net = summary["total_net"]
            total_hours = summary["total_hours"]
            effective_hourly_rate = (total_net / total_hours) if total_hours > 0 else 0.0
            
            return {
                **summary,
                "effective_hourly_rate": round(effective_hourly_rate, 2)
            }

