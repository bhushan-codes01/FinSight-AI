import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, jsonify, flash

transactions_bp = Blueprint("transactions", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@transactions_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@transactions_bp.route("/transactions", methods=["GET", "POST"])
def manage_transactions():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    if request.method == "POST":
        amount = float(request.form.get("amount", 0))
        category = request.form.get("category", "Other").strip()
        description = request.form.get("description", "").strip()
        transaction_type = request.form.get("transaction_type", "expense")
        transaction_date = request.form.get("transaction_date", "").strip()
        is_recurring = 1 if request.form.get("is_recurring") == "1" else 0
        recurrence_type = request.form.get("recurrence_type", "none").strip().lower() if is_recurring else "none"

        if amount <= 0 or transaction_type not in ["income", "expense"] or not transaction_date:
            flash("Please provide a valid transaction form.", "danger")
            return redirect(url_for("transactions.manage_transactions"))

        next_due_date = transaction_date if is_recurring else None

        db.execute(
            "INSERT INTO transactions (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date),
        )
        db.commit()

        # Check budget alerts for expenses
        if transaction_type == "expense":
            user = db.execute("SELECT email, name, email_notifications, currency_symbol FROM users WHERE id = ?", (user_id,)).fetchone()
            if user and user["email_notifications"]:
                try:
                    month_str = transaction_date[:7] # YYYY-MM
                    budget_row = db.execute(
                        "SELECT budget_amount FROM budgets WHERE user_id = ? AND category = ? AND month = ?",
                        (user_id, category, month_str)
                    ).fetchone()
                    
                    if budget_row:
                        budget_amount = budget_row["budget_amount"]
                        spent_row = db.execute(
                            "SELECT SUM(amount) as total_spent FROM transactions "
                            "WHERE user_id = ? AND category = ? AND transaction_type = 'expense' "
                            "AND strftime('%Y-%m', transaction_date) = ?",
                            (user_id, category, month_str)
                        ).fetchone()
                        
                        total_spent = spent_row["total_spent"] or 0.0
                        pct = (total_spent / budget_amount * 100) if budget_amount > 0 else 0
                        
                        from services.email_service import EmailAlertsService
                        email_service = EmailAlertsService(current_app)
                        
                        currency_sym = user["currency_symbol"] if user["currency_symbol"] else "₹"
                        
                        if pct >= 100:
                            alert_sent = db.execute(
                                "SELECT 1 FROM sent_alerts WHERE user_id = ? AND category = ? AND month = ? AND alert_type = 'exceeded'",
                                (user_id, category, month_str)
                            ).fetchone()
                            if not alert_sent:
                                email_service.send_budget_exceeded(user["email"], user["name"], category, total_spent, budget_amount, currency_sym)
                                db.execute(
                                    "INSERT INTO sent_alerts (user_id, category, month, alert_type) VALUES (?, ?, ?, 'exceeded')",
                                    (user_id, category, month_str)
                                )
                                db.commit()
                        elif pct >= 80:
                            alert_sent = db.execute(
                                "SELECT 1 FROM sent_alerts WHERE user_id = ? AND category = ? AND month = ? AND alert_type IN ('warning', 'exceeded')",
                                (user_id, category, month_str)
                            ).fetchone()
                            if not alert_sent:
                                email_service.send_budget_warning(user["email"], user["name"], category, total_spent, budget_amount, currency_sym)
                                db.execute(
                                    "INSERT INTO sent_alerts (user_id, category, month, alert_type) VALUES (?, ?, ?, 'warning')",
                                    (user_id, category, month_str)
                                )
                                db.commit()
                except Exception as e:
                    print(f"Error checking budget alerts: {e}")

        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({
                "success": True,
                "message": "Transaction added successfully." + (" (Recurring)" if is_recurring else "")
            })
        flash("Transaction added successfully." + (" (Recurring)" if is_recurring else ""), "success")
        return redirect(url_for("transactions.manage_transactions"))

    category = request.args.get("category", "")
    transaction_type = request.args.get("type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    search = request.args.get("search", "")

    query = "SELECT * FROM transactions WHERE user_id = ?"
    args = [user_id]

    if category:
        query += " AND category = ?"
        args.append(category)
    if transaction_type:
        query += " AND transaction_type = ?"
        args.append(transaction_type)
    if start_date:
        query += " AND transaction_date >= ?"
        args.append(start_date)
    if end_date:
        query += " AND transaction_date <= ?"
        args.append(end_date)
    if search:
        query += " AND (description LIKE ? OR category LIKE ?)"
        args.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY transaction_date DESC"
    transactions = db.execute(query, tuple(args)).fetchall()

    if request.headers.get('Accept') == 'application/json' or request.args.get('json') == '1':
        return jsonify({
            "transactions": [dict(t) for t in transactions]
        })

    # Get upcoming recurring transactions
    recurring = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND is_recurring = 1 AND next_due_date IS NOT NULL ORDER BY next_due_date ASC LIMIT 5",
        (user_id,),
    ).fetchall()

    return render_template("transactions.html", transactions=transactions, recurring=recurring)


def get_upcoming_recurring(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type FROM transactions WHERE user_id = ? AND is_recurring = 1",
        (user_id,)
    ).fetchall()

    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    upcoming = []

    for row in rows:
        try:
            start_date = datetime.strptime(row["transaction_date"], "%Y-%m-%d").date()
        except Exception:
            continue

        rec_type = row["recurrence_type"]
        if not rec_type or rec_type == "none":
            continue

        next_date = start_date
        while next_date < today:
            if rec_type == "weekly":
                next_date += timedelta(days=7)
            elif rec_type == "monthly":
                try:
                    month = next_date.month + 1
                    year = next_date.year
                    if month > 12:
                        month = 1
                        year += 1
                    day = min(next_date.day, 28 if month == 2 else 30 if month in [4,6,9,11] else 31)
                    next_date = next_date.replace(year=year, month=month, day=day)
                except Exception:
                    next_date += timedelta(days=30)
            else:
                break

        if today <= next_date <= week_later:
            days_until = (next_date - today).days
            upcoming.append({
                "id": row["id"],
                "description": row["description"] or row["category"],
                "category": row["category"],
                "amount": row["amount"],
                "transaction_type": row["transaction_type"],
                "due_date": next_date.strftime("%Y-%m-%d"),
                "days_until": days_until
            })

    upcoming.sort(key=lambda x: x["due_date"])
    return upcoming


@transactions_bp.route("/transactions/upcoming", methods=["GET"])
def upcoming_recurring():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    db = get_db()

    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    recurring = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND is_recurring = 1 AND next_due_date BETWEEN ? AND ? ORDER BY next_due_date ASC",
        (user_id, str(today), str(week_later)),
    ).fetchall()

    return jsonify({
        "upcoming": [dict(r) for r in recurring],
        "count": len(recurring)
    })


@transactions_bp.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")
    transaction_type = data.get("transaction_type")
    transaction_date = data.get("transaction_date")

    if not amount or not category or not transaction_type or not transaction_date:
        return jsonify({"error": "Invalid payload"}), 400

    db = get_db()
    cursor = db.execute(
        "UPDATE transactions SET amount = ?, category = ?, description = ?, transaction_type = ?, transaction_date = ? WHERE id = ? AND user_id = ?",
        (amount, category, description, transaction_type, transaction_date, transaction_id, session["user_id"]),
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"success": True})


@transactions_bp.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cursor = db.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, session["user_id"]),
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"success": True})

