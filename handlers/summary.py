from telegram import Update
from telegram.ext import ContextTypes
from db import get_month_summary
from data_seed import get_russian_month, MONTH_NAMES_RU

# Build reverse lookup: lowercase Russian month name -> full "Месяц YYYY" string
MONTHS_RU = {}
for num, name in MONTH_NAMES_RU.items():
    MONTHS_RU[name.lower()] = f"{name} 2026"


def format_summary(month: str, data: dict) -> str:
    snap = data.get("snapshot", {})
    txs = data.get("transactions", [])

    if not snap and not txs:
        return f"\u274c Нет данных за {month}"

    manual_income = sum(t["amount"] for t in txs if t["type"] == "income")
    manual_expense = sum(t["amount"] for t in txs if t["type"] == "expense")

    total_income = (snap.get("total_income", 0) or 0) + manual_income
    total_expenses = (snap.get("total_expenses", 0) or 0) + manual_expense
    profit = total_income - total_expenses

    emoji = "\U0001f4c8" if profit >= 0 else "\U0001f4c9"
    sign = "+" if profit >= 0 else ""

    lines = [
        f"\U0001f4ca *{month}*\n",
        f"\U0001f4b0 Доходы: *\u20bd{total_income:,.0f}*",
        f"\U0001f4b8 Расходы: *\u20bd{total_expenses:,.0f}*",
        f"{emoji} Результат: *{sign}\u20bd{profit:,.0f}*",
    ]

    if snap:
        lines.append("\n*Расходы по категориям:*")
        cats = [
            ("\U0001f6d2 Продукты", "expenses_food"),
            ("\U0001f697 Транспорт", "expenses_transport"),
            ("\U0001f3e0 Дом", "expenses_home"),
            ("\u2764\ufe0f Здоровье", "expenses_health"),
            ("\u2728 Лайфстайл", "expenses_lifestyle"),
            ("\U0001f4b3 Кредиты", "expenses_credits"),
            ("\U0001f4da Образование", "expenses_education"),
            ("\U0001f37d Еда вне дома", "expenses_dining"),
            ("\U0001f381 Подарки", "expenses_gifts"),
        ]
        for label, key in cats:
            val = snap.get(key, 0) or 0
            if val > 0:
                lines.append(f"  {label}: \u20bd{val:,.0f}")

    if txs:
        lines.append(f"\n_+{len(txs)} ручных записей_")

    return "\n".join(lines)


async def handle_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    month = get_russian_month()
    data = get_month_summary(month)
    await update.message.reply_text(format_summary(month, data), parse_mode="Markdown")


async def handle_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Укажите месяц: /month Январь")
        return
    month_key = args[0].lower()
    month = MONTHS_RU.get(month_key, f"{args[0]} 2026")
    data = get_month_summary(month)
    await update.message.reply_text(format_summary(month, data), parse_mode="Markdown")
