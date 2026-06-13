import os
import sqlite3
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import auth_bp
from routes.transactions import transactions_bp
from routes.budget import budget_bp
from routes.chatbot import chatbot_bp
from routes.goals import goals_bp
from routes.reports import reports_bp
from services.analytics import AnalyticsService
from services.email_service import EmailAlertsService
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "finance_tracker.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.config["SECRET_KEY"] = app.secret_key
app.config["DATABASE"] = DATABASE_PATH

# Initialize Flask-Mail
email_service = EmailAlertsService(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(reports_bp)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped_view


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
    with open(schema_path, mode="r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def ensure_database():
    if not os.path.exists(app.config["DATABASE"]):
        os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    conn = sqlite3.connect(app.config["DATABASE"])
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    conn.close()

    if table_count == 0:
        with app.app_context():
            init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    analytics = AnalyticsService(get_db(), user_id)
    summary = analytics.generate_dashboard_summary()
    expense_breakdown = analytics.expense_breakdown_by_category()
    monthly_trend = analytics.monthly_trend_data()
    budget_status = analytics.budget_status_summary()
    recent_transactions = query_db(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 10",
        (user_id,),
    )

    return render_template(
        "dashboard.html",
        summary=summary,
        expense_breakdown=expense_breakdown,
        monthly_trend=monthly_trend,
        budget_status=budget_status,
        recent_transactions=recent_transactions,
    )


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
