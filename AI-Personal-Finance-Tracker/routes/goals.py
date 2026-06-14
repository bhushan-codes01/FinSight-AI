import sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, jsonify, flash
from services.gemini_service import GeminiService
from models.goal import Goal

goals_bp = Blueprint("goals", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@goals_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


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

    return render_template("goals.html", goals=goal_data)


@goals_bp.route("/goals", methods=["POST"])
def create_goal():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    title = request.form.get("title", "").strip()
    target_amount = float(request.form.get("target_amount", 0))
    deadline = request.form.get("deadline", "").strip()

    if not title or target_amount <= 0 or not deadline:
        flash("Please provide valid goal details.", "danger")
        return redirect(url_for("goals.get_goals"))

    db = get_db()
    Goal.create(db, user_id, title, target_amount, deadline)
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
    new_amount = Goal.update_progress(db, goal_id, session["user_id"], amount)
    
    if new_amount is None:
        return jsonify({"error": "Goal not found"}), 404

    return jsonify({"success": True, "new_amount": new_amount})


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
    transactions = db.execute(
        "SELECT amount, category, transaction_type FROM transactions WHERE user_id = ? AND transaction_type = 'expense' ORDER BY transaction_date DESC LIMIT 30",
        (session["user_id"],),
    ).fetchall()

    expense_avg = sum(t["amount"] for t in transactions) / max(len(transactions), 1)

    prompt = (
        f"I have a savings goal: '{title}' to save ₹{target_amount:,.0f}. "
        f"I've already saved ₹{current_amount:,.0f} and have {days_left} days left. "
        f"I need to save ₹{daily_needed:.0f} per day. My average daily expense is ₹{expense_avg:.0f}. "
        f"Provide 3 specific, actionable tips to help me reach this goal faster. "
        f"Be encouraging and realistic about my timeline."
    )

    gemini = GeminiService()
    advice = gemini.analyze(prompt)

    return jsonify({"advice": advice})
