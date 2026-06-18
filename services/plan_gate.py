from datetime import datetime
from functools import wraps
from flask import g, current_app, redirect, url_for, session, jsonify, request
from services.db import get_db

def get_user_plan(user_id):
    db = get_db()
    # Check users table first
    user = db.execute("SELECT plan, plan_expiry FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return 'free'
        
    plan = user["plan"] or 'free'
    plan_expiry = user["plan_expiry"]
    
    if plan == 'pro':
        if not plan_expiry:
            return 'pro'
        try:
            # Parse plan_expiry (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, or date/datetime objects)
            if isinstance(plan_expiry, str):
                expiry_date = datetime.strptime(plan_expiry.split(" ")[0], "%Y-%m-%d").date()
            elif isinstance(plan_expiry, datetime):
                expiry_date = plan_expiry.date()
            else:
                # Assuming it is already a datetime.date object
                expiry_date = plan_expiry
                
            if expiry_date >= datetime.now().date():
                return 'pro'
        except Exception:
            # Fallback to pro on parse error to avoid locking paid users
            return 'pro'

    # Check subscriptions table as fallback
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sub = db.execute(
        "SELECT id FROM subscriptions WHERE user_id = ? AND plan = 'pro' AND status = 'active' AND (expires_at IS NULL OR expires_at > ?)",
        (user_id, now_str)
    ).fetchone()
    
    if sub:
        return 'pro'
        
    return 'free'

def check_ai_quota(user_id):
    plan = get_user_plan(user_id)
    if plan == 'pro':
        return True
        
    db = get_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    row = db.execute(
        "SELECT message_count FROM ai_usage WHERE user_id = ? AND usage_date = ?",
        (user_id, today_str)
    ).fetchone()
    
    if row and row["message_count"] >= 10:
        return False
    return True

def increment_ai_usage(user_id):
    db = get_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    db.execute(
        "INSERT OR IGNORE INTO ai_usage (user_id, usage_date, message_count) VALUES (?, ?, 0)",
        (user_id, today_str)
    )
    db.execute(
        "UPDATE ai_usage SET message_count = message_count + 1 WHERE user_id = ? AND usage_date = ?",
        (user_id, today_str)
    )
    db.commit()

def require_pro(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
            
        user_id = session["user_id"]
        if get_user_plan(user_id) != 'pro':
            # In AJAX/API endpoints, return JSON error instead of redirection
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "pro_required", "message": "This feature requires a Pro subscription."}), 403
            return redirect(url_for("billing.upgrade"))
            
        return f(*args, **kwargs)
    return decorated_function
