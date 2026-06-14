import os
import sqlite3
import datetime
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash, jsonify
from services.gemini_service import GeminiService

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


def handle_create_budget(user_id, db, args):
    category = args.get("category", "Other").strip()
    try:
        budget_amount = float(args.get("budget_amount", 0))
    except (TypeError, ValueError):
        budget_amount = 0
    month = args.get("month", "").strip()

    if not category or budget_amount <= 0 or not month:
        return {"success": False, "error": "Invalid budget details"}

    db.execute(
        "INSERT INTO budgets (user_id, category, budget_amount, month) VALUES (?, ?, ?, ?)",
        (user_id, category, budget_amount, month),
    )
    db.commit()
    return {
        "success": True, 
        "message": f"Successfully created a budget limit of ₹{budget_amount:,.2f} for '{category}' for the month of {month}."
    }


def handle_log_transaction(user_id, db, args):
    try:
        amount = float(args.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    category = args.get("category", "Other").strip()
    description = args.get("description", "").strip()
    transaction_type = args.get("transaction_type", "expense").strip().lower()
    transaction_date = args.get("transaction_date", "").strip()
    is_recurring = 1 if args.get("is_recurring") else 0
    recurrence_type = args.get("recurrence_type", "none").strip().lower() if is_recurring else "none"

    if amount <= 0 or transaction_type not in ["income", "expense"] or not transaction_date:
        return {"success": False, "error": "Invalid transaction form fields."}

    next_due_date = transaction_date if is_recurring else None

    db.execute(
        "INSERT INTO transactions (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, amount, category, description, transaction_type, transaction_date, is_recurring, recurrence_type, next_due_date),
    )
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully logged {transaction_type} of ₹{amount:,.2f} under category '{category}' on {transaction_date}."
    }


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_question = request.form.get("user_question", "").strip()
    csv_file = request.files.get("statement_file")
    user_id = session["user_id"]
    db = get_db()

    # 1. Fetch current user financial context snapshot (RAG)
    budgets_rows = db.execute(
        "SELECT category, budget_amount, month FROM budgets WHERE user_id = ?",
        (user_id,)
    ).fetchall()

    goals_rows = db.execute(
        "SELECT title, target_amount, current_amount, deadline FROM goals WHERE user_id = ?",
        (user_id,)
    ).fetchall()

    recurring_rows = db.execute(
        "SELECT amount, category, description, recurrence_type, next_due_date FROM transactions "
        "WHERE user_id = ? AND is_recurring = 1",
        (user_id,)
    ).fetchall()

    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    trans_rows = db.execute(
        "SELECT amount, category, description, transaction_type, transaction_date FROM transactions "
        "WHERE user_id = ? AND transaction_date >= ? ORDER BY transaction_date DESC",
        (user_id, start_date)
    ).fetchall()

    budgets_text = "\n".join([f"- {r['category']} ({r['month']}): Limit ₹{r['budget_amount']:,.2f}" for r in budgets_rows]) or "None set"
    goals_text = "\n".join([f"- {r['title']}: Saved ₹{r['current_amount']:,.2f} of ₹{r['target_amount']:,.2f} (Deadline: {r['deadline']})" for r in goals_rows]) or "None set"
    recurring_text = "\n".join([f"- {r['category']} ({r['recurrence_type']}): ₹{r['amount']:,.2f} (Next Due: {r['next_due_date']})" for r in recurring_rows]) or "None set"
    trans_df = pd.DataFrame([dict(r) for r in trans_rows]) if trans_rows else pd.DataFrame()

    context_summary = (
        "=== ACTIVE SYSTEM BUDGETS ===\n"
        f"{budgets_text}\n\n"
        "=== ACTIVE SAVINGS milestones ===\n"
        f"{goals_text}\n\n"
        "=== UPCOMING RECURRING BILLS ===\n"
        f"{recurring_text}\n\n"
    )

    if not trans_df.empty:
        trans_df['amount'] = pd.to_numeric(trans_df['amount'], errors='coerce').fillna(0.0)
        total_income = float(trans_df[trans_df['transaction_type'] == 'income']['amount'].sum())
        total_expense = float(trans_df[trans_df['transaction_type'] == 'expense']['amount'].sum())
        net_flow = total_income - total_expense
        
        expenses_df = trans_df[trans_df['transaction_type'] == 'expense']
        top_cats = {}
        if not expenses_df.empty:
            top_cats = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5).to_dict()

        context_summary += (
            "=== LAST 30 DAYS DATABASE SUMMARY ===\n"
            f"- Total Transactions: {len(trans_df)}\n"
            f"- Total Income: ₹{total_income:,.2f}\n"
            f"- Total Expenses: ₹{total_expense:,.2f}\n"
            f"- Net Cash Flow: ₹{net_flow:,.2f}\n"
            f"- Top Expense Categories:\n"
        )
        for cat, amt in top_cats.items():
            context_summary += f"  * {cat}: ₹{amt:,.2f}\n"
    else:
        context_summary += "=== LAST 30 DAYS DATABASE SUMMARY ===\nNo recent transactions found.\n"

    # 2. Append CSV stats if CSV file uploaded
    if csv_file and csv_file.filename:
        try:
            df = pd.read_csv(csv_file)
            df.columns = [c.strip().lower() for c in df.columns]
            if 'amount' in df.columns:
                df['amount'] = pd.to_numeric(df['amount'].astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce').fillna(0.0)
            else:
                df['amount'] = 0.0
            if 'transaction_type' in df.columns:
                df['transaction_type'] = df['transaction_type'].astype(str).str.strip().str.lower()
            else:
                df['transaction_type'] = 'expense'
            if 'category' not in df.columns:
                df['category'] = 'Other'
            
            csv_income = float(df[df['transaction_type'] == 'income']['amount'].sum())
            csv_expense = float(df[df['transaction_type'] == 'expense']['amount'].sum())
            
            context_summary += (
                "\n=== UPLOADED STATEMENT STATS ===\n"
                f"- Statement File: {csv_file.filename}\n"
                f"- Total Records: {len(df)}\n"
                f"- Total Inflow: ₹{csv_income:,.2f}\n"
                f"- Total Outflow: ₹{csv_expense:,.2f}\n"
            )
        except Exception as e:
            current_app.logger.error(f"Error parsing uploaded CSV in chatbot context: {e}")

    # 3. Formulate standard system instruction & tools
    system_instruction = (
        "You are FinSight AI, a premium professional personal financial assistant.\n"
        "Your goal is to help users manage their money, track budgets, save for goals, and analyze transactions.\n\n"
        "PERSONALITY & STYLE:\n"
        "- Tone: Professional, encouraging, realistic, and highly mathematical.\n"
        "- Math-Focused: Always cite exact figures (totals, averages, progress percentages, days remaining) in your advice.\n"
        "- Restrictive scope: Only answer questions related to personal finance, budgeting, saving, or financial analysis. "
        "If the user asks an unrelated question (like coding, history, or science), politely decline to answer and redirect them back to their finances.\n\n"
        "CURRENT USER PROFILE SUMMARY CONTEXT:\n"
        f"{context_summary}\n"
        "FUNCTION CALLING / LOCAL ACTIONS:\n"
        "You have tools to perform database actions on the user's behalf: create_budget and log_transaction.\n"
        "- If the user expresses a clear intent to log an expense or income, call log_transaction.\n"
        "- If the user expresses a clear intent to set a category budget limit, call create_budget.\n"
        "- Do not call functions if details are missing or if the user's request is purely informational.\n"
        "- After executing a function, explain the result and summarize the updated status to the user in a natural, encouraging way."
    )

    tools = [
        {
            "functionDeclarations": [
                {
                    "name": "create_budget",
                    "description": "Create a budget limit for a category for a specific month.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "category": {
                                "type": "STRING",
                                "description": "Budget category name (e.g. food, transport, shopping, rent, utilities)"
                            },
                            "budget_amount": {
                                "type": "NUMBER",
                                "description": "The budget limit amount in Rupees"
                            },
                            "month": {
                                "type": "STRING",
                                "description": "The month in YYYY-MM format (e.g. 2026-06)"
                            }
                        },
                        "required": ["category", "budget_amount", "month"]
                    }
                },
                {
                    "name": "log_transaction",
                    "description": "Log or create a new transaction (income or expense) on the user's behalf.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "amount": {
                                "type": "NUMBER",
                                "description": "The transaction amount in Rupees"
                            },
                            "category": {
                                "type": "STRING",
                                "description": "Category name (e.g. food, transport, shopping, salary, entertainment)"
                            },
                            "description": {
                                "type": "STRING",
                                "description": "Short description of the transaction"
                            },
                            "transaction_type": {
                                "type": "STRING",
                                "description": "Type of transaction, must be either 'income' or 'expense'"
                            },
                            "transaction_date": {
                                "type": "STRING",
                                "description": "Date of transaction in YYYY-MM-DD format"
                            },
                            "is_recurring": {
                                "type": "BOOLEAN",
                                "description": "Whether the transaction is recurring"
                            },
                            "recurrence_type": {
                                "type": "STRING",
                                "description": "Type of recurrence if is_recurring is true (must be either 'daily', 'weekly', 'monthly', 'yearly', or 'none')"
                            }
                        },
                        "required": ["amount", "category", "transaction_type", "transaction_date"]
                    }
                }
            ]
        }
    ]

    contents = [
        {
            "role": "user",
            "parts": [{"text": user_question}]
        }
    ]

    gemini = GeminiService()
    response_data = gemini.analyze_with_history(
        contents=contents,
        system_instruction=system_instruction,
        tools=tools
    )

    # 4. Handle function calling loop
    if "functionCall" in response_data:
        func_call = response_data["functionCall"]
        func_name = func_call["name"]
        func_args = func_call["args"]

        if func_name == "create_budget":
            result = handle_create_budget(user_id, db, func_args)
        elif func_name == "log_transaction":
            result = handle_log_transaction(user_id, db, func_args)
        else:
            result = {"success": False, "error": f"Unknown tool: {func_name}"}

        # Append Turn 2 (model's request) to contents
        contents.append({
            "role": "model",
            "parts": [
                {
                    "functionCall": {
                        "name": func_name,
                        "args": func_args
                    }
                }
            ]
        })

        # Append Turn 3 (tool response) to contents
        contents.append({
            "role": "user",
            "parts": [
                {
                    "functionResponse": {
                        "name": func_name,
                        "response": result
                    }
                }
            ]
        })

        # Call Gemini again with execution result to get the final conversational text response
        second_resp = gemini.analyze_with_history(
            contents=contents,
            system_instruction=system_instruction,
            tools=tools
        )
        ai_response = second_resp.get("text", "")
        if not ai_response or "AI service error:" in ai_response:
            if result.get("success"):
                ai_response = f"[System Note: Action executed successfully, but Gemini response limit was reached.] {result.get('message')}"
            else:
                ai_response = f"Action failed: {result.get('error', 'Unknown database execution error.')}"
    else:
        ai_response = response_data.get("text", "No response returned from Gemini.")
        if "AI service error:" in ai_response:
            if "429" in ai_response or "quota" in ai_response.lower() or "limit" in ai_response.lower():
                ai_response = "⚠️ The AI Assistant is currently experiencing a rate limit or has exceeded its daily/monthly quota. Please check your Gemini API key settings in Google AI Studio or try again in a few moments."
            else:
                ai_response = f"⚠️ AI Service Error: {ai_response.replace('AI service error: ', '')}"

    db.execute(
        "INSERT INTO chat_history (user_id, user_message, ai_response) VALUES (?, ?, ?)",
        (session["user_id"], user_question, ai_response),
    )
    db.commit()

    return jsonify({"response": ai_response})

