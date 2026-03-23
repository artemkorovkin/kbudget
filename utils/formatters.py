def format_transaction_confirm(parsed: dict, tx_id: int) -> str:
    EMOJI = {
        "Продукты": "\U0001f6d2", "Транспорт": "\U0001f697", "Дом": "\U0001f3e0",
        "Здоровье": "\u2764\ufe0f", "Лайфстайл": "\u2728", "Кредиты": "\U0001f4b3",
        "Образование": "\U0001f4da", "Еда вне дома": "\U0001f37d", "Подарки": "\U0001f381",
        "Зарплата Артём": "\U0001f4bc", "Проценты и кешбэк": "\U0001f4b0",
        "Другой доход": "\U0001f4b5", "Другое": "\U0001f4e6",
    }

    icon = EMOJI.get(parsed.get("category", ""), "\U0001f4dd")
    type_label = "Доход" if parsed["type"] == "income" else "Расход"
    sign = "+" if parsed["type"] == "income" else "\u2212"

    lines = [
        f"\u2705 *Записано* (#{tx_id})\n",
        f"{icon} *{type_label}*: {sign}\u20bd{parsed['amount']:,.0f}",
        f"\U0001f4c1 Категория: {parsed.get('category', 'Другое')}",
        f"\U0001f464 Кто: {parsed.get('person', 'Семья')}",
    ]

    if parsed.get("description"):
        lines.append(f"\U0001f4dd _{parsed['description']}_")

    return "\n".join(lines)
