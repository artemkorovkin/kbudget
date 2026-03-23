import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from data_seed import get_russian_month, month_sort_key

DB_PATH = os.getenv("DATABASE_PATH", "budget.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrency for multiple users
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
    month_str = get_russian_month(now)
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
            "SELECT * FROM monthly_snapshots"
        ).fetchall()
        txs = conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

    snaps = sorted([dict(s) for s in snaps], key=lambda s: month_sort_key(s["month"]))

    lines = ["=== Monthly Snapshots ==="]
    for s in snaps:
        lines.append(
            f"{s['month']}: income \u20bd{s['total_income']:,.0f}, "
            f"expenses \u20bd{s['total_expenses']:,.0f}, "
            f"profit \u20bd{s['profit']:,.0f}, "
            f"total debt \u20bd{s['total_debt']:,.0f}"
        )

    if txs:
        lines.append("\n=== Recent Manual Transactions ===")
        for t in txs:
            t = dict(t)
            lines.append(
                f"{t['month']} | {t['type']} | {t['category']} | "
                f"\u20bd{t['amount']:,.0f} | {t['description'] or ''}"
            )

    return "\n".join(lines)
