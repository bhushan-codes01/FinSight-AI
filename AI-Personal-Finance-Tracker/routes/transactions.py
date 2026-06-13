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
        is_recurring = int(request.form.get("is_recurring", 0))
        recurrence_type = request.form.get("recurrence_type", None) if is_recurring else None

        if amount <= 0 or transaction_type not in ["income", "expense"] or not transaction_date:
            flash("Please provide a valid transaction form.", "danger")
            return redirect(url_for("transactions.manage_transactions"))

        next_due_date = transaction_date if is_recurring else None

        db.execute(
            "INSERT INTO transactions (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date),
        )
        db.commit()
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

    # Get upcoming recurring transactions
    recurring = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND is_recurring = 1 AND next_due_date IS NOT NULL ORDER BY next_due_date ASC LIMIT 5",
        (user_id,),
    ).fetchall()

    return render_template("transactions.html", transactions=transactions, recurring=recurring)


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

