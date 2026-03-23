import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from db import init_db, add_transaction, get_budget_context
from ai_parser import parse_message, answer_question
from handlers.add import get_add_conversation_handler
from handlers.summary import handle_summary_command, handle_month_command
from handlers.ask import handle_ask_command
from handlers.debt import handle_debt_command
from utils.formatters import format_transaction_confirm

load_dotenv()
logging.basicConfig(level=logging.INFO)

ALLOWED_IDS = [int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x]


async def auth_check(update: Update) -> bool:
    if ALLOWED_IDS and update.effective_user.id not in ALLOWED_IDS:
        await update.message.reply_text("\u26d4 Доступ запрещён.")
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
        "\u2022 _\u00abсколько ушло на еду в январе?\u00bb_\n\n"
        "Или используйте команды:\n"
        "/add \u2014 добавить запись\n"
        "/summary \u2014 текущий месяц\n"
        "/month \u2014 конкретный месяц\n"
        "/debt \u2014 кредиты\n"
        "/ask \u2014 задать вопрос\n"
        "/dashboard \u2014 веб-дашборд",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update):
        return
    text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    parsed = parse_message(text)

    if parsed["action"] == "add_transaction":
        tx_id = add_transaction(parsed)
        reply = format_transaction_confirm(parsed, tx_id)
        await update.message.reply_text(reply, parse_mode="Markdown")

    elif parsed["action"] == "query":
        ctx = get_budget_context()
        answer = answer_question(parsed["question"], ctx)
        await update.message.reply_text(answer, parse_mode="Markdown")

    else:
        await update.message.reply_text(
            "Не понял \U0001f914 Попробуйте:\n"
            "\u2022 _\u00abпотратил 1500 на такси\u00bb_\n"
            "\u2022 _\u00abзарплата 80000\u00bb_\n"
            "\u2022 Или /help для списка команд",
            parse_mode="Markdown",
        )


def main():
    init_db()
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # /add conversation handler (must be added before generic message handler)
    app.add_handler(get_add_conversation_handler())

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summary", handle_summary_command))
    app.add_handler(CommandHandler("month", handle_month_command))
    app.add_handler(CommandHandler("debt", handle_debt_command))
    app.add_handler(CommandHandler("ask", handle_ask_command))
    app.add_handler(CommandHandler("dashboard", lambda u, c: u.message.reply_text(
        f"\U0001f4ca Дашборд: {os.getenv('DASHBOARD_URL', 'http://localhost:8080')}"
    )))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
