import sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, jsonify, flash
from services.gemini_service import GeminiService

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


@goals_bp.route("/goals", methods=["GET", "POST"])
def manage_goals():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        target_amount = float(request.form.get("target_amount", 0))
        deadline = request.form.get("deadline", "").strip()

        if not title or target_amount <= 0 or not deadline:
            flash("Please provide valid goal details.", "danger")
            return redirect(url_for("goals.manage_goals"))

        db.execute(
            "INSERT INTO savings_goals (user_id, title, target_amount, current_amount, deadline) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, target_amount, 0, deadline),
        )
        db.commit()
        flash("Savings goal created successfully!", "success")
        return redirect(url_for("goals.manage_goals"))

    goals = db.execute(
        "SELECT * FROM savings_goals WHERE user_id = ? ORDER BY deadline ASC", (user_id,)
    ).fetchall()

    # Calculate progress for each goal
    goal_data = []
    for goal in goals:
        progress_pct = round((goal["current_amount"] / goal["target_amount"] * 100)) if goal["target_amount"] > 0 else 0
        remaining = goal["target_amount"] - goal["current_amount"]
        deadline_obj = datetime.strptime(goal["deadline"], "%Y-%m-%d")
        today = datetime.now()
        days_left = (deadline_obj - today).days
        
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


@goals_bp.route("/goals/<int:goal_id>/update", methods=["POST"])
def update_goal_progress(goal_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    amount = data.get("amount", 0)

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    db = get_db()
    goal = db.execute(
        "SELECT * FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, session["user_id"]),
    ).fetchone()

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    new_amount = min(goal["current_amount"] + amount, goal["target_amount"])
    db.execute(
        "UPDATE savings_goals SET current_amount = ?, updated_at = datetime('now') WHERE id = ?",
        (new_amount, goal_id),
    )
    db.commit()

    return jsonify({"success": True, "new_amount": new_amount})


@goals_bp.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cursor = db.execute(
        "DELETE FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, session["user_id"]),
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Goal not found"}), 404

    return jsonify({"success": True})


@goals_bp.route("/goals/<int:goal_id>/advice", methods=["POST"])
def get_goal_advice(goal_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    goal = db.execute(
        "SELECT * FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, session["user_id"]),
    ).fetchone()

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    # Get recent transactions for context
    transactions = db.execute(
        "SELECT amount, category, transaction_type FROM transactions WHERE user_id = ? AND transaction_type = 'expense' ORDER BY transaction_date DESC LIMIT 30",
        (session["user_id"],),
    ).fetchall()

    expense_avg = sum(t["amount"] for t in transactions) / max(len(transactions), 1)
    remaining = goal["target_amount"] - goal["current_amount"]
    days_left = max((datetime.strptime(goal["deadline"], "%Y-%m-%d") - datetime.now()).days, 1)
    daily_needed = remaining / days_left

    prompt = (
        f"I have a savings goal: '{goal['title']}' to save ₹{goal['target_amount']:,.0f}. "
        f"I've already saved ₹{goal['current_amount']:,.0f} and have {days_left} days left. "
        f"I need to save ₹{daily_needed:.0f} per day. My average daily expense is ₹{expense_avg:.0f}. "
        f"Provide 3 specific, actionable tips to help me reach this goal faster. "
        f"Be encouraging and realistic about my timeline."
    )

    gemini = GeminiService()
    advice = gemini.analyze(prompt)

    return jsonify({"advice": advice})
