"""Seed FairGig with realistic demo data for local development."""

from __future__ import annotations

import os
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import bcrypt
import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fairgig",
)
SEED_PASSWORD = "FairGig123!"
NAMESPACE = uuid.UUID("14588811-1f5d-449e-8402-89b95bd4677e")

CITY_ZONES = (
    "Karachi Central",
    "Lahore North",
    "Islamabad-Rawalpindi",
    "Faisalabad Urban",
)
CATEGORIES = ("ride_hailing", "delivery", "freelancing")
PLATFORMS = {
    "ride_hailing": ("Careem", "inDrive", "Yango"),
    "delivery": ("Foodpanda", "Bykea", "Cheetay"),
    "freelancing": ("Upwork", "Fiverr", "PeoplePerHour"),
}
BASE_RATES = {
    "ride_hailing": (520, 850),
    "delivery": (350, 560),
    "freelancing": (900, 1700),
}
BASE_COMMISSIONS = {
    "Careem": 0.20,
    "inDrive": 0.11,
    "Yango": 0.16,
    "Foodpanda": 0.18,
    "Bykea": 0.14,
    "Cheetay": 0.15,
    "Upwork": 0.10,
    "Fiverr": 0.20,
    "PeoplePerHour": 0.15,
}
COMMISSION_INCREASES = {
    "Yango": 0.05,
    "Foodpanda": 0.04,
    "Fiverr": 0.03,
}
WORKER_NAMES = (
    "Ahsan Raza", "Areeba Khan", "Bilal Ahmed", "Danish Ali", "Eman Fatima",
    "Farhan Qureshi", "Hafsa Noor", "Hamza Siddiqui", "Hira Aslam", "Imran Shah",
    "Iqra Javed", "Kashif Mehmood", "Laiba Tariq", "Maham Riaz", "Mohsin Abbas",
    "Nadia Saleem", "Noman Akhtar", "Rabia Iqbal", "Rafay Hassan", "Rida Khalid",
    "Saad Malik", "Saba Arshad", "Salman Butt", "Sana Waheed", "Shahzaib Khan",
    "Sidra Amin", "Sohail Anwar", "Sumaira Bashir", "Talha Zafar", "Umer Farooq",
    "Usama Mir", "Waqas Haider", "Yasir Nawaz", "Zainab Asif", "Zohaib Tariq",
    "Anam Sheikh", "Fahad Latif", "Komal Younis", "Mustafa Saeed", "Neha Ilyas",
)


def stable_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, key)


def money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def utc_at(day: date, hour: int = 12) -> datetime:
    return datetime.combine(day, time(hour=hour), tzinfo=timezone.utc)


def build_workers(password_hash: str) -> list[tuple]:
    workers = []
    for index, name in enumerate(WORKER_NAMES):
        category = CATEGORIES[index % len(CATEGORIES)]
        city_zone = CITY_ZONES[index % len(CITY_ZONES)]
        email_name = name.lower().replace(" ", ".")
        workers.append(
            (
                stable_uuid(f"worker-{index + 1}"),
                name,
                f"{email_name}@example.com",
                password_hash,
                "worker",
                city_zone,
                category,
            )
        )
    return workers


def build_shifts(workers: list[tuple], start_day: date, rng: random.Random) -> list[tuple]:
    shifts = []
    commission_change_day = start_day + timedelta(days=45)

    for worker_index, worker in enumerate(workers):
        worker_id, _, _, _, _, _, category = worker
        low_rate, high_rate = BASE_RATES[category]
        platforms = PLATFORMS[category]

        for offset in range(90):
            shift_day = start_day + timedelta(days=offset)
            if (offset + worker_index) % 7 not in (0, 2, 4, 6):
                continue

            platform = platforms[(offset // 7 + worker_index) % len(platforms)]
            hours = rng.uniform(4.5, 9.5) if category != "freelancing" else rng.uniform(3.0, 7.5)
            hourly_rate = rng.uniform(low_rate, high_rate)

            if worker_index % 9 == 0 and offset >= 60:
                hours *= 0.58
                hourly_rate *= 0.90

            gross = hours * hourly_rate
            commission = BASE_COMMISSIONS[platform]
            if shift_day >= commission_change_day:
                commission += COMMISSION_INCREASES.get(platform, 0)

            deductions = gross * commission + rng.uniform(20, 95)
            if worker_index in (5, 22) and offset in (68, 82):
                deductions += gross * 0.18

            net = max(gross - deductions, 0)
            status_roll = rng.random()
            if status_roll < 0.65:
                verification_status = "confirmed"
            elif status_roll < 0.88:
                verification_status = "pending"
            elif status_roll < 0.96:
                verification_status = "discrepancy_flagged"
            else:
                verification_status = "unverifiable"

            screenshot_url = (
                f"https://files.example.test/shifts/{worker_id}/{shift_day.isoformat()}.jpg"
                if verification_status != "unverifiable"
                else None
            )
            shifts.append(
                (
                    stable_uuid(f"shift-{worker_id}-{platform}-{shift_day}"),
                    worker_id,
                    platform,
                    shift_day,
                    money(hours),
                    money(gross),
                    money(deductions),
                    money(net),
                    verification_status,
                    screenshot_url,
                    utc_at(shift_day, 20),
                )
            )
    return shifts


def insert_grievances(cursor: psycopg.Cursor, workers: list[tuple], start_day: date) -> None:
    clusters = (
        (stable_uuid("cluster-commission"), "Unexpected commission increase", None, "commission", "escalated"),
        (stable_uuid("cluster-deactivation"), "Accounts deactivated without review", None, "deactivation", "monitoring"),
        (stable_uuid("cluster-delayed-payment"), "Delayed weekly payments", None, "payment_delay", "open"),
    )
    cursor.executemany(
        """
        INSERT INTO grievance_clusters (id, title, platform, category, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        clusters,
    )

    templates = (
        ("Yango", "commission", "The deduction percentage increased without a clear notice.", 0),
        ("Foodpanda", "commission", "My weekly statement shows a higher platform fee than last month.", 0),
        ("Fiverr", "commission", "The final payout was lower after a new fee appeared.", 0),
        ("Careem", "deactivation", "My account was paused and the appeal reason was not explained.", 1),
        ("Bykea", "deactivation", "I was deactivated after a customer complaint without a review call.", 1),
        ("Upwork", "payment_delay", "A completed milestone has remained pending beyond the stated period.", 2),
        ("Cheetay", "payment_delay", "My weekly transfer arrived late for the second time.", 2),
        ("inDrive", "safety", "I need a documented way to report unsafe pickup locations.", None),
    )
    grievances = []
    tags = []
    for index in range(24):
        platform, category, description, cluster_index = templates[index % len(templates)]
        worker_id = workers[(index * 7) % len(workers)][0]
        grievance_id = stable_uuid(f"grievance-{index + 1}")
        status = ("submitted", "reviewing", "escalated", "resolved")[index % 4]
        cluster_id = clusters[cluster_index][0] if cluster_index is not None else None
        created_day = start_day + timedelta(days=10 + index * 3)
        grievances.append(
            (grievance_id, worker_id, platform, category, description, status, cluster_id, utc_at(created_day))
        )
        tags.append((grievance_id, category.replace("_", "-")))
        if category == "commission":
            tags.append((grievance_id, "unexpected-deduction"))

    cursor.executemany(
        """
        INSERT INTO grievances
            (id, worker_id, platform, category, description, status, cluster_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        grievances,
    )
    cursor.executemany(
        "INSERT INTO grievance_tags (grievance_id, tag) VALUES (%s, %s)",
        tags,
    )


def main() -> None:
    rng = random.Random(2026)
    password_hash = bcrypt.hashpw(SEED_PASSWORD.encode(), bcrypt.gensalt()).decode()
    workers = build_workers(password_hash)
    start_day = date.today() - timedelta(days=89)
    shifts = build_shifts(workers, start_day, rng)

    staff = (
        (stable_uuid("verifier-1"), "Muneeb Verification", "verifier@fairgig.test", password_hash, "verifier", None, None),
        (stable_uuid("advocate-1"), "Amna Advocacy", "advocate@fairgig.test", password_hash, "advocate", None, None),
    )

    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE grievance_tags, grievances, grievance_clusters, shifts, refresh_tokens, users RESTART IDENTITY CASCADE"
            )
            cursor.executemany(
                """
                INSERT INTO users (id, name, email, password_hash, role, city_zone, category)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [*workers, *staff],
            )
            cursor.executemany(
                """
                INSERT INTO shifts
                    (id, worker_id, platform, date, hours_worked, gross_earned,
                     deductions, net_received, verification_status, screenshot_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                shifts,
            )
            insert_grievances(cursor, workers, start_day)
        connection.commit()

    print(f"Seeded {len(workers)} workers, {len(shifts)} shifts, and 24 grievances.")
    print(f"Demo password for all seeded accounts: {SEED_PASSWORD}")


if __name__ == "__main__":
    main()

