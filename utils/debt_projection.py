import math
from data_seed import month_sort_key, MONTH_NAMES_RU


def calculate_projections(snapshots: list) -> dict:
    """Calculate debt payoff projections based on monthly payment trends.

    Args:
        snapshots: list of monthly_snapshot dicts, sorted chronologically

    Returns:
        dict mapping debt key to projection info
    """
    if len(snapshots) < 2:
        return {}

    latest = snapshots[-1]

    debt_keys = [
        ("debt_car", "\U0001f697 Кредит машина"),
        ("debt_coffee_machine", "\u2615 Кофемашина"),
        ("debt_drums", "\U0001f941 Барабаны"),
        ("debt_credit_card", "\U0001f4b3 Кредитка"),
    ]

    # Calculate average monthly reduction for each debt
    projections = {}
    for key, label in debt_keys:
        current = latest.get(key, 0) or 0
        if current <= 0:
            continue

        # Collect all monthly changes
        reductions = []
        for i in range(1, len(snapshots)):
            prev_val = snapshots[i - 1].get(key, 0) or 0
            curr_val = snapshots[i].get(key, 0) or 0
            if prev_val > 0:
                reductions.append(prev_val - curr_val)

        if not reductions:
            continue

        avg_reduction = sum(reductions) / len(reductions)

        if avg_reduction <= 0:
            projections[key] = {
                "label": label,
                "current": current,
                "avg_monthly": avg_reduction,
                "months_left": None,
                "payoff_date": None,
            }
            continue

        months_left = math.ceil(current / avg_reduction)

        # Calculate payoff date
        latest_month = latest["month"]
        parts = latest_month.split()
        if len(parts) == 2:
            month_name, year = parts[0], int(parts[1])
            month_num = next((n for n, name in MONTH_NAMES_RU.items() if name == month_name), 1)

            target_month = month_num + months_left
            target_year = year + (target_month - 1) // 12
            target_month = ((target_month - 1) % 12) + 1
            payoff_date = f"{MONTH_NAMES_RU[target_month]} {target_year}"
        else:
            payoff_date = None

        projections[key] = {
            "label": label,
            "current": current,
            "avg_monthly": avg_reduction,
            "months_left": months_left,
            "payoff_date": payoff_date,
        }

    return projections


def format_projections(projections: dict) -> str:
    """Format debt projections as a Telegram message."""
    if not projections:
        return "\u274c Недостаточно данных для прогноза (нужно минимум 2 месяца)"

    lines = ["\U0001f4c8 *Прогноз погашения кредитов*\n"]

    total_months = 0
    for key, p in projections.items():
        lines.append(f"{p['label']}")
        lines.append(f"  Остаток: *\u20bd{p['current']:,.0f}*")

        if p["avg_monthly"] > 0:
            lines.append(f"  Платёж/мес: ~\u20bd{p['avg_monthly']:,.0f}")

        if p["months_left"] and p["payoff_date"]:
            lines.append(f"  \u2705 Погашение: *{p['payoff_date']}* ({p['months_left']} мес.)")
            total_months = max(total_months, p["months_left"])
        else:
            lines.append(f"  \u26a0\ufe0f Долг не уменьшается")

        lines.append("")

    if total_months > 0:
        lines.append(f"\U0001f3c1 Все кредиты закрыты через *{total_months} мес.*")

    return "\n".join(lines)
