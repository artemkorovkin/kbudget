from telegram import Update
from telegram.ext import ContextTypes
from db import get_budget_context
from ai_parser import answer_question


async def handle_ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Задайте вопрос: /ask сколько потратили на еду в январе?"
        )
        return

    question = " ".join(args)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    budget_ctx = get_budget_context()
    answer = answer_question(question, budget_ctx)
    await update.message.reply_text(answer, parse_mode="Markdown")
