import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configure email password string
email_pass = os.getenv('EMAIL_PASS') or os.getenv('EMAIL_PASSWORD') or ''

import sqlite3
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, jsonify, has_request_context
from flask_mail import Mail, Message
from routes.auth import auth_bp
from routes.transactions import transactions_bp, get_upcoming_recurring
from routes.budget import budget_bp
from routes.chatbot import chatbot_bp
from routes.goals import goals_bp
from routes.reports import reports_bp
from routes.billing import billing_bp
from routes.profile import profile_bp
from services.analytics import AnalyticsService
from services.email_service import EmailAlertsService

DATABASE_PATH = os.path.join(BASE_DIR, "database", "finance.db")

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.config["SECRET_KEY"] = app.secret_key
app.config["DATABASE"] = DATABASE_PATH

# Step 1 & 5: Flask-Mail Configuration and Space-Stripping for App Password
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
mail_port_env = os.getenv('MAIL_PORT', '587')
app.config['MAIL_PORT'] = int(mail_port_env) if str(mail_port_env).isdigit() else 587
tls_env = os.getenv('MAIL_USE_TLS', 'True')
app.config['MAIL_USE_TLS'] = tls_env.strip().lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = email_pass.replace(' ', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')

mail = Mail(app)
app.mail = mail

# Initialize Flask-Mail
email_service = EmailAlertsService(app)
app.email_service = email_service

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(profile_bp)


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
        if "firebase_uid" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN firebase_uid TEXT")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid)")
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
        if "currency" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'INR'")
            modified = True
        if "currency_symbol" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN currency_symbol TEXT DEFAULT '₹'")
            modified = True
        if "occupation" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN occupation TEXT DEFAULT ''")
            modified = True
        if "monthly_income" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN monthly_income REAL DEFAULT 0.0")
            modified = True
        if "savings_goal" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN savings_goal REAL DEFAULT 0.0")
            modified = True
        if "budget_style" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN budget_style TEXT DEFAULT '50/30/20'")
            modified = True
        if "risk_appetite" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN risk_appetite TEXT DEFAULT 'Moderate'")
            modified = True
        if "advice_level" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN advice_level TEXT DEFAULT 'Balanced'")
            modified = True
        if "theme" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'dark'")
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
def inject_global_user_data():
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.getenv("FIREBASE_APP_ID", "")
    }
    
    context = {
        "user_plan": "free",
        "email_verified": 0,
        "currency": "INR",
        "currency_symbol": "₹",
        "theme": "dark",
        "firebase_config": firebase_config
    }
    
    if not has_request_context() or not session.get("user_id"):
        return context
        
    try:
        db = get_db()
        user = db.execute("SELECT name, email, plan, email_verified, currency, currency_symbol, profile_picture, auth_provider, theme FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if user:
            context.update({
                "user_name": user["name"],
                "user_email": user["email"],
                "user_plan": user["plan"] or "free",
                "email_verified": user["email_verified"],
                "currency": user["currency"] or "INR",
                "currency_symbol": user["currency_symbol"] or "₹",
                "profile_picture": user["profile_picture"],
                "auth_provider": user["auth_provider"] or "local",
                "theme": user["theme"] or "dark"
            })
    except Exception:
        pass
    return context


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

    # Extract metrics with safe defaults (0 instead of None or empty)
    total_income = summary.get("income", 0) if summary else 0
    total_expenses = summary.get("expenses", 0) if summary else 0
    net_balance = summary.get("balance", 0) if summary else 0
    savings_rate = summary.get("savings_rate", 0) if summary else 0

    if total_income is None: total_income = 0
    if total_expenses is None: total_expenses = 0
    if net_balance is None: net_balance = 0
    if savings_rate is None: savings_rate = 0

    return render_template(
        "dashboard.html",
        summary=summary,
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
        savings_rate=savings_rate,
        expense_breakdown=expense_breakdown,
        monthly_trend=monthly_trend,
        budget_status=budget_status,
        recent_transactions=recent_transactions,
        upcoming_recurring=upcoming_recurring,
        email_notifications=email_notifications,
        email_verified=email_verified,
        user_plan=user_plan,
    )


@app.route("/settings", methods=["GET"])
@login_required
def settings_page():
    db = get_db()
    user = db.execute("SELECT email_notifications, currency FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    email_notifications = user["email_notifications"] if user else 1
    selected_currency = user["currency"] if user else "INR"
    
    from services.currency import CURRENCIES
    return render_template(
        "settings.html",
        email_notifications=email_notifications,
        selected_currency=selected_currency,
        currencies=CURRENCIES
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
    return redirect(url_for("settings_page"))


@app.route("/settings/currency", methods=["POST"])
@login_required
def update_currency():
    user_id = session["user_id"]
    currency_code = request.form.get("currency", "INR").upper()
    
    from services.currency import CURRENCIES
    if currency_code not in CURRENCIES:
        flash("Invalid currency selection.", "danger")
        return redirect(url_for("settings_page"))
        
    symbol = CURRENCIES[currency_code]["symbol"]
    
    db = get_db()
    db.execute("UPDATE users SET currency = ?, currency_symbol = ? WHERE id = ?", (currency_code, symbol, user_id))
    db.commit()
    
    flash(f"Currency updated to {currency_code} ({symbol}).", "success")
    return redirect(url_for("settings_page"))


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


@app.route("/analytics")
@login_required
def analytics_page():
    user_id = session["user_id"]
    db = get_db()
    
    analytics = AnalyticsService(db, user_id)
    summary = analytics.generate_dashboard_summary()
    expense_breakdown = analytics.expense_breakdown_by_category()
    monthly_trend = analytics.monthly_trend_data()
    budget_status = analytics.budget_status_summary()
    
    return render_template(
        "analytics.html",
        summary=summary,
        expense_breakdown=expense_breakdown,
        monthly_trend=monthly_trend,
        budget_status=budget_status
    )

@app.route("/dashboard/ai-insight")
@login_required
def dashboard_ai_insight():
    user_id = session["user_id"]
    db = get_db()
    
    analytics = AnalyticsService(db, user_id)
    summary = analytics.generate_dashboard_summary()
    budget_status = analytics.budget_status_summary()
    
    if not summary or (summary.get('income', 0) == 0 and summary.get('expenses', 0) == 0):
        return jsonify({
            "insight": "Welcome to FinSight AI! Log your first transaction under the Transactions page to unlock personalized, real-time AI-powered financial advisory. 🚀"
        })
        
    context = f"Income: {summary.get('income', 0)}, Expenses: {summary.get('expenses', 0)}, Net Balance: {summary.get('balance', 0)}, Savings Rate: {summary.get('savings_rate', 0)}%."
    if budget_status:
        over_budgets = [b['category'] for b in budget_status if b.get('status') == 'over-budget']
        if over_budgets:
            context += f" Over budget categories: {', '.join(over_budgets)}."
            
    prompt = (
        f"You are FinSight AI, a premium personal finance coach. Analyze this snapshot of the user's monthly finances: {context}. "
        f"Provide a short, extremely actionable, 2-sentence financial health recommendation or insight. Be encouraging and direct. Do not use markdown headers, but you can use emojis."
    )
    
    try:
        from services.gemini_service import GeminiService
        gemini = GeminiService()
        insight = gemini.analyze(prompt)
    except Exception as e:
        insight = "FinSight AI could not retrieve insights at this time. Please ensure a valid Google Gemini API key is configured."
        
    return jsonify({"insight": insight})

@app.route("/settings/toggle-theme", methods=["POST"])
@login_required
def toggle_theme():
    user_id = session["user_id"]
    data = request.get_json() or {}
    theme = data.get("theme", "dark").strip()
    
    if theme not in ["light", "dark"]:
        theme = "dark"
        
    db = get_db()
    db.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))
    db.commit()
    
    return jsonify({"success": True, "theme": theme})


ensure_database()

if __name__ == "__main__":
    app.run(debug=True)
