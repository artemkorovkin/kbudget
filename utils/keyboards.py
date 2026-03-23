from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data_seed import EXPENSE_CATEGORIES, INCOME_CATEGORIES, CATEGORY_EMOJI


def type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select income or expense."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4b8 Расход", callback_data="type:expense"),
            InlineKeyboardButton("\U0001f4b0 Доход", callback_data="type:income"),
        ]
    ])


def category_keyboard(tx_type: str = "expense") -> InlineKeyboardMarkup:
    """Keyboard to select a category based on transaction type."""
    categories = EXPENSE_CATEGORIES if tx_type == "expense" else INCOME_CATEGORIES
    buttons = []
    row = []
    for cat in categories:
        emoji = CATEGORY_EMOJI.get(cat, "\U0001f4e6")
        row.append(InlineKeyboardButton(f"{emoji} {cat}", callback_data=f"cat:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("\u274c Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)
