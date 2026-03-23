import logging
import os
from dotenv import load_dotenv
from telegram import Update, CallbackQuery
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from db import init_db, add_transaction, get_budget_context, get_month_summary
from ai_parser import parse_message, answer_question, parse_receipt
from handlers.add import get_add_conversation_handler
from handlers.summary import handle_summary_command, handle_month_command, format_summary
from handlers.ask import handle_ask_command
from handlers.debt import handle_debt_command
from utils.formatters import format_transaction_confirm
from utils.keyboards import main_menu_keyboard, months_keyboard

load_dotenv()
logging.basicConfig(level=logging.INFO)

ALLOWED_IDS = [int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x]


async def auth_check(update: Update) -> bool:
    user = update.effective_user
    if ALLOWED_IDS and user.id not in ALLOWED_IDS:
        if update.message:
            await update.message.reply_text("\u26d4 Доступ запрещён.")
        elif update.callback_query:
            await update.callback_query.answer("\u26d4 Доступ запрещён.", show_alert=True)
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update):
        return
    await update.message.reply_text(
        "\U0001f44b *Семейный бюджет*\n\n"
        "Просто напишите что потратили или получили:\n"
        "\u2022 _\u00abпотратил 3500 на продукты\u00bb_\n"
        "\u2022 _\u00abпришло 5000 кешбэк\u00bb_\n"
        "\u2022 _\u00abсколько ушло на еду в январе?\u00bb_\n"
        "\U0001f4f7 Или отправьте *фото чека*!\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update):
        return
    query: CallbackQuery = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]

    if action == "add":
        await query.message.reply_text(
            "Выберите тип записи:",
            reply_markup=__import__("utils.keyboards", fromlist=["type_keyboard"]).type_keyboard(),
        )

    elif action == "summary":
        from data_seed import get_russian_month
        month = get_russian_month()
        data = get_month_summary(month)
        await query.message.reply_text(
            format_summary(month, data),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    elif action == "debt":
        from db import get_conn
        from data_seed import month_sort_key
        with get_conn() as conn:
            snaps = conn.execute("SELECT * FROM monthly_snapshots").fetchall()
        snaps = sorted([dict(s) for s in snaps], key=lambda s: month_sort_key(s["month"]), reverse=True)
        if not snaps:
            await query.message.reply_text("\u274c Нет данных по кредитам")
            return
        latest = snaps[0]
        prev = snaps[1] if len(snaps) > 1 else None
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
        await query.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    elif action == "projection":
        from db import get_conn
        from data_seed import month_sort_key
        from utils.debt_projection import calculate_projections, format_projections
        with get_conn() as conn:
            snaps = conn.execute("SELECT * FROM monthly_snapshots").fetchall()
        snaps = sorted([dict(s) for s in snaps], key=lambda s: month_sort_key(s["month"]))
        projections = calculate_projections(snaps)
        text = format_projections(projections)
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif action == "ask":
        context.user_data["awaiting_question"] = True
        await query.message.reply_text("Задайте вопрос о бюджете:")

    elif action == "months":
        await query.message.reply_text(
            "\U0001f4c5 Выберите месяц:",
            reply_markup=months_keyboard(),
        )

    elif action == "dashboard":
        base = os.getenv("DASHBOARD_URL", "http://localhost:8080")
        token = os.getenv("DASHBOARD_TOKEN", "")
        url = f"{base}?token={token}" if token else base
        await query.message.reply_text(
            f"\U0001f4ca [Открыть дашборд]({url})",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    elif action == "back":
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )


async def handle_month_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update):
        return
    query: CallbackQuery = update.callback_query
    await query.answer()
    month = query.data.split(":", 1)[1]
    data = get_month_summary(month)
    await query.message.reply_text(
        format_summary(month, data),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt photos."""
    if not await auth_check(update):
        return

    await update.message.chat.send_action("typing")

    # Get the largest photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    parsed = parse_receipt(bytes(image_bytes), "image/jpeg")

    if parsed.get("action") != "receipt" or not parsed.get("items"):
        await update.message.reply_text(
            "Не удалось распознать чек \U0001f914\nПопробуйте сфотографировать ближе и чётче.",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Save each item as a transaction
    total = parsed.get("total", 0)
    store = parsed.get("store", "")
    items = parsed["items"]

    # If only one category across all items, save as single transaction
    categories = set(item.get("category", "Другое") for item in items)
    if len(categories) == 1:
        single_parsed = {
            "type": "expense",
            "category": items[0].get("category", "Другое"),
            "amount": total or sum(item["amount"] for item in items),
            "description": store or "Чек",
            "person": "Семья",
        }
        tx_id = add_transaction(single_parsed)
        reply = format_transaction_confirm(single_parsed, tx_id)
        await update.message.reply_text(reply, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        # Multiple categories — save each item separately
        tx_ids = []
        for item in items:
            tx_parsed = {
                "type": "expense",
                "category": item.get("category", "Другое"),
                "amount": item["amount"],
                "description": item.get("description", ""),
                "person": "Семья",
            }
            tx_ids.append(add_transaction(tx_parsed))

        lines = [f"\U0001f9fe *Чек распознан* ({store or 'магазин'})\n"]
        for item, tx_id in zip(items, tx_ids):
            lines.append(f"  \u2022 {item.get('description', '?')} — \u20bd{item['amount']:,.0f} _{item.get('category', '')}_")
        lines.append(f"\n*Итого: \u20bd{total:,.0f}* ({len(items)} позиций)")
        lines.append(f"_Записано #{tx_ids[0]}–#{tx_ids[-1]}_")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )


async def handle_projection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /projection command — debt payoff forecast."""
    if not await auth_check(update):
        return
    from db import get_conn
    from data_seed import month_sort_key
    from utils.debt_projection import calculate_projections, format_projections

    with get_conn() as conn:
        snaps = conn.execute("SELECT * FROM monthly_snapshots").fetchall()
    snaps = sorted([dict(s) for s in snaps], key=lambda s: month_sort_key(s["month"]))

    projections = calculate_projections(snaps)
    text = format_projections(projections)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update):
        return
    text = update.message.text

    # Handle awaiting question from menu
    if context.user_data.get("awaiting_question"):
        context.user_data["awaiting_question"] = False
        await update.message.chat.send_action("typing")
        ctx = get_budget_context()
        answer = answer_question(text, ctx)
        await update.message.reply_text(
            answer,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.chat.send_action("typing")

    parsed = parse_message(text)

    if parsed["action"] == "add_transaction":
        tx_id = add_transaction(parsed)
        reply = format_transaction_confirm(parsed, tx_id)
        await update.message.reply_text(
            reply,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    elif parsed["action"] == "query":
        ctx = get_budget_context()
        answer = answer_question(parsed["question"], ctx)
        await update.message.reply_text(
            answer,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    else:
        await update.message.reply_text(
            "Не понял \U0001f914 Попробуйте:\n"
            "\u2022 _\u00abпотратил 1500 на такси\u00bb_\n"
            "\u2022 _\u00abзарплата 80000\u00bb_\n",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )


def main():
    init_db()
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # /add conversation handler (must be added before generic handlers)
    app.add_handler(get_add_conversation_handler())

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summary", handle_summary_command))
    app.add_handler(CommandHandler("month", handle_month_command))
    app.add_handler(CommandHandler("debt", handle_debt_command))
    app.add_handler(CommandHandler("projection", handle_projection_command))
    app.add_handler(CommandHandler("ask", handle_ask_command))
    def _dashboard_url():
        base = os.getenv("DASHBOARD_URL", "http://localhost:8080")
        token = os.getenv("DASHBOARD_TOKEN", "")
        return f"{base}?token={token}" if token else base

    app.add_handler(CommandHandler("dashboard", lambda u, c: u.message.reply_text(
        f"\U0001f4ca [Открыть дашборд]({_dashboard_url()})",
        parse_mode="Markdown",
    )))

    # Menu button callbacks
    app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(handle_month_callback, pattern=r"^month:"))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
