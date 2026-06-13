import os
import csv
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash, jsonify
from services.gemini_service import GeminiService
from services.csv_processor import CSVProcessor

chatbot_bp = Blueprint("chatbot", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@chatbot_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@chatbot_bp.route("/chatbot")
def chatbot_page():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return render_template("chatbot.html")


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_question = request.form.get("user_question", "").strip()
    csv_file = request.files.get("statement_file")
    transaction_data = []

    db = get_db()
    if csv_file and csv_file.filename:
        transaction_data = CSVProcessor(csv_file).parse_transactions()
    else:
        rows = db.execute(
            "SELECT amount, category, description, transaction_type, transaction_date FROM transactions WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 50",
            (session["user_id"],),
        ).fetchall()
        for row in rows:
            transaction_data.append(dict(row))

    prompt = (
        "You are a professional financial assistant. Analyze the following transaction data: "
        f"{transaction_data}. User question: {user_question}. Provide: 1. Summary 2. Key Insights 3. Savings Opportunities 4. Budget Recommendations. Keep response concise and actionable."
    )

    gemini = GeminiService()
    ai_response = gemini.analyze(prompt)

    db.execute(
        "INSERT INTO chat_history (user_id, user_message, ai_response) VALUES (?, ?, ?)",
        (session["user_id"], user_question, ai_response),
    )
    db.commit()

    return jsonify({"response": ai_response})
