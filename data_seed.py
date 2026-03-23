MONTH_NAMES_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

INCOME_CATEGORIES = [
    "Зарплата Артём",
    "Проценты и кешбэк",
    "Другой доход",
]

EXPENSE_CATEGORIES = [
    "Продукты",
    "Транспорт",
    "Дом",
    "Здоровье",
    "Лайфстайл",
    "Кредиты",
    "Образование",
    "Еда вне дома",
    "Подарки",
    "Другое",
]

CATEGORY_EMOJI = {
    "Продукты": "\U0001f6d2",
    "Транспорт": "\U0001f697",
    "Дом": "\U0001f3e0",
    "Здоровье": "\u2764\ufe0f",
    "Лайфстайл": "\u2728",
    "Кредиты": "\U0001f4b3",
    "Образование": "\U0001f4da",
    "Еда вне дома": "\U0001f37d",
    "Подарки": "\U0001f381",
    "Зарплата Артём": "\U0001f4bc",
    "Проценты и кешбэк": "\U0001f4b0",
    "Другой доход": "\U0001f4b5",
    "Другое": "\U0001f4e6",
}

SEED_DATA = [
    {
        "month": "Январь 2026",
        "salary_artem": 0,
        "interest_cashback": 5354,
        "total_income": 5354,
        "expenses_food": 70177,
        "expenses_transport": 28565,
        "expenses_home": 23558,
        "expenses_health": 20231,
        "expenses_lifestyle": 129193,
        "expenses_credits": 158578,
        "expenses_education": 0,
        "expenses_dining": 9471,
        "expenses_gifts": 0,
        "total_expenses": 430302,
        "profit": -424948,
        "debt_car": 2622435,
        "debt_coffee_machine": 43065,
        "debt_drums": 17711,
        "debt_credit_card": 431182,
        "total_debt": 3114393,
        "debt_change": 0,
    },
    {
        "month": "Февраль 2026",
        "salary_artem": 0,
        "interest_cashback": 0,
        "total_income": 0,
        "expenses_food": 72007,
        "expenses_transport": 15417,
        "expenses_home": 6079,
        "expenses_health": 12256,
        "expenses_lifestyle": 32921,
        "expenses_credits": 96338,
        "expenses_education": 48800,
        "expenses_dining": 20429,
        "expenses_gifts": 18574,
        "total_expenses": 322822,
        "profit": -322822,
        "debt_car": 2597881,
        "debt_coffee_machine": 35900,
        "debt_drums": 8994,
        "debt_credit_card": 425398,
        "total_debt": 3068173,
        "debt_change": -46220,
    },
]


def get_russian_month(dt=None):
    """Return Russian month string like 'Март 2026' for the given datetime (or now)."""
    from datetime import datetime
    if dt is None:
        dt = datetime.now()
    return f"{MONTH_NAMES_RU[dt.month]} {dt.year}"
