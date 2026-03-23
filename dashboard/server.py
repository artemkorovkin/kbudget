import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv
from db import init_db, get_conn

load_dotenv()

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/data")
def get_data():
    with get_conn() as conn:
        snapshots = conn.execute("SELECT * FROM monthly_snapshots ORDER BY month").fetchall()
        transactions = conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    return jsonify({
        "snapshots": [dict(r) for r in snapshots],
        "transactions": [dict(r) for r in transactions],
    })


@app.route("/api/summary/<month>")
def get_month(month):
    with get_conn() as conn:
        snap = conn.execute("SELECT * FROM monthly_snapshots WHERE month = ?", (month,)).fetchall()
        txs = conn.execute(
            "SELECT * FROM transactions WHERE month = ? ORDER BY created_at DESC", (month,)
        ).fetchall()
    return jsonify({
        "snapshot": dict(snap[0]) if snap else {},
        "transactions": [dict(r) for r in txs],
    })


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    app.run(host="0.0.0.0", port=port)
