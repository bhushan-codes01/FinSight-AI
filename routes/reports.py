from flask import Blueprint, request, redirect, url_for, session, current_app, g, jsonify, send_file, flash
from services.pdf_service import PDFReportService
from services.report_generator import generate_pdf_report
from services.email_service import EmailAlertsService
from services.plan_gate import require_pro
from datetime import datetime
from services.db import get_db
from services.groq_service import GroqService
import os
import io

reports_bp = Blueprint("reports", __name__)


def get_groq_service():
    try:
        return GroqService()
    except Exception as e:
        print(f"[GROQ] Failed to initialize: {e}")
        return None


@reports_bp.route('/reports/pdf')
def download_pdf():
    if 'user_id' not in session:
        return redirect('/login')

    try:
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))

        groq_service = get_groq_service()

        pdf_bytes = generate_pdf_report(
            user_id=session['user_id'],
            month=month,
            year=year,
            db_conn=get_db(),
            ai_service=groq_service
        )

        filename = f"FinSight_Report_{year}_{str(month).zfill(2)}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return f"Error generating report: {str(e)}", 500


@reports_bp.route("/reports/send-email", methods=["POST"])
def send_report_email():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    json_data = request.get_json(silent=True) or {}
    month_year = json_data.get("month", datetime.now().strftime("%Y-%m"))

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

    user = db.execute("SELECT email, name, currency_symbol FROM users WHERE id = ?", (user_id,)).fetchone()
    email_service = EmailAlertsService(current_app)
    currency_symbol = user["currency_symbol"] if (user and user["currency_symbol"]) else "₹"

    budgets = db.execute(
        "SELECT b.*, COALESCE(SUM(t.amount), 0) as spent FROM budgets b LEFT JOIN transactions t ON b.user_id = t.user_id AND b.category = t.category AND t.transaction_type = 'expense' AND substr(t.transaction_date, 1, 7) = b.month WHERE b.user_id = ? GROUP BY b.id",
        (user_id,),
    ).fetchall()

    alerts_sent = 0

    for budget in budgets:
        spent = budget["spent"]
        budget_amount = budget["budget_amount"]
        percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0

        if percentage >= 100:
            email_service.send_budget_exceeded(user["email"], user["name"], budget["category"], spent, budget_amount, currency_symbol)
            alerts_sent += 1
        elif percentage >= 80:
            email_service.send_budget_warning(user["email"], user["name"], budget["category"], spent, budget_amount, currency_symbol)
            alerts_sent += 1

    return jsonify({"success": True, "alerts_sent": alerts_sent})


@reports_bp.route("/alerts/recurring-reminder", methods=["POST"])
def recurring_reminder():
    """Send reminders for upcoming recurring transactions"""
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    db = get_db()

    user = db.execute("SELECT email, name, currency_symbol FROM users WHERE id = ?", (user_id,)).fetchone()
    email_service = EmailAlertsService(current_app)
    currency_symbol = user["currency_symbol"] if (user and user["currency_symbol"]) else "₹"

    from datetime import datetime, timedelta
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    recurring = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND is_recurring = 1 AND next_due_date BETWEEN ? AND ?",
        (user_id, str(today), str(week_later)),
    ).fetchall()

    for txn in recurring:
        email_service.send_upcoming_recurring_reminder(
            user["email"], user["name"], txn["description"], txn["amount"], txn["next_due_date"], currency_symbol
        )

    return jsonify({"success": True, "reminders_sent": len(recurring)})
