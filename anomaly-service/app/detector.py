from collections import defaultdict
from statistics import mean, pstdev


def detect_anomalies(records: list[dict]) -> list[dict]:
    if not records:
        return []

    anomalies: list[dict] = []
    deductions = [float(record["deductions"]) for record in records]
    deduction_mean = mean(deductions)
    deduction_deviation = pstdev(deductions)
    deduction_threshold = deduction_mean + 2 * deduction_deviation

    if deduction_deviation > 0:
        for record in records:
            deduction = float(record["deductions"])
            if deduction > deduction_threshold:
                anomalies.append(
                    {
                        "type": "high_deduction",
                        "date": record["date"].isoformat(),
                        "platform": record["platform"],
                        "value": round(deduction, 2),
                        "threshold": round(deduction_threshold, 2),
                        "explanation": (
                            f"Deductions of PKR {deduction:,.0f} were more than two standard "
                            f"deviations above this worker's average of PKR {deduction_mean:,.0f}."
                        ),
                    }
                )

    monthly_income: dict[str, float] = defaultdict(float)
    for record in records:
        monthly_income[record["date"].strftime("%Y-%m")] += float(record["net_received"])

    ordered_months = sorted(monthly_income)
    for previous_month, current_month in zip(ordered_months, ordered_months[1:]):
        previous_income = monthly_income[previous_month]
        current_income = monthly_income[current_month]
        if previous_income <= 0:
            continue
        drop_percent = (previous_income - current_income) / previous_income * 100
        if drop_percent > 20:
            anomalies.append(
                {
                    "type": "monthly_income_drop",
                    "month": current_month,
                    "previous_month": previous_month,
                    "value": round(current_income, 2),
                    "previous_value": round(previous_income, 2),
                    "drop_percent": round(drop_percent, 1),
                    "explanation": (
                        f"Net income fell {drop_percent:.1f}% from {previous_month} to {current_month}, "
                        "which is above the 20% review threshold."
                    ),
                }
            )

    return anomalies

