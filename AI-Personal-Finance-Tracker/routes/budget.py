import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash, jsonify
from services.analytics import AnalyticsService

budget_bp = Blueprint("budget", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@budget_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@budget_bp.route("/budgets", methods=["GET", "POST"])
def manage_budgets():
    if not session.get("user_id"):
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    if request.method == "POST":
        category = request.form.get("category", "Other").strip()
        budget_amount = float(request.form.get("budget_amount", 0))
        month = request.form.get("month", "").strip()

        if not category or budget_amount <= 0 or not month:
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return jsonify({"error": "Invalid budget details"}), 400
            flash("Please provide valid budget details.", "danger")
            return redirect(url_for("budget.manage_budgets"))

        db.execute(
            "INSERT INTO budgets (user_id, category, budget_amount, month) VALUES (?, ?, ?, ?)",
            (user_id, category, budget_amount, month),
        )
        db.commit()

        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({"success": True, "message": "Budget created successfully."})
        
        flash("Budget created successfully.", "success")
        return redirect(url_for("budget.manage_budgets"))

    if request.headers.get('Accept') == 'application/json' or request.args.get('json') == '1':
        analytics = AnalyticsService(db, user_id)
        budget_status = analytics.budget_status_summary()
        return jsonify({"budgets": budget_status})

    analytics = AnalyticsService(db, user_id)
    budget_status = analytics.budget_status_summary()
    return render_template("budgets.html", budgets=budget_status)


@budget_bp.route("/budgets/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cursor = db.execute(
        "DELETE FROM budgets WHERE id = ? AND user_id = ?",
        (budget_id, session["user_id"]),
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Budget not found"}), 404

    return jsonify({"success": True})
