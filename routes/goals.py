from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, jsonify, flash
from services.gemini_service import GeminiService
from models.goal import Goal
from services.db import get_db

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("/goals", methods=["GET"])
def get_goals():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    goals = Goal.get_all_by_user(db, user_id)

    # Calculate progress and metadata for each goal
    goal_data = []
    for goal in goals:
        progress_pct = round((goal["current_amount"] / goal["target_amount"] * 100)) if goal["target_amount"] > 0 else 0
        remaining = max(goal["target_amount"] - goal["current_amount"], 0)
        
        try:
            deadline_obj = datetime.strptime(goal["deadline"], "%Y-%m-%d")
            today = datetime.now()
            # Reset times to compare dates
            deadline_obj = deadline_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_obj - today).days
        except Exception:
            days_left = 0
            
        daily_rate = remaining / max(days_left, 1)
        
        goal_data.append({
            "id": goal["id"],
            "title": goal["title"],
            "target_amount": goal["target_amount"],
            "current_amount": goal["current_amount"],
            "remaining": remaining,
            "deadline": goal["deadline"],
            "progress_pct": min(progress_pct, 100),
            "days_left": max(days_left, 0),
            "daily_rate": round(daily_rate, 2),
        })

    if request.headers.get('Accept') == 'application/json' or request.args.get('json') == '1':
        return jsonify({"goals": goal_data})

    return render_template("goals.html", goals=goal_data)


@goals_bp.route("/goals", methods=["POST"])
def create_goal():
    if not session.get("user_id"):
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    
    if request.is_json:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        try:
            target_amount = float(data.get("target_amount", 0))
        except (TypeError, ValueError):
            target_amount = 0
        deadline = data.get("deadline", "").strip()
    else:
        title = request.form.get("title", "").strip()
        try:
            target_amount = float(request.form.get("target_amount", 0))
        except (TypeError, ValueError):
            target_amount = 0
        deadline = request.form.get("deadline", "").strip()

    if not title or target_amount <= 0 or not deadline:
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({"error": "Please provide valid goal details."}), 400
        flash("Please provide valid goal details.", "danger")
        return redirect(url_for("goals.get_goals"))

    db = get_db()
    goal_id = Goal.create(db, user_id, title, target_amount, deadline)
    
    if request.headers.get('Accept') == 'application/json' or request.is_json:
        try:
            deadline_obj = datetime.strptime(deadline, "%Y-%m-%d")
            today = datetime.now()
            deadline_obj = deadline_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_obj - today).days
        except Exception:
            days_left = 0
            
        remaining = target_amount
        daily_rate = remaining / max(days_left, 1)
        
        goal_data = {
            "id": goal_id,
            "title": title,
            "target_amount": target_amount,
            "current_amount": 0.0,
            "remaining": remaining,
            "deadline": deadline,
            "progress_pct": 0,
            "days_left": max(days_left, 0),
            "daily_rate": round(daily_rate, 2),
        }
        return jsonify({"success": True, "goal": goal_data})

    flash("Savings goal created successfully!", "success")
    return redirect(url_for("goals.get_goals"))


@goals_bp.route("/goals/<int:goal_id>", methods=["PUT"])
def update_goal(goal_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    # Support JSON or form data
    data = request.get_json() or {}
    amount = data.get("amount")
    if amount is None:
        amount = request.form.get("amount")
        
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, session["user_id"])).fetchone()
    if not row:
        return jsonify({"error": "Goal not found"}), 404
        
    new_amount = Goal.update_progress(db, goal_id, session["user_id"], amount)
    if new_amount is None:
        return jsonify({"error": "Goal not found"}), 404

    target_amount = row["target_amount"]
    progress_pct = round((new_amount / target_amount * 100)) if target_amount > 0 else 0
    remaining = max(target_amount - new_amount, 0)
    
    try:
        deadline_obj = datetime.strptime(row["deadline"], "%Y-%m-%d")
        today = datetime.now()
        deadline_obj = deadline_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        days_left = (deadline_obj - today).days
    except Exception:
        days_left = 0
        
    daily_rate = remaining / max(days_left, 1)
    
    return jsonify({
        "success": True,
        "new_amount": new_amount,
        "progress_pct": min(progress_pct, 100),
        "remaining": remaining,
        "daily_rate": round(daily_rate, 2),
        "target_amount": target_amount,
        "days_left": max(days_left, 0)
    })


@goals_bp.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    success = Goal.delete(db, goal_id, session["user_id"])
    
    if not success:
        return jsonify({"error": "Goal not found"}), 404

    return jsonify({"success": True})


@goals_bp.route("/goals/advice", methods=["POST"])
def get_goal_advice():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = data.get("title")
    target_amount = data.get("target_amount")
    current_amount = data.get("current_amount")
    deadline = data.get("deadline")

    if not title or target_amount is None or current_amount is None or not deadline:
        # Fallback to loading goal from db if only ID is provided or if fields missing
        goal_id = data.get("id")
        if goal_id:
            db = get_db()
            row = db.execute("SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, session["user_id"])).fetchone()
            if row:
                title = row["title"]
                target_amount = row["target_amount"]
                current_amount = row["current_amount"]
                deadline = row["deadline"]
            else:
                return jsonify({"error": "Goal not found"}), 404
        else:
            return jsonify({"error": "Missing goal details"}), 400

    try:
        target_amount = float(target_amount)
        current_amount = float(current_amount)
        deadline_obj = datetime.strptime(deadline, "%Y-%m-%d")
        today = datetime.now()
        days_left = max((deadline_obj - today).days, 1)
    except Exception as e:
        return jsonify({"error": f"Invalid data format: {e}"}), 400

    remaining = max(target_amount - current_amount, 0)
    daily_needed = remaining / days_left

    # Query recent transactions for context if available
    db = get_db()
    user = db.execute("SELECT currency_symbol FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    currency_symbol = user["currency_symbol"] if (user and user["currency_symbol"]) else "₹"

    transactions = db.execute(
        "SELECT amount, category, transaction_type FROM transactions WHERE user_id = ? AND transaction_type = 'expense' ORDER BY transaction_date DESC LIMIT 30",
        (session["user_id"],),
    ).fetchall()

    expense_avg = sum(t["amount"] for t in transactions) / max(len(transactions), 1)

    prompt = (
        f"I have a savings goal: '{title}' to save {currency_symbol}{target_amount:,.0f}. "
        f"I've already saved {currency_symbol}{current_amount:,.0f} and have {days_left} days left. "
        f"I need to save {currency_symbol}{daily_needed:.0f} per day. My average daily expense is {currency_symbol}{expense_avg:.0f}. "
        f"Provide 3 specific, actionable tips to help me reach this goal faster. "
        f"Be encouraging and realistic about my timeline. "
        f"Provide your response using {currency_symbol} as the currency symbol for all monetary amounts."
    )

    gemini = GeminiService()
    advice = gemini.analyze(prompt)

    return jsonify({"advice": advice})
