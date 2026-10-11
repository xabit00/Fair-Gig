from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from psycopg import Connection

from .auth import require_advocate
from .config import settings
from .db import get_connection, pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(
    title="FairGig Analytics Service",
    version="1.0.0",
    description="K-anonymous aggregate earnings metrics. Groups smaller than five workers are omitted.",
    lifespan=lifespan,
)


@app.get("/health")
def health(connection: Connection = Depends(get_connection)) -> dict:
    connection.execute("SELECT 1")
    return {"service": "analytics-service", "status": "ok", "database": "connected"}


@app.get("/kpis")
def kpis(
    _: dict = Depends(require_advocate),
    connection: Connection = Depends(get_connection),
) -> dict:
    row = connection.execute(
        """
        WITH monthly_income AS (
            SELECT s.worker_id,
                   DATE_TRUNC('month', s.date) AS month,
                   SUM(s.net_received) AS net_income,
                   SUM(s.gross_earned) AS gross_income,
                   SUM(s.deductions) AS deductions
            FROM shifts s
            JOIN users u ON u.id = s.worker_id
            WHERE u.role = 'worker'
            GROUP BY s.worker_id, DATE_TRUNC('month', s.date)
        )
        SELECT COUNT(DISTINCT worker_id) AS worker_count,
               ROUND(SUM(net_income), 2) AS total_net_received,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY net_income)::numeric, 2)
                   AS median_monthly_income,
               ROUND((SUM(deductions) / NULLIF(SUM(gross_income), 0) * 100), 2)
                   AS effective_deduction_percent
        FROM monthly_income
        HAVING COUNT(DISTINCT worker_id) >= %s
        """,
        (settings.minimum_group_size,),
    ).fetchone()
    if row is None:
        return {"suppressed": True, "minimum_group_size": settings.minimum_group_size}
    return {"suppressed": False, "minimum_group_size": settings.minimum_group_size, **row}


@app.get("/platforms")
def platform_breakdown(
    _: dict = Depends(require_advocate),
    connection: Connection = Depends(get_connection),
) -> dict:
    rows = connection.execute(
        """
        WITH worker_months AS (
            SELECT platform,
                   worker_id,
                   DATE_TRUNC('month', date) AS month,
                   SUM(net_received) AS net_income,
                   SUM(gross_earned) AS gross_income,
                   SUM(deductions) AS deductions
            FROM shifts
            GROUP BY platform, worker_id, DATE_TRUNC('month', date)
        )
        SELECT platform,
               COUNT(DISTINCT worker_id) AS worker_count,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY net_income)::numeric, 2)
                   AS median_monthly_income,
               ROUND((SUM(deductions) / NULLIF(SUM(gross_income), 0) * 100), 2)
                   AS effective_deduction_percent
        FROM worker_months
        GROUP BY platform
        HAVING COUNT(DISTINCT worker_id) >= %s
        ORDER BY platform
        """,
        (settings.minimum_group_size,),
    ).fetchall()
    return {"minimum_group_size": settings.minimum_group_size, "groups": rows}


@app.get("/city-zones")
def city_zone_breakdown(
    _: dict = Depends(require_advocate),
    connection: Connection = Depends(get_connection),
) -> dict:
    rows = connection.execute(
        """
        WITH worker_months AS (
            SELECT u.city_zone,
                   s.worker_id,
                   DATE_TRUNC('month', s.date) AS month,
                   SUM(s.net_received) AS net_income
            FROM shifts s
            JOIN users u ON u.id = s.worker_id
            WHERE u.city_zone IS NOT NULL
            GROUP BY u.city_zone, s.worker_id, DATE_TRUNC('month', s.date)
        )
        SELECT city_zone,
               COUNT(DISTINCT worker_id) AS worker_count,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY net_income)::numeric, 2)
                   AS median_monthly_income
        FROM worker_months
        GROUP BY city_zone
        HAVING COUNT(DISTINCT worker_id) >= %s
        ORDER BY city_zone
        """,
        (settings.minimum_group_size,),
    ).fetchall()
    return {"minimum_group_size": settings.minimum_group_size, "groups": rows}

