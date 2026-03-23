from telegram import Update
from telegram.ext import ContextTypes
from db import get_conn


async def handle_debt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_conn() as conn:
        snaps = conn.execute(
            "SELECT * FROM monthly_snapshots ORDER BY month DESC LIMIT 2"
        ).fetchall()

    if not snaps:
        await update.message.reply_text("\u274c Нет данных по кредитам")
        return

    latest = dict(snaps[0])
    prev = dict(snaps[1]) if len(snaps) > 1 else None

    lines = [f"\U0001f4b3 *Кредиты \u2014 {latest['month']}*\n"]

    debts = [
        ("\U0001f697 Кредит машина", "debt_car"),
        ("\u2615 Кофемашина", "debt_coffee_machine"),
        ("\U0001f941 Барабаны", "debt_drums"),
        ("\U0001f4b3 Кредитка", "debt_credit_card"),
    ]

    for label, key in debts:
        val = latest.get(key, 0) or 0
        if val > 0:
            change = ""
            if prev:
                diff = val - (prev.get(key, 0) or 0)
                if diff < 0:
                    change = f" _(\u2193 \u2212\u20bd{abs(diff):,.0f})_"
                elif diff > 0:
                    change = f" _(\u2191 +\u20bd{abs(diff):,.0f})_"
            lines.append(f"{label}: *\u20bd{val:,.0f}*{change}")

    total = latest.get("total_debt", 0) or 0
    change_total = latest.get("debt_change", 0) or 0
    lines.append(f"\n*Итого: \u20bd{total:,.0f}*")
    if change_total:
        sign = "\u2193 \u2212" if change_total < 0 else "\u2191 +"
        lines.append(f"_{sign}\u20bd{abs(change_total):,.0f} за месяц_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
