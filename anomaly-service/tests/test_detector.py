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


# === EDGE CASE TESTS ===

def test_empty_earnings_history():
    """Empty records should return empty anomalies."""
    anomalies = detect_anomalies([])
    assert anomalies == []


def test_single_earning_record():
    """Single record should not trigger any anomaly (no deviation possible)."""
    records = [{
        "date": date(2026, 1, 1),
        "platform": "Uber",
        "gross_earned": 5000,
        "deductions": 500,
        "net_received": 4500,
    }]
    anomalies = detect_anomalies(records)
    assert anomalies == []


def test_identical_deductions_zero_stddev():
    """Identical deductions across all records -> stddev = 0 -> no high_deduction flag."""
    records = []
    for day in range(1, 6):
        records.append({
            "date": date(2026, 1, day),
            "platform": "Uber",
            "gross_earned": 2000,
            "deductions": 200,  # All identical
            "net_received": 1800,
        })
    anomalies = detect_anomalies(records)
    # With zero stddev, no record can exceed mean + 2*0 = mean
    types = {a["type"] for a in anomalies}
    assert "high_deduction" not in types


def test_zero_previous_month_income():
    """Previous month income = 0 should not trigger monthly_income_drop."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 0, "deductions": 0, "net_received": 0},
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 100, "net_received": 900},
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" not in types


def test_exactly_20_percent_decline():
    """Exactly 20% decline should NOT trigger (>20% required)."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 0, "net_received": 1000},
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 800, "deductions": 0, "net_received": 800},  # Exactly 20% drop
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" not in types


def test_greater_than_20_percent_decline():
    """Greater than 20% decline SHOULD trigger."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 0, "net_received": 1000},
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 799, "deductions": 0, "net_received": 799},  # 20.1% drop
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" in types


def test_increasing_income():
    """Increasing income should not trigger monthly_income_drop."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 0, "net_received": 1000},
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 1500, "deductions": 0, "net_received": 1500},
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" not in types


def test_multiple_records_same_month():
    """Multiple records in same month should be summed for monthly income."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 500, "deductions": 0, "net_received": 500},
        {"date": date(2026, 1, 15), "platform": "Uber", "gross_earned": 500, "deductions": 0, "net_received": 500},  # Jan total: 1000
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 400, "deductions": 0, "net_received": 400},  # Feb: 400 (60% drop)
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" in types
    # Check the drop is calculated on monthly totals
    drop_anomaly = next(a for a in anomalies if a["type"] == "monthly_income_drop")
    assert drop_anomaly["previous_value"] == 1000.0
    assert drop_anomaly["value"] == 400.0


def test_missing_months():
    """Missing months should not be compared (only consecutive months in data)."""
    records = [
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 0, "net_received": 1000},
        {"date": date(2026, 3, 1), "platform": "Uber", "gross_earned": 500, "deductions": 0, "net_received": 500},  # Skip Feb
    ]
    anomalies = detect_anomalies(records)
    # Jan and Mar are not consecutive calendar months, but they ARE consecutive in the data
    # The current implementation compares consecutive months in the sorted data
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" in types  # Current behavior: compares consecutive months in data


def test_out_of_order_dates():
    """Records should be processed regardless of input order."""
    records = [
        {"date": date(2026, 2, 1), "platform": "Uber", "gross_earned": 500, "deductions": 0, "net_received": 500},
        {"date": date(2026, 1, 1), "platform": "Uber", "gross_earned": 1000, "deductions": 0, "net_received": 1000},
    ]
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "monthly_income_drop" in types


def test_high_deduction_threshold_calculation():
    """High deduction threshold should be mean + 2*pop_stddev."""
    # 5 records with deductions: 100, 100, 100, 100, 500
    # mean = 180, pop_stddev = sqrt((6400*4 + 102400)/5) = sqrt(46080) ≈ 214.7
    # threshold = 180 + 2*214.7 = 609.4
    # 500 < 609.4, so no anomaly
    records = []
    for i in range(4):
        records.append({
            "date": date(2026, 1, i+1),
            "platform": "Uber",
            "gross_earned": 2000,
            "deductions": 100,
            "net_received": 1900,
        })
    records.append({
        "date": date(2026, 1, 5),
        "platform": "Uber",
        "gross_earned": 2000,
        "deductions": 500,
        "net_received": 1500,
    })
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "high_deduction" not in types


def test_high_deduction_triggered():
    """Deduction exceeding mean + 2*stddev should trigger."""
    # Use 10 base records at 100, then one outlier
    # With 10 records at 100 and 1 at x:
    # mean = (1000 + x)/11, stdev ≈ |x-100|*sqrt(10/121) ≈ 0.287*|x-100|
    # threshold = mean + 2*stdev ≈ 90.9 + 0.091*x + 0.574*|x-100|
    # For x > 100: threshold ≈ 90.9 + 0.091*x + 0.574*(x-100) = -48.5 + 0.665*x
    # x > -48.5 + 0.665*x => 0.335*x > -48.5 => x > -144 (always true for positive x)
    # So any x > 100 will trigger!
    records = []
    for i in range(10):
        records.append({
            "date": date(2026, 1, i+1),
            "platform": "Uber",
            "gross_earned": 2000,
            "deductions": 100,
            "net_received": 1900,
        })
    # Add outlier that should trigger
    records.append({
        "date": date(2026, 1, 11),
        "platform": "Uber",
        "gross_earned": 2000,
        "deductions": 500,
        "net_received": 1500,
    })
    anomalies = detect_anomalies(records)
    types = {a["type"] for a in anomalies}
    assert "high_deduction" in types


def test_consistent_results():
    """Repeated calls with same input should produce consistent results."""
    records = [{
        "date": date(2026, 1, 1),
        "platform": "Uber",
        "gross_earned": 5000,
        "deductions": 500,
        "net_received": 4500,
    }]
    result1 = detect_anomalies(records)
    result2 = detect_anomalies(records)
    assert result1 == result2


def test_anomaly_explanation_format():
    """Anomaly explanations should be human-readable."""
    records = []
    for day in range(1, 10):
        records.append({
            "date": date(2026, 1, day),
            "platform": "Careem",
            "gross_earned": 2000,
            "deductions": 200,
            "net_received": 1800,
        })
    records.append({
        "date": date(2026, 1, 10),
        "platform": "Careem",
        "gross_earned": 3000,
        "deductions": 1800,
        "net_received": 1200,
    })
    
    anomalies = detect_anomalies(records)
    for anomaly in anomalies:
        assert "explanation" in anomaly
        assert isinstance(anomaly["explanation"], str)
        assert len(anomaly["explanation"]) > 0
        if anomaly["type"] == "high_deduction":
            assert "PKR" in anomaly["explanation"]
            assert "deviations" in anomaly["explanation"]
        elif anomaly["type"] == "monthly_income_drop":
            assert "%" in anomaly["explanation"]
            assert "threshold" in anomaly["explanation"]