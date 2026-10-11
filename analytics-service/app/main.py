from contextlib import asynccontextmanager
from datetime import date, timedelta
import statistics

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health(connection: Connection = Depends(get_connection)) -> dict:
    connection.execute("SELECT 1")
    return {"status": "ok", "service": "analytics-service", "database": "connected"}


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


@app.get("/analytics/overview")
def analytics_overview(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> dict:
    today = date.today()
    try:
        start_date = date.fromisoformat(from_date.split("T")[0]) if from_date else today - timedelta(days=30)
    except Exception:
        start_date = today - timedelta(days=30)

    try:
        end_date = date.fromisoformat(to_date.split("T")[0]) if to_date else today
    except Exception:
        end_date = today

    worker_rows = connection.execute(
        """
        SELECT worker_id, SUM(net_received) AS net_sum
        FROM shifts
        WHERE date >= %s AND date <= %s
        GROUP BY worker_id
        """,
        (start_date, end_date),
    ).fetchall()

    net_sums = [float(row["net_sum"]) for row in worker_rows if row.get("net_sum") is not None]
    total_workers = len(worker_rows)
    if total_workers < settings.minimum_group_size:
        return {"suppressed": True, "minimum_group_size": settings.minimum_group_size}
    avg_net_earnings = round(float(sum(net_sums) / total_workers), 2) if total_workers > 0 else 0.0
    median_net_earnings = round(float(statistics.median(net_sums)), 2) if total_workers > 0 else 0.0

    comm_row = connection.execute(
        """
        SELECT AVG(deductions / gross_earned * 100.0) AS avg_commission_pct
        FROM shifts
        WHERE date >= %s AND date <= %s AND gross_earned > 0
        """,
        (start_date, end_date),
    ).fetchone()

    avg_commission_pct = 0.0
    if comm_row and comm_row.get("avg_commission_pct") is not None:
        avg_commission_pct = round(float(comm_row["avg_commission_pct"]), 2)

    return {
        "suppressed": False,
        "minimum_group_size": settings.minimum_group_size,
        "total_workers": total_workers,
        "avg_net_earnings": avg_net_earnings,
        "median_net_earnings": median_net_earnings,
        "avg_commission_pct": avg_commission_pct,
        "period": {
            "from": str(start_date),
            "to": str(end_date),
        },
    }


@app.get("/analytics/earnings-trends")
def earnings_trends(
    group: str = Query("month"),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT TO_CHAR(DATE_TRUNC('month', date), 'YYYY-MM') AS label,
               ROUND(SUM(net_received)::numeric, 2) AS total_net,
               COUNT(DISTINCT worker_id) AS worker_count
        FROM shifts
        GROUP BY DATE_TRUNC('month', date)
        HAVING COUNT(DISTINCT worker_id) >= %s
        ORDER BY DATE_TRUNC('month', date) ASC
        """,
        (settings.minimum_group_size,),
    ).fetchall()

    return [
        {
            "label": str(row["label"]),
            "total_net": float(row["total_net"]) if row.get("total_net") is not None else 0.0,
            "worker_count": int(row["worker_count"]),
        }
        for row in rows
    ]


@app.get("/analytics/platforms")
def analytics_platforms(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> list[dict]:
    conditions = []
    params = []
    if from_date:
        try:
            conditions.append("date >= %s")
            params.append(date.fromisoformat(from_date.split("T")[0]))
        except Exception:
            pass
    if to_date:
        try:
            conditions.append("date <= %s")
            params.append(date.fromisoformat(to_date.split("T")[0]))
        except Exception:
            pass

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT platform AS label,
               ROUND((SUM(net_received) / NULLIF(COUNT(DISTINCT worker_id), 0))::numeric, 2) AS avg_net_per_worker,
               COUNT(DISTINCT worker_id) AS worker_count
        FROM shifts
        {where_sql}
        GROUP BY platform
        HAVING COUNT(DISTINCT worker_id) >= %s
        ORDER BY platform ASC
    """
    rows = connection.execute(query, (*params, settings.minimum_group_size)).fetchall()

    return [
        {
            "label": str(row["label"]),
            "avg_net_per_worker": float(row["avg_net_per_worker"]) if row.get("avg_net_per_worker") is not None else 0.0,
            "worker_count": int(row["worker_count"]),
        }
        for row in rows
    ]


@app.get("/analytics/zones")
def analytics_zones(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> list[dict]:
    conditions = ["u.city_zone IS NOT NULL"]
    params = []
    if from_date:
        try:
            conditions.append("s.date >= %s")
            params.append(date.fromisoformat(from_date.split("T")[0]))
        except Exception:
            pass
    if to_date:
        try:
            conditions.append("s.date <= %s")
            params.append(date.fromisoformat(to_date.split("T")[0]))
        except Exception:
            pass

    where_sql = f"WHERE {' AND '.join(conditions)}"

    query = f"""
        SELECT u.city_zone AS label,
               ROUND((SUM(s.net_received) / NULLIF(COUNT(DISTINCT s.worker_id), 0))::numeric, 2) AS avg_net_per_worker,
               COUNT(DISTINCT s.worker_id) AS worker_count
        FROM shifts s
        JOIN users u ON u.id = s.worker_id
        {where_sql}
        GROUP BY u.city_zone
        HAVING COUNT(DISTINCT s.worker_id) >= %s
        ORDER BY u.city_zone ASC
    """
    rows = connection.execute(query, (*params, settings.minimum_group_size)).fetchall()

    return [
        {
            "label": str(row["label"]),
            "avg_net_per_worker": float(row["avg_net_per_worker"]) if row.get("avg_net_per_worker") is not None else 0.0,
            "worker_count": int(row["worker_count"]),
        }
        for row in rows
    ]


@app.get("/analytics/grievances")
def analytics_grievances(
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> list[dict]:
    conditions = []
    params = []
    if from_date:
        try:
            conditions.append("created_at >= %s")
            params.append(date.fromisoformat(from_date.split("T")[0]))
        except Exception:
            pass
    if to_date:
        try:
            conditions.append("created_at <= %s")
            params.append(date.fromisoformat(to_date.split("T")[0]))
        except Exception:
            pass

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT category AS label,
               COUNT(*) AS count,
               COUNT(DISTINCT worker_id) AS worker_count
        FROM grievances
        {where_sql}
        GROUP BY category
        HAVING COUNT(DISTINCT worker_id) >= %s
        ORDER BY category ASC
    """
    rows = connection.execute(query, (*params, settings.minimum_group_size)).fetchall()

    return [
        {
            "label": str(row["label"]),
            "count": int(row["count"]),
            "worker_count": int(row["worker_count"]),
        }
        for row in rows
    ]


@app.get("/analytics/vulnerability")
def analytics_vulnerability(
    months: int = Query(2),
    connection: Connection = Depends(get_connection),
    _: dict = Depends(require_advocate),
) -> list[dict]:
    month_rows = connection.execute(
        """
        SELECT DISTINCT DATE_TRUNC('month', date) AS m
        FROM shifts
        WHERE date IS NOT NULL
        ORDER BY m DESC
        LIMIT %s
        """,
        (max(months, 2),),
    ).fetchall()

    if len(month_rows) < 2:
        return []

    curr_month = month_rows[0]["m"]
    prev_month = month_rows[1]["m"]

    worker_rows = connection.execute(
        """
        SELECT worker_id,
               SUM(CASE WHEN DATE_TRUNC('month', date) = %s THEN net_received ELSE 0 END) AS curr_net,
               SUM(CASE WHEN DATE_TRUNC('month', date) = %s THEN net_received ELSE 0 END) AS prev_net
        FROM shifts
        WHERE DATE_TRUNC('month', date) IN (%s, %s)
        GROUP BY worker_id
        """,
        (curr_month, prev_month, curr_month, prev_month),
    ).fetchall()

    declining_workers = set()
    for row in worker_rows:
        w_id = row["worker_id"]
        prev = float(row["prev_net"] or 0)
        curr = float(row["curr_net"] or 0)
        if prev > 0:
            decline_pct = (prev - curr) / prev * 100.0
            if decline_pct > 20:
                declining_workers.add(w_id)

    platform_worker_rows = connection.execute(
        """
        SELECT platform, worker_id
        FROM shifts
        WHERE platform IS NOT NULL
          AND DATE_TRUNC('month', date) IN (%s, %s)
        GROUP BY platform, worker_id
        """,
        (curr_month, prev_month),
    ).fetchall()

    platform_workers: dict[str, set] = {}
    for row in platform_worker_rows:
        plat = str(row["platform"])
        platform_workers.setdefault(plat, set()).add(row["worker_id"])

    zone_worker_rows = connection.execute(
        """
        SELECT u.city_zone, s.worker_id
        FROM shifts s
        JOIN users u ON u.id = s.worker_id
        WHERE u.city_zone IS NOT NULL
          AND DATE_TRUNC('month', s.date) IN (%s, %s)
        GROUP BY u.city_zone, s.worker_id
        """,
        (curr_month, prev_month),
    ).fetchall()

    zone_workers: dict[str, set] = {}
    for row in zone_worker_rows:
        zone = str(row["city_zone"])
        zone_workers.setdefault(zone, set()).add(row["worker_id"])

    results: list[dict] = []

    total_platform_workers = len(set.union(*platform_workers.values())) if platform_workers else 0
    for plat in sorted(platform_workers):
        workers_in_group = platform_workers[plat]
        group_size = len(workers_in_group)
        if group_size < settings.minimum_group_size:
            continue
        if 0 < (total_platform_workers - group_size) < settings.minimum_group_size:
            continue
        dec_count = sum(1 for w in workers_in_group if w in declining_workers)
        results.append({
            "group_type": "platform",
            "label": plat,
            "group_size": group_size,
            "declining_count": dec_count,
        })

    total_zone_workers = len(set.union(*zone_workers.values())) if zone_workers else 0
    for zone in sorted(zone_workers):
        workers_in_group = zone_workers[zone]
        group_size = len(workers_in_group)
        if group_size < settings.minimum_group_size:
            continue
        if 0 < (total_zone_workers - group_size) < settings.minimum_group_size:
            continue
        dec_count = sum(1 for w in workers_in_group if w in declining_workers)
        results.append({
            "group_type": "zone",
            "label": zone,
            "group_size": group_size,
            "declining_count": dec_count,
        })

    return results

