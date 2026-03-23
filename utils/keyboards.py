from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data_seed import EXPENSE_CATEGORIES, INCOME_CATEGORIES, CATEGORY_EMOJI


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu buttons shown after /start."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Добавить", callback_data="menu:add"),
            InlineKeyboardButton("\U0001f4ca Сводка", callback_data="menu:summary"),
        ],
        [
            InlineKeyboardButton("\U0001f4b3 Кредиты", callback_data="menu:debt"),
            InlineKeyboardButton("\u2753 Задать вопрос", callback_data="menu:ask"),
        ],
        [
            InlineKeyboardButton("\U0001f4c5 Выбрать месяц", callback_data="menu:months"),
            InlineKeyboardButton("\U0001f4ca Дашборд", callback_data="menu:dashboard"),
        ],
    ])


def months_keyboard() -> InlineKeyboardMarkup:
    """Month selection buttons."""
    from data_seed import MONTH_NAMES_RU
    buttons = []
    row = []
    for num, name in MONTH_NAMES_RU.items():
        row.append(InlineKeyboardButton(name, callback_data=f"month:{name} 2026"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("\u25c0 Назад", callback_data="menu:back")])
    return InlineKeyboardMarkup(buttons)


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
