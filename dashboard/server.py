import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, send_from_directory, request, abort, session
from dotenv import load_dotenv
from db import init_db, get_conn
from data_seed import month_sort_key

load_dotenv()

app = Flask(__name__, static_folder=".")
app.secret_key = os.getenv("DASHBOARD_SECRET", "change-me-in-production")

DASHBOARD_TOKEN = os.getenv("DASHBOARD_TOKEN", "")


@app.before_request
def check_auth():
    # Token auth: once validated, store in session so subsequent requests work
    token = request.args.get("token")
    if token and token == DASHBOARD_TOKEN:
        session["authenticated"] = True

    if not session.get("authenticated"):
        abort(403)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/data")
def get_data():
    with get_conn() as conn:
        snapshots = conn.execute("SELECT * FROM monthly_snapshots").fetchall()
        transactions = conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    sorted_snaps = sorted([dict(r) for r in snapshots], key=lambda s: month_sort_key(s["month"]))
    return jsonify({
        "snapshots": sorted_snaps,
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
