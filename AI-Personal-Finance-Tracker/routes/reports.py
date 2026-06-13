import sqlite3
from flask import Blueprint, request, redirect, url_for, session, current_app, g, jsonify, send_file, flash
from services.pdf_service import PDFReportService
from services.email_service import EmailAlertsService
from datetime import datetime

reports_bp = Blueprint("reports", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@reports_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@reports_bp.route("/reports/pdf", methods=["GET"])
def download_report():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    month_year = request.args.get("month", datetime.now().strftime("%Y-%m"))
    db = get_db()

    pdf_service = PDFReportService(db, session["user_id"])
    pdf_bytes, filename = pdf_service.generate_monthly_report(month_year)

    return send_file(
        __import__("io").BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route("/reports/send-email", methods=["POST"])
def send_report_email():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    month_year = request.json.get("month", datetime.now().strftime("%Y-%m"))

    db = get_db()
    user = db.execute("SELECT email, name FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        email_service = EmailAlertsService(current_app)
        email_service.send_report_ready(user["email"], user["name"], month_year)
        return jsonify({"success": True, "message": "Report sent to your email"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/alerts/check-budgets", methods=["POST"])
def check_budget_alerts():
    """Check if any budgets need alerts"""
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    db = get_db()

    user = db.execute("SELECT email, name FROM users WHERE id = ?", (user_id,)).fetchone()
    email_service = EmailAlertsService(current_app)

    budgets = db.execute(
        "SELECT b.*, COALESCE(SUM(t.amount), 0) as spent FROM budgets b LEFT JOIN transactions t ON b.user_id = t.user_id AND b.category = t.category AND t.transaction_type = 'expense' AND strftime('%Y-%m', t.transaction_date) = b.month WHERE b.user_id = ? GROUP BY b.id",
        (user_id,),
    ).fetchall()

    alerts_sent = 0

    for budget in budgets:
        spent = budget["spent"]
        budget_amount = budget["budget_amount"]
        percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0

        if percentage >= 100:
            email_service.send_budget_exceeded(user["email"], user["name"], budget["category"], spent, budget_amount)
            alerts_sent += 1
        elif percentage >= 80:
            email_service.send_budget_warning(user["email"], user["name"], budget["category"], spent, budget_amount)
            alerts_sent += 1

    return jsonify({"success": True, "alerts_sent": alerts_sent})


@reports_bp.route("/alerts/recurring-reminder", methods=["POST"])
def recurring_reminder():
    """Send reminders for upcoming recurring transactions"""
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    db = get_db()

    user = db.execute("SELECT email, name FROM users WHERE id = ?", (user_id,)).fetchone()
    email_service = EmailAlertsService(current_app)

    from datetime import datetime, timedelta
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    recurring = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND is_recurring = 1 AND next_due_date BETWEEN ? AND ?",
        (user_id, str(today), str(week_later)),
    ).fetchall()

    for txn in recurring:
        email_service.send_upcoming_recurring_reminder(
            user["email"], user["name"], txn["description"], txn["amount"], txn["next_due_date"]
        )

    return jsonify({"success": True, "reminders_sent": len(recurring)})
