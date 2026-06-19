import os
import datetime
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash, jsonify
from services.groq_service import GroqService
from services.db import get_db

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot")
def chatbot_page():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))
    history = db.execute(
        "SELECT user_message, ai_response FROM chat_history "
        "WHERE user_id = ? ORDER BY id ASC",
        (session["user_id"],)
    ).fetchall()
    return render_template("chatbot.html", chat_history=history)


def handle_create_budget(user_id, db, args, currency_symbol="₹"):
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
        "message": f"Successfully created a budget limit of {currency_symbol}{budget_amount:,.2f} for '{category}' for the month of {month}."
    }


def handle_log_transaction(user_id, db, args, currency_symbol="₹"):
    try:
        amount = float(args.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    category = args.get("category", "Other").strip()
    description = args.get("description", "").strip()
    transaction_type = args.get("transaction_type", "expense").strip().lower()
    transaction_date = args.get("transaction_date", "").strip()
    
    is_rec_val = args.get("is_recurring")
    if isinstance(is_rec_val, str):
        is_recurring = 1 if is_rec_val.strip().lower() in ("true", "1", "yes") else 0
    else:
        is_recurring = 1 if is_rec_val else 0
        
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
        "message": f"Successfully logged {transaction_type} of {currency_symbol}{amount:,.2f} under category '{category}' on {transaction_date}."
    }


@chatbot_bp.route("/chat", methods=["POST"])
@chatbot_bp.route("/chatbot/send", methods=["POST"])
def chat():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    db = get_db()
    
    # Fetch user currency, language, and profile settings
    user = db.execute(
        "SELECT name, currency_symbol, language, occupation, monthly_income, savings_goal, budget_style, risk_appetite, advice_level "
        "FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    
    if not user:
        session.clear()
        return jsonify({"error": "Unauthorized", "message": "User not found in database. Please log in again."}), 401
        
    user_name = "FinSighter"
    currency_symbol = "₹"
    user_lang = "en"
    occupation = "Not specified"
    monthly_income = 0.0
    savings_goal_val = 0.0
    budget_style = "50/30/20"
    risk_appetite = "Moderate"
    advice_level = "Balanced"
    
    try:
        user_name = user["name"] or "FinSighter"
        currency_symbol = user["currency_symbol"] or "₹"
        user_lang = user["language"] or "en"
        occupation = user["occupation"] or "Not specified"
        monthly_income = float(user["monthly_income"] or 0.0)
        savings_goal_val = float(user["savings_goal"] or 0.0)
        budget_style = user["budget_style"] or "50/30/20"
        risk_appetite = user["risk_appetite"] or "Moderate"
        advice_level = user["advice_level"] or "Balanced"
    except (TypeError, KeyError, IndexError):
        user_name = user[0] or "FinSighter"
        currency_symbol = user[1] or "₹"
        user_lang = user[2] or "en"
        occupation = user[3] or "Not specified"
        monthly_income = float(user[4] or 0.0)
        savings_goal_val = float(user[5] or 0.0)
        budget_style = user[6] or "50/30/20"
        risk_appetite = user[7] or "Moderate"
        advice_level = user[8] or "Balanced"
    
    if "lang" in session:
        user_lang = session["lang"]
        
    LANGUAGES_MAP = {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "mr": "Marathi (मराठी)",
        "es": "Spanish (Español)",
        "fr": "French (Français)",
        "de": "German (Deutsch)",
        "gu": "Gujarati (ગુજરાતી)",
        "bn": "Bengali (বাংলা)",
        "ta": "Tamil (தமிழ்)",
        "kn": "Kannada (ಕನ್ನಡ)"
    }
    target_language = LANGUAGES_MAP.get(user_lang, "English")
    
    # 1. Check AI Quota for Free Plan
    from services.plan_gate import check_ai_quota, increment_ai_usage, get_user_plan
    if not check_ai_quota(user_id):
        return jsonify({
            "error": "quota_exceeded", 
            "message": "Daily limit reached. Upgrade to Pro for unlimited AI chat.",
            "response": "⚠️ Daily limit reached. Upgrade to Pro for unlimited AI chat."
        }), 403

    if request.is_json:
        req_data = request.get_json() or {}
        user_question = req_data.get("message", "").strip()
        csv_file = None
    else:
        user_question = request.form.get("user_question", "").strip()
        csv_file = request.files.get("statement_file")

    # 2. Check CSV Gating (Pro only)
    if csv_file and csv_file.filename:
        if get_user_plan(user_id) != 'pro':
            return jsonify({
                "error": "pro_required", 
                "message": "CSV upload and analysis is a Pro feature. Please upgrade to Pro to upload statements.",
                "response": "⚠️ CSV upload and analysis is a Pro feature. Please upgrade to Pro to upload statements."
            }), 403

    # If quota ok, increment usage count
    increment_ai_usage(user_id)

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

    budgets_text = "\n".join([f"- {r['category']} ({r['month']}): Limit {currency_symbol}{r['budget_amount']:,.2f}" for r in budgets_rows]) or "None set"
    goals_text = "\n".join([f"- {r['title']}: Saved {currency_symbol}{r['current_amount']:,.2f} of {currency_symbol}{r['target_amount']:,.2f} (Deadline: {r['deadline']})" for r in goals_rows]) or "None set"
    recurring_text = "\n".join([f"- {r['category']} ({r['recurrence_type']}): {currency_symbol}{r['amount']:,.2f} (Next Due: {r['next_due_date']})" for r in recurring_rows]) or "None set"
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
            f"- Total Income: {currency_symbol}{total_income:,.2f}\n"
            f"- Total Expenses: {currency_symbol}{total_expense:,.2f}\n"
            f"- Net Cash Flow: {currency_symbol}{net_flow:,.2f}\n"
            f"- Top Expense Categories:\n"
        )
        for cat, amt in top_cats.items():
            context_summary += f"  * {cat}: {currency_symbol}{amt:,.2f}\n"
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
                f"- Total Inflow: {currency_symbol}{csv_income:,.2f}\n"
                f"- Total Outflow: {currency_symbol}{csv_expense:,.2f}\n"
            )
        except Exception as e:
            current_app.logger.error(f"Error parsing uploaded CSV in chatbot context: {e}")

    # 3. Formulate standard system instruction & tools
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d (%A)")
    profile_summary = (
        "USER PROFILE CONTEXT:\n"
        f"- Name: {user_name}\n"
        f"- Occupation: {occupation}\n"
        f"- Monthly Income: {currency_symbol}{monthly_income:,.2f}\n"
        f"- Savings Goal: {currency_symbol}{savings_goal_val:,.2f}\n"
        f"- Budgeting Style: {budget_style}\n"
        f"- Investment Risk Appetite: {risk_appetite}\n"
        f"- Financial Advice Level: {advice_level}\n\n"
    )
    system_instruction = (
        "You are FinSight AI, a premium professional personal financial assistant.\n"
        "Your goal is to help users manage their money, track budgets, save for goals, and analyze transactions.\n\n"
        "PERSONALITY & STYLE:\n"
        "- Tone: Professional, encouraging, realistic, and highly mathematical.\n"
        "- Math-Focused: Always cite exact figures (totals, averages, progress percentages, days remaining) in your advice.\n"
        f"- Currency formatting: Use {currency_symbol} as the currency symbol for all monetary amounts in your replies.\n"
        f"- Today's Date: The current date is {current_date_str}. Use this date as the default when the user refers to 'today', 'yesterday', 'this week', 'this month', or similar relative times.\n"
        f"- LANGUAGE REQUIREMENT: You MUST speak, respond, and analyze strictly in the language: {target_language}. Do not write in any other language, even if the user prompts you in a different language. However, keep the function calls in standard schema format.\n"
        "- Restrictive scope: Only answer questions related to personal finance, budgeting, saving, or financial analysis. "
        "If the user asks an unrelated question (like coding, history, or science), politely decline to answer and redirect them back to their finances.\n\n"
        f"{profile_summary}"
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
                                "type": "STRING",
                                "description": "The budget limit amount (e.g. '5000' or '1000.50')"
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
                                "type": "STRING",
                                "description": "The transaction amount (e.g. '150' or '250.75')"
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
                                "type": "STRING",
                                "description": "Whether the transaction is recurring, must be 'true' or 'false'"
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

    # Fetch recent chat history to provide conversational context memory
    history_rows = db.execute(
        "SELECT user_message, ai_response FROM chat_history "
        "WHERE user_id = ? ORDER BY id DESC LIMIT 5",
        (user_id,)
    ).fetchall()
    
    contents = []
    for row in reversed(history_rows):
        contents.append({
            "role": "user",
            "parts": [{"text": row["user_message"]}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": row["ai_response"]}]
        })
        
    contents.append({
        "role": "user",
        "parts": [{"text": user_question}]
    })

    user_plan = get_user_plan(user_id)
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ai_service = GroqService(model_name=model_name)
    response_data = ai_service.analyze_with_history(
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
            result = handle_create_budget(user_id, db, func_args, currency_symbol)
        elif func_name == "log_transaction":
            result = handle_log_transaction(user_id, db, func_args, currency_symbol)
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

        # Call Groq again with execution result to get the final conversational text response
        second_resp = ai_service.analyze_with_history(
            contents=contents,
            system_instruction=system_instruction,
            tools=tools
        )
        ai_response = second_resp.get("text", "")
        if not ai_response or "AI service error:" in ai_response:
            if result.get("success"):
                ai_response = f"[System Note: Action executed successfully, but Groq response limit was reached.] {result.get('message')}"
            else:
                ai_response = f"Action failed: {result.get('error', 'Unknown database execution error.')}"
    else:
        ai_response = response_data.get("text", "No response returned from Groq.")
        if "AI service error:" in ai_response:
            if "429" in ai_response or "quota" in ai_response.lower() or "limit" in ai_response.lower():
                ai_response = "⚠️ The AI Assistant is currently experiencing a rate limit or has exceeded its daily/monthly quota. Please check your Groq API key settings in the .env file or try again in a few moments."
            else:
                ai_response = f"⚠️ AI Service Error: {ai_response.replace('AI service error: ', '')}"

    db.execute(
        "INSERT INTO chat_history (user_id, user_message, ai_response) VALUES (?, ?, ?)",
        (session["user_id"], user_question, ai_response),
    )
    db.commit()

    return jsonify({"response": ai_response})

