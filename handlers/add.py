from telegram import Update, CallbackQuery
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)
from db import add_transaction
from utils.keyboards import type_keyboard, category_keyboard
from utils.formatters import format_transaction_confirm

SELECT_TYPE, SELECT_CATEGORY, ENTER_AMOUNT = range(3)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the /add interactive flow."""
    await update.message.reply_text(
        "Выберите тип записи:",
        reply_markup=type_keyboard(),
    )
    return SELECT_TYPE


async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle type selection callback."""
    query: CallbackQuery = update.callback_query
    await query.answer()

    data = query.data  # "type:expense" or "type:income"
    tx_type = data.split(":")[1]
    context.user_data["tx_type"] = tx_type

    label = "расхода" if tx_type == "expense" else "дохода"
    await query.edit_message_text(
        f"Выберите категорию {label}:",
        reply_markup=category_keyboard(tx_type),
    )
    return SELECT_CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection callback."""
    query: CallbackQuery = update.callback_query
    await query.answer()

    data = query.data  # "cat:Продукты"
    category = data.split(":", 1)[1]
    context.user_data["category"] = category

    await query.edit_message_text(f"Категория: *{category}*\n\nВведите сумму:", parse_mode="Markdown")
    return ENTER_AMOUNT


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount text input."""
    text = update.message.text.strip().replace(" ", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введите положительное число:")
        return ENTER_AMOUNT

    parsed = {
        "type": context.user_data["tx_type"],
        "category": context.user_data["category"],
        "amount": amount,
        "person": "Семья",
    }

    tx_id = add_transaction(parsed)
    reply = format_transaction_confirm(parsed, tx_id)
    await update.message.reply_text(reply, parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel callback."""
    query: CallbackQuery = update.callback_query
    await query.answer()
    await query.edit_message_text("Отменено.")
    context.user_data.clear()
    return ConversationHandler.END


def get_add_conversation_handler() -> ConversationHandler:
    """Build and return the /add ConversationHandler."""
    return ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(select_type, pattern=r"^type:"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            SELECT_CATEGORY: [
                CallbackQueryHandler(select_category, pattern=r"^cat:"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
            ],
            ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount),
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: cancel(u, c))],
    )
