import anthropic
import json
from data_seed import get_russian_month

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client

PARSE_SYSTEM = """
You are a financial transaction parser for a Russian-speaking family.
Extract transaction data from the user's message and return ONLY valid JSON.

Return one of these structures:

For a transaction:
{
  "action": "add_transaction",
  "type": "income" | "expense",
  "amount": <number>,
  "category": <category from list>,
  "description": <original text or null>,
  "person": "Артём" | "Партнёр" | "Семья"
}

For a query:
{
  "action": "query",
  "question": <rephrased question in Russian>
}

For unknown/ambiguous:
{
  "action": "unknown"
}

Income categories: Зарплата Артём, Проценты и кешбэк, Другой доход
Expense categories: Продукты, Транспорт, Дом, Здоровье, Лайфстайл, Кредиты, Образование, Еда вне дома, Подарки, Другое

Rules:
- Amount is always positive
- If person not mentioned, use "Семья"
- Map "еда", "супермаркет", "магазин", "пятёрочка", "вкусвилл" → Продукты
- Map "такси", "метро", "бензин", "парковка", "каршеринг" → Транспорт
- Map "аптека", "врач", "клиника", "лекарства" → Здоровье
- Map "ресторан", "кафе", "обед вне дома" → Еда вне дома
- Map "кредит", "платёж по кредиту", "ипотека" → Кредиты
- Map "кино", "спорт", "подписка", "развлечения" → Лайфстайл
"""


def parse_message(text: str) -> dict:
    current_month = get_russian_month()

    response = get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=PARSE_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Current month: {current_month}\nMessage: {text}"
        }]
    )

    try:
        return json.loads(response.content[0].text)
    except (json.JSONDecodeError, IndexError):
        return {"action": "unknown"}


AI_ANSWER_SYSTEM = """
You are a helpful family financial assistant. Answer questions about the family budget in Russian.
Be concise (max 100 words), use real numbers from the data, and use ₽ for currency.
Format nicely for Telegram (use *bold* and line breaks).
"""


def answer_question(question: str, budget_context: str) -> str:
    response = get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=AI_ANSWER_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Budget data:\n{budget_context}\n\nQuestion: {question}"
        }]
    )
    return response.content[0].text
