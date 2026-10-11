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

