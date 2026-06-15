import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import sqlite3
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import auth_bp, oauth
from routes.transactions import transactions_bp, get_upcoming_recurring
from routes.budget import budget_bp
from routes.chatbot import chatbot_bp
from routes.goals import goals_bp
from routes.reports import reports_bp
from routes.billing import billing_bp
from services.analytics import AnalyticsService
from services.email_service import EmailAlertsService

DATABASE_PATH = os.path.join(BASE_DIR, "database", "finance.db")

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.config["SECRET_KEY"] = app.secret_key
app.config["DATABASE"] = DATABASE_PATH

# Initialize Flask-Mail
email_service = EmailAlertsService(app)
app.email_service = email_service

# Initialize OAuth
oauth.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(billing_bp)


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

    if table_count == 0:
        conn.close()
        with app.app_context():
            init_db()
    else:
        # Check if goals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
        goals_exists = cursor.fetchone()
        modified = False
        if not goals_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    target_amount REAL,
                    current_amount REAL DEFAULT 0,
                    deadline DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            modified = True

        # Check if sent_alerts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sent_alerts'")
        sent_alerts_exists = cursor.fetchone()
        if not sent_alerts_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    month TEXT,
                    alert_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            modified = True
        
        # Check if budgets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'")
        budgets_exists = cursor.fetchone()
        if not budgets_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    budget_amount REAL NOT NULL,
                    month TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            modified = True

        # Check if chat_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        chat_history_exists = cursor.fetchone()
        if not chat_history_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            modified = True

        # Check users columns
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [row[1] for row in cursor.fetchall()]
        if "email_notifications" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN email_notifications INTEGER DEFAULT 1")
            modified = True
        if "google_id" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
            modified = True
        if "auth_provider" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'")
            modified = True
        if "profile_picture" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
            modified = True
        if "email_verified" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            modified = True
        if "plan" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
            modified = True
        if "plan_expiry" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN plan_expiry DATE")
            modified = True

        # Check if auth_tokens table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_tokens'")
        auth_tokens_exists = cursor.fetchone()
        if not auth_tokens_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE NOT NULL,
                    token_type TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            modified = True

        # Check if subscriptions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
        subscriptions_exists = cursor.fetchone()
        if not subscriptions_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan TEXT NOT NULL,
                    billing_cycle TEXT,
                    razorpay_subscription_id TEXT,
                    razorpay_payment_id TEXT,
                    status TEXT DEFAULT 'active',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            modified = True

        # Check if ai_usage table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage'")
        ai_usage_exists = cursor.fetchone()
        if not ai_usage_exists:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    usage_date DATE,
                    message_count INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(user_id, usage_date)
                )
            """)
            modified = True

        cursor.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in cursor.fetchall()]
        if "is_recurring" not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0")
            modified = True
        if "recurrence_type" not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence_type TEXT CHECK(recurrence_type IN ('daily', 'weekly', 'monthly', 'yearly', NULL))")
            modified = True
        if "next_due_date" not in columns:
            cursor.execute("ALTER TABLE transactions ADD COLUMN next_due_date TEXT")
            modified = True
        if modified:
            conn.commit()
        conn.close()


@app.context_processor
def inject_user_plan():
    if not session.get("user_id"):
        return {}
    try:
        db = get_db()
        user = db.execute("SELECT plan, email_verified FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if user:
            return {
                "user_plan": user["plan"] or "free",
                "email_verified": user["email_verified"]
            }
    except Exception:
        pass
    return {"user_plan": "free", "email_verified": 0}


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
    upcoming_recurring = get_upcoming_recurring(user_id)

    user_data = query_db("SELECT email_notifications, email_verified, plan FROM users WHERE id = ?", (user_id,), one=True)
    email_notifications = user_data["email_notifications"] if user_data else 1
    email_verified = user_data["email_verified"] if user_data else 0
    user_plan = user_data["plan"] if user_data else "free"

    return render_template(
        "dashboard.html",
        summary=summary,
        expense_breakdown=expense_breakdown,
        monthly_trend=monthly_trend,
        budget_status=budget_status,
        recent_transactions=recent_transactions,
        upcoming_recurring=upcoming_recurring,
        email_notifications=email_notifications,
        email_verified=email_verified,
        user_plan=user_plan,
    )


@app.route("/settings/notifications", methods=["POST"])
@login_required
def toggle_notifications():
    user_id = session["user_id"]
    enabled = 1 if request.form.get("email_notifications") == "1" else 0
    
    db = get_db()
    db.execute("UPDATE users SET email_notifications = ? WHERE id = ?", (enabled, user_id))
    db.commit()
    
    flash("Notification preferences updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/debug-env")
def debug_env():
    return {
        "GOOGLE_CLIENT_ID_present": os.getenv("GOOGLE_CLIENT_ID") is not None,
        "GOOGLE_CLIENT_ID_val": os.getenv("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET_present": os.getenv("GOOGLE_CLIENT_SECRET") is not None,
        "GOOGLE_CLIENT_SECRET_len": len(os.getenv("GOOGLE_CLIENT_SECRET") or ""),
    }


@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    return f"""
    <div style="font-family: monospace; padding: 20px; background: #111; color: #ff5555;">
        <h2>Internal Server Error (500)</h2>
        <pre>{tb}</pre>
    </div>
    """, 500


ensure_database()

if __name__ == "__main__":
    app.run(debug=True)
