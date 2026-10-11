from datetime import date

from app.detector import detect_anomalies


def test_flags_high_deduction_and_monthly_drop() -> None:
    records = []
    for day in range(1, 10):
        records.append(
            {
                "date": date(2026, 1, day),
                "platform": "Careem",
                "gross_earned": 2000,
                "deductions": 200,
                "net_received": 1800,
            }
        )
    records.append(
        {
            "date": date(2026, 1, 10),
            "platform": "Careem",
            "gross_earned": 3000,
            "deductions": 1800,
            "net_received": 1200,
        }
    )
    records.append(
        {
            "date": date(2026, 2, 10),
            "platform": "Careem",
            "gross_earned": 3000,
            "deductions": 200,
            "net_received": 2800,
        }
    )

    anomalies = detect_anomalies(records)
    types = {anomaly["type"] for anomaly in anomalies}
    assert "high_deduction" in types
    assert "monthly_income_drop" in types


def test_normal_earnings_do_not_trigger_alerts() -> None:
    records = [
        {
            "date": date(2026, month, 1),
            "platform": "Careem",
            "gross_earned": 2000,
            "deductions": 200,
            "net_received": 1800,
        }
        for month in range(1, 4)
    ]

    assert detect_anomalies(records) == []


def test_missing_history_and_zero_previous_income_are_safe() -> None:
    assert detect_anomalies([]) == []
    records = [
        {
            "date": date(2026, 1, 1),
            "platform": "Upwork",
            "gross_earned": 0,
            "deductions": 0,
            "net_received": 0,
        },
        {
            "date": date(2026, 2, 1),
            "platform": "Upwork",
            "gross_earned": 1000,
            "deductions": 0,
            "net_received": 1000,
        },
    ]

    assert detect_anomalies(records) == []


def test_exactly_twenty_percent_drop_is_not_flagged() -> None:
    records = [
        {
            "date": date(2026, 1, 1),
            "platform": "Foodpanda",
            "gross_earned": 1000,
            "deductions": 100,
            "net_received": 1000,
        },
        {
            "date": date(2026, 2, 1),
            "platform": "Foodpanda",
            "gross_earned": 800,
            "deductions": 100,
            "net_received": 800,
        },
    ]

    assert detect_anomalies(records) == []
