# Family Budget — Telegram Bot + Web Dashboard

## Project Overview

A personal family finance system with two surfaces:
1. **Telegram bot** — natural language interface for logging income/expenses and quick queries
2. **Web dashboard** — full visual dashboard with charts, budget tracking, debt overview

The bot uses Claude AI to parse free-text messages and store structured data. The dashboard reads from the same data source and renders charts + summaries.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Bot runtime | Python 3.11+ | Best Telegram library ecosystem |
| Telegram library | `python-telegram-bot` v21 | Async, well maintained |
| AI parsing | Anthropic Claude API (`claude-haiku-4-5`) | Fast + cheap for parsing |
| Database | SQLite (local) or Supabase (cloud) | SQLite for local dev, Supabase for prod |
| Dashboard | Single HTML file (vanilla JS + Chart.js) | Zero dependencies, works on any device |
| Dashboard server | Python `http.server` or Flask | Serve the HTML + a `/api/data` endpoint |
| Hosting | Railway / Render / VPS | Free tier works fine |

---

## Data Model

### Transactions table

```sql
CREATE TABLE transactions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  month       TEXT NOT NULL,          -- "Январь 2026"
  year        INTEGER NOT NULL,       -- 2026
  type        TEXT NOT NULL,          -- "income" | "expense"
  category    TEXT NOT NULL,          -- see categories below
  amount      REAL NOT NULL,          -- always positive
  description TEXT,                   -- free text note
  person      TEXT DEFAULT 'Семья',   -- "Артём" | "Партнёр" | "Семья"
  source      TEXT DEFAULT 'bot'      -- "bot" | "manual" | "import"
);
```

### Monthly snapshots table (from spreadsheet imports)

```sql
CREATE TABLE monthly_snapshots (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  month           TEXT NOT NULL,       -- "Январь 2026"
  salary_artem    REAL DEFAULT 0,
  interest_cashback REAL DEFAULT 0,
  total_income    REAL DEFAULT 0,
  expenses_food       REAL DEFAULT 0,
  expenses_transport  REAL DEFAULT 0,
  expenses_home       REAL DEFAULT 0,
  expenses_health     REAL DEFAULT 0,
  expenses_lifestyle  REAL DEFAULT 0,
  expenses_credits    REAL DEFAULT 0,
  expenses_education  REAL DEFAULT 0,
  expenses_dining     REAL DEFAULT 0,
  expenses_gifts      REAL DEFAULT 0,
  total_expenses  REAL DEFAULT 0,
  profit          REAL DEFAULT 0,
  debt_car        REAL DEFAULT 0,
  debt_coffee_machine REAL DEFAULT 0,
  debt_drums      REAL DEFAULT 0,
  debt_credit_card REAL DEFAULT 0,
  total_debt      REAL DEFAULT 0,
  debt_change     REAL DEFAULT 0,
  UNIQUE(month)
);
```

### Seed data (from uploaded spreadsheet)

```python
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
```

---

## Categories

```python
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
    "Продукты": "🛒",
    "Транспорт": "🚗",
    "Дом": "🏠",
    "Здоровье": "❤️",
    "Лайфстайл": "✨",
    "Кредиты": "💳",
    "Образование": "📚",
    "Еда вне дома": "🍽",
    "Подарки": "🎁",
    "Зарплата Артём": "💼",
    "Проценты и кешбэк": "💰",
    "Другой доход": "💵",
    "Другое": "📦",
}
```

---

## Project Structure

```
family-budget/
├── CLAUDE.md              # This file
├── .env                   # Secrets (never commit)
├── .env.example           # Template
├── requirements.txt
├── bot.py                 # Main bot entry point
├── db.py                  # Database layer
├── ai_parser.py           # Claude API — parse user messages
├── handlers/
│   ├── __init__.py
│   ├── add.py             # /add command + natural language
│   ├── summary.py         # /summary, /month commands
│   ├── ask.py             # /ask — AI question answering
│   └── debt.py            # /debt — credit overview
├── dashboard/
│   ├── server.py          # Flask server for dashboard + API
│   └── index.html         # Single-page dashboard
└── utils/
    ├── formatters.py      # Currency formatters
    └── keyboards.py       # Telegram inline keyboards
```

---

## Environment Variables

```bash
# .env.example
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=sqlite:///budget.db      # or postgres://... for Supabase
DASHBOARD_PORT=8080
DASHBOARD_SECRET=your_random_secret   # optional basic auth
ALLOWED_CHAT_IDS=123456789,987654321  # comma-separated Telegram user IDs
```

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message + command list |
| `/add` | Interactive add flow with inline buttons |
| `/summary` | Current month summary |
| `/month [Январь]` | Summary for specific month |
| `/debt` | Current debt balances |
| `/ask [question]` | Ask AI anything about budget |
| `/dashboard` | Get link to web dashboard |
| `/help` | Command reference |

### Natural language — no commands needed

Users can just type naturally. Examples the bot must handle:

```
"потратил 3500 на продукты"             → expense, Продукты, 3500
"купил лекарства за 1200"               → expense, Здоровье, 1200
"пришло 5000 кешбэк"                    → income, Проценты и кешбэк, 5000
"заплатил за бензин 4800"               → expense, Транспорт, 4800
"ужин в ресторане 8000"                 → expense, Еда вне дома, 8000
"зарплата 50000"                        → income, Зарплата Артём, 50000
"сколько потратили в январе?"           → /summary Январь
"самая большая трата этого месяца?"     → AI query
"на сколько уменьшился долг?"           → AI query about debt
```

---

## AI Parser — `ai_parser.py`

```python
import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

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
    current_month = datetime.now().strftime("%B %Y")  # Russian month
    
    response = client.messages.create(
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
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=AI_ANSWER_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Budget data:\n{budget_context}\n\nQuestion: {question}"
        }]
    )
    return response.content[0].text
```

---

## Bot Main — `bot.py`

```python
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from db import init_db, get_budget_context
from ai_parser import parse_message, answer_question
from handlers.add import handle_add_command
from handlers.summary import handle_summary_command, handle_month_command
from handlers.debt import handle_debt_command
from utils.formatters import format_transaction_confirm
from utils.keyboards import category_keyboard

load_dotenv()
logging.basicConfig(level=logging.INFO)

ALLOWED_IDS = [int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x]

async def auth_check(update: Update) -> bool:
    if ALLOWED_IDS and update.effective_user.id not in ALLOWED_IDS:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.message.reply_text(
        "👋 *Семейный бюджет*\n\n"
        "Просто напишите что потратили или получили:\n"
        "• _«потратил 3500 на продукты»_\n"
        "• _«пришло 5000 кешбэк»_\n"
        "• _«сколько ушло на еду в январе?»_\n\n"
        "Или используйте команды:\n"
        "/summary — текущий месяц\n"
        "/debt — кредиты\n"
        "/ask — задать вопрос\n"
        "/dashboard — веб-дашборд",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    text = update.message.text
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    parsed = parse_message(text)
    
    if parsed["action"] == "add_transaction":
        # Store and confirm
        from db import add_transaction
        tx_id = add_transaction(parsed)
        reply = format_transaction_confirm(parsed, tx_id)
        await update.message.reply_text(reply, parse_mode="Markdown")
    
    elif parsed["action"] == "query":
        ctx = get_budget_context()
        answer = answer_question(parsed["question"], ctx)
        await update.message.reply_text(answer, parse_mode="Markdown")
    
    else:
        await update.message.reply_text(
            "Не понял 🤔 Попробуйте:\n"
            "• _«потратил 1500 на такси»_\n"
            "• _«зарплата 80000»_\n"
            "• Или /help для списка команд",
            parse_mode="Markdown"
        )

def main():
    init_db()
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("summary", handle_summary_command))
    app.add_handler(CommandHandler("month", handle_month_command))
    app.add_handler(CommandHandler("debt", handle_debt_command))
    app.add_handler(CommandHandler("dashboard", lambda u, c: u.message.reply_text(
        f"📊 Дашборд: {os.getenv('DASHBOARD_URL', 'http://localhost:8080')}"
    )))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
```

---

## Database Layer — `db.py`

```python
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "budget.db")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                month       TEXT NOT NULL,
                year        INTEGER NOT NULL,
                type        TEXT NOT NULL,
                category    TEXT NOT NULL,
                amount      REAL NOT NULL,
                description TEXT,
                person      TEXT DEFAULT 'Семья',
                source      TEXT DEFAULT 'bot'
            );
            CREATE TABLE IF NOT EXISTS monthly_snapshots (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                month               TEXT NOT NULL UNIQUE,
                salary_artem        REAL DEFAULT 0,
                interest_cashback   REAL DEFAULT 0,
                total_income        REAL DEFAULT 0,
                expenses_food       REAL DEFAULT 0,
                expenses_transport  REAL DEFAULT 0,
                expenses_home       REAL DEFAULT 0,
                expenses_health     REAL DEFAULT 0,
                expenses_lifestyle  REAL DEFAULT 0,
                expenses_credits    REAL DEFAULT 0,
                expenses_education  REAL DEFAULT 0,
                expenses_dining     REAL DEFAULT 0,
                expenses_gifts      REAL DEFAULT 0,
                total_expenses      REAL DEFAULT 0,
                profit              REAL DEFAULT 0,
                debt_car            REAL DEFAULT 0,
                debt_coffee_machine REAL DEFAULT 0,
                debt_drums          REAL DEFAULT 0,
                debt_credit_card    REAL DEFAULT 0,
                total_debt          REAL DEFAULT 0,
                debt_change         REAL DEFAULT 0
            );
        """)
        _seed_data(conn)

def _seed_data(conn):
    """Insert spreadsheet data if not already present."""
    from data_seed import SEED_DATA
    for row in SEED_DATA:
        conn.execute("""
            INSERT OR IGNORE INTO monthly_snapshots (month, salary_artem, interest_cashback,
            total_income, expenses_food, expenses_transport, expenses_home, expenses_health,
            expenses_lifestyle, expenses_credits, expenses_education, expenses_dining,
            expenses_gifts, total_expenses, profit, debt_car, debt_coffee_machine,
            debt_drums, debt_credit_card, total_debt, debt_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["month"], row["salary_artem"], row["interest_cashback"],
            row["total_income"], row["expenses_food"], row["expenses_transport"],
            row["expenses_home"], row["expenses_health"], row["expenses_lifestyle"],
            row["expenses_credits"], row["expenses_education"], row["expenses_dining"],
            row["expenses_gifts"], row["total_expenses"], row["profit"],
            row["debt_car"], row["debt_coffee_machine"], row["debt_drums"],
            row["debt_credit_card"], row["total_debt"], row["debt_change"]
        ))

def add_transaction(parsed: dict) -> int:
    now = datetime.now()
    month_str = now.strftime("%B %Y")  # localise to Russian if needed
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO transactions (month, year, type, category, amount, description, person)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            month_str, now.year,
            parsed["type"], parsed["category"], parsed["amount"],
            parsed.get("description"), parsed.get("person", "Семья")
        ))
        return cursor.lastrowid

def get_month_summary(month: str) -> dict:
    with get_conn() as conn:
        snap = conn.execute(
            "SELECT * FROM monthly_snapshots WHERE month = ?", (month,)
        ).fetchone()
        
        txs = conn.execute(
            "SELECT * FROM transactions WHERE month = ? ORDER BY created_at DESC",
            (month,)
        ).fetchall()
        
        return {"snapshot": dict(snap) if snap else {}, "transactions": [dict(t) for t in txs]}

def get_budget_context() -> str:
    """Build a text context for AI queries."""
    with get_conn() as conn:
        snaps = conn.execute(
            "SELECT * FROM monthly_snapshots ORDER BY month"
        ).fetchall()
        txs = conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    
    lines = ["=== Monthly Snapshots ==="]
    for s in snaps:
        s = dict(s)
        lines.append(
            f"{s['month']}: income ₽{s['total_income']:,.0f}, "
            f"expenses ₽{s['total_expenses']:,.0f}, "
            f"profit ₽{s['profit']:,.0f}, "
            f"total debt ₽{s['total_debt']:,.0f}"
        )
    
    if txs:
        lines.append("\n=== Recent Manual Transactions ===")
        for t in txs:
            t = dict(t)
            lines.append(
                f"{t['month']} | {t['type']} | {t['category']} | "
                f"₽{t['amount']:,.0f} | {t['description'] or ''}"
            )
    
    return "\n".join(lines)
```

---

## Summary Handler — `handlers/summary.py`

```python
from telegram import Update
from telegram.ext import ContextTypes
from db import get_month_summary
from datetime import datetime

MONTHS_RU = {
    "январь": "Январь 2026", "февраль": "Февраль 2026",
    "март": "Март 2026", "апрель": "Апрель 2026",
}

def format_summary(month: str, data: dict) -> str:
    snap = data.get("snapshot", {})
    txs = data.get("transactions", [])
    
    if not snap and not txs:
        return f"❌ Нет данных за {month}"
    
    # Add manual transaction totals on top of snapshot
    manual_income = sum(t["amount"] for t in txs if t["type"] == "income")
    manual_expense = sum(t["amount"] for t in txs if t["type"] == "expense")
    
    total_income = (snap.get("total_income", 0) or 0) + manual_income
    total_expenses = (snap.get("total_expenses", 0) or 0) + manual_expense
    profit = total_income - total_expenses
    
    emoji = "📈" if profit >= 0 else "📉"
    sign = "+" if profit >= 0 else ""
    
    lines = [
        f"📊 *{month}*\n",
        f"💰 Доходы: *₽{total_income:,.0f}*",
        f"💸 Расходы: *₽{total_expenses:,.0f}*",
        f"{emoji} Результат: *{sign}₽{profit:,.0f}*",
    ]
    
    if snap:
        lines.append("\n*Расходы по категориям:*")
        cats = [
            ("🛒 Продукты", "expenses_food"),
            ("🚗 Транспорт", "expenses_transport"),
            ("🏠 Дом", "expenses_home"),
            ("❤️ Здоровье", "expenses_health"),
            ("✨ Лайфстайл", "expenses_lifestyle"),
            ("💳 Кредиты", "expenses_credits"),
            ("📚 Образование", "expenses_education"),
            ("🍽 Еда вне дома", "expenses_dining"),
            ("🎁 Подарки", "expenses_gifts"),
        ]
        for label, key in cats:
            val = snap.get(key, 0) or 0
            if val > 0:
                lines.append(f"  {label}: ₽{val:,.0f}")
    
    if txs:
        lines.append(f"\n_+{len(txs)} ручных записей_")
    
    return "\n".join(lines)

async def handle_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    month = datetime.now().strftime("%B %Y")
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
```

---

## Debt Handler — `handlers/debt.py`

```python
from telegram import Update
from telegram.ext import ContextTypes
from db import get_conn

async def handle_debt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_conn() as conn:
        snaps = conn.execute(
            "SELECT * FROM monthly_snapshots ORDER BY month DESC LIMIT 2"
        ).fetchall()
    
    if not snaps:
        await update.message.reply_text("❌ Нет данных по кредитам")
        return
    
    latest = dict(snaps[0])
    prev = dict(snaps[1]) if len(snaps) > 1 else None
    
    lines = [f"💳 *Кредиты — {latest['month']}*\n"]
    
    debts = [
        ("🚗 Кредит машина", "debt_car"),
        ("☕ Кофемашина", "debt_coffee_machine"),
        ("🥁 Барабаны", "debt_drums"),
        ("💳 Кредитка", "debt_credit_card"),
    ]
    
    for label, key in debts:
        val = latest.get(key, 0) or 0
        if val > 0:
            change = ""
            if prev:
                diff = val - (prev.get(key, 0) or 0)
                if diff < 0:
                    change = f" _(↓ −₽{abs(diff):,.0f})_"
                elif diff > 0:
                    change = f" _(↑ +₽{abs(diff):,.0f})_"
            lines.append(f"{label}: *₽{val:,.0f}*{change}")
    
    total = latest.get("total_debt", 0) or 0
    change_total = latest.get("debt_change", 0) or 0
    lines.append(f"\n*Итого: ₽{total:,.0f}*")
    if change_total:
        sign = "↓ −" if change_total < 0 else "↑ +"
        lines.append(f"_{sign}₽{abs(change_total):,.0f} за месяц_")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
```

---

## Formatters — `utils/formatters.py`

```python
def format_transaction_confirm(parsed: dict, tx_id: int) -> str:
    EMOJI = {
        "Продукты": "🛒", "Транспорт": "🚗", "Дом": "🏠",
        "Здоровье": "❤️", "Лайфстайл": "✨", "Кредиты": "💳",
        "Образование": "📚", "Еда вне дома": "🍽", "Подарки": "🎁",
        "Зарплата Артём": "💼", "Проценты и кешбэк": "💰",
        "Другой доход": "💵", "Другое": "📦",
    }
    
    icon = EMOJI.get(parsed.get("category", ""), "📝")
    type_label = "Доход" if parsed["type"] == "income" else "Расход"
    sign = "+" if parsed["type"] == "income" else "−"
    
    lines = [
        f"✅ *Записано* (#{tx_id})\n",
        f"{icon} *{type_label}*: {sign}₽{parsed['amount']:,.0f}",
        f"📁 Категория: {parsed.get('category', 'Другое')}",
        f"👤 Кто: {parsed.get('person', 'Семья')}",
    ]
    
    if parsed.get("description"):
        lines.append(f"📝 _{parsed['description']}_")
    
    return "\n".join(lines)
```

---

## Dashboard API — `dashboard/server.py`

```python
from flask import Flask, jsonify, send_from_directory
import sqlite3, os

app = Flask(__name__, static_folder=".")
DB_PATH = os.getenv("DATABASE_PATH", "budget.db")

def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/data")
def get_data():
    snapshots = query_db("SELECT * FROM monthly_snapshots ORDER BY month")
    transactions = query_db(
        "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 200"
    )
    return jsonify({"snapshots": snapshots, "transactions": transactions})

@app.route("/api/summary/<month>")
def get_month(month):
    snap = query_db("SELECT * FROM monthly_snapshots WHERE month = ?", (month,))
    txs = query_db("SELECT * FROM transactions WHERE month = ? ORDER BY created_at DESC", (month,))
    return jsonify({"snapshot": snap[0] if snap else {}, "transactions": txs})

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    app.run(host="0.0.0.0", port=port)
```

---

## Dashboard — `dashboard/index.html`

The dashboard is the HTML file already built in this project (`family-finance-tracker.html`), modified to fetch data from `/api/data` instead of using hardcoded values.

Key change — replace the hardcoded `DATA` object with:

```javascript
async function loadData() {
  const res = await fetch('/api/data');
  const { snapshots, transactions } = await res.json();
  
  // Transform snapshots array into keyed object
  window.DATA = {};
  for (const snap of snapshots) {
    window.DATA[snap.month] = {
      totalIncome: snap.total_income,
      totalExpenses: snap.total_expenses,
      profit: snap.profit,
      expenses: {
        'Продукты': snap.expenses_food,
        'Транспорт': snap.expenses_transport,
        'Дом': snap.expenses_home,
        'Здоровье': snap.expenses_health,
        'Лайфстайл': snap.expenses_lifestyle,
        'Кредиты': snap.expenses_credits,
        'Образование': snap.expenses_education,
        'Еда вне дома': snap.expenses_dining,
        'Подарки': snap.expenses_gifts,
      },
      debts: {
        'Кредит машина': snap.debt_car,
        'Кредит кофемашина': snap.debt_coffee_machine,
        'Кредит барабаны': snap.debt_drums,
        'Кредитка': snap.debt_credit_card,
      },
      totalDebt: snap.total_debt,
      debtChange: snap.debt_change,
    };
  }
  
  window.TRANSACTIONS = transactions;
  renderDash();
  renderTabs();
}

loadData();
```

---

## `requirements.txt`

```
python-telegram-bot==21.6
anthropic>=0.34.0
flask>=3.0.0
python-dotenv>=1.0.0
```

---

## Setup Instructions

### 1. Create Telegram bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. `/newbot` → give it a name and username
3. Copy the token → paste into `.env` as `TELEGRAM_BOT_TOKEN`

### 2. Get your Telegram user ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your numeric ID → paste into `.env` as `ALLOWED_CHAT_IDS`

### 3. Install and run locally

```bash
git clone <your-repo>
cd family-budget
cp .env.example .env
# Fill in .env values

pip install -r requirements.txt
python bot.py
```

In a second terminal:
```bash
python dashboard/server.py
# Open http://localhost:8080
```

### 4. Deploy to Railway (free tier)

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

Add environment variables in Railway dashboard. Set start command:
```
python bot.py & python dashboard/server.py
```

Or use a `Procfile`:
```
web: python dashboard/server.py
worker: python bot.py
```

---

## Deployment Checklist

- [ ] `TELEGRAM_BOT_TOKEN` set
- [ ] `ANTHROPIC_API_KEY` set
- [ ] `ALLOWED_CHAT_IDS` set (your Telegram user ID)
- [ ] `DASHBOARD_URL` set to your public URL
- [ ] Database initialized with seed data
- [ ] Bot responds to `/start`
- [ ] Natural language parsing works
- [ ] Dashboard accessible at public URL
- [ ] Dashboard loads data from `/api/data`

---

## Example Bot Conversation

```
You: потратил 4500 на продукты в пятёрочке

Bot: ✅ Записано (#42)
     🛒 Расход: −₽4,500
     📁 Категория: Продукты
     👤 Кто: Семья
     📝 потратил 4500 на продукты в пятёрочке

You: сколько потратили на еду в феврале?

Bot: В феврале 2026 на продукты ушло ₽72,007
     Это самая крупная статья после кредитов.
     +₽4,500 добавлено вручную в марте.

You: /debt

Bot: 💳 Кредиты — Февраль 2026
     🚗 Кредит машина: ₽2,597,881 (↓ −₽24,554)
     ☕ Кофемашина: ₽35,900 (↓ −₽7,165)
     🥁 Барабаны: ₽8,994 (↓ −₽8,717)
     💳 Кредитка: ₽425,398 (↓ −₽5,784)
     
     Итого: ₽3,068,173
     ↓ −₽46,220 за месяц
```

---

## Notes for Claude

- All amounts in Russian Rubles (₽)
- Months stored as "Январь 2026", "Февраль 2026" etc.
- The seed data from the spreadsheet should always be present — never delete it
- New transactions added by the bot are additive on top of snapshots
- The dashboard is a single HTML file — keep it self-contained
- The AI parser uses `claude-haiku-4-5-20251001` for cost efficiency
- The AI answer uses `claude-haiku-4-5-20251001` too — switch to Sonnet if quality needs improvement
- Always validate `ALLOWED_CHAT_IDS` before processing any message
