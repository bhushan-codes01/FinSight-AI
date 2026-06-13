import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash

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
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    if request.method == "POST":
        category = request.form.get("category", "Other").strip()
        budget_amount = float(request.form.get("budget_amount", 0))
        month = request.form.get("month", "").strip()

        if not category or budget_amount <= 0 or not month:
            flash("Please provide valid budget details.", "danger")
            return redirect(url_for("budget.manage_budgets"))

        db.execute(
            "INSERT INTO budgets (user_id, category, budget_amount, month) VALUES (?, ?, ?, ?)",
            (user_id, category, budget_amount, month),
        )
        db.commit()
        flash("Budget updated successfully.", "success")
        return redirect(url_for("budget.manage_budgets"))

    budgets = db.execute(
        "SELECT * FROM budgets WHERE user_id = ? ORDER BY month DESC, category ASC", (user_id,)
    ).fetchall()
    return render_template("budgets.html", budgets=budgets)
