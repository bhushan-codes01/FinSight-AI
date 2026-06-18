try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    import warnings
    warnings.warn(f"WeasyPrint could not be loaded due to missing GTK libraries: {e}. PDF generation will fail locally but will work on Render.")
    WEASYPRINT_AVAILABLE = False

from flask import render_template_string
from datetime import datetime
import os
from services.db import get_db

# Category colors mapping
CATEGORY_COLORS = {
    'Food': '#f59e0b',
    'Travel': '#06b6d4',
    'Shopping': '#a855f7',
    'Housing': '#3b82f6',
    'Health': '#10b981',
    'Entertainment': '#ec4899',
    'Education': '#8b5cf6',
    'Utilities': '#f97316',
    'Income': '#4ade80',
    'Other': '#78716c',
}

# Category emoji mapping
CATEGORY_EMOJIS = {
    'Food': '🍔',
    'Travel': '🚗',
    'Shopping': '🛍️',
    'Housing': '🏠',
    'Health': '💊',
    'Entertainment': '🎮',
    'Education': '📚',
    'Utilities': '💡',
    'Income': '💰',
    'Other': '📦',
}


def generate_pdf_report(user_id, month, year, db_conn, gemini_service=None):
    """
    Generate a Warm Premium PDF report for the given user and month.
    Returns PDF bytes for download.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint is missing GObject/GTK C-libraries on your Windows system. "
            "Please follow the installation instructions to install GTK3 on Windows: "
            "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows "
            "Note: This will work perfectly on Render production Linux containers where weasyprint dependencies are pre-installed."
        )

    conn = db_conn

    # ── Fetch user info ──
    user = conn.execute(
        'SELECT name, email, currency_symbol, language FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    currency_symbol = "₹"
    user_name = "Valued Client"
    user_email = ""
    user_lang = "en"
    if user:
        try:
            user_name = user["name"] or "Valued Client"
        except (TypeError, KeyError, IndexError):
            user_name = user[0] or "Valued Client"
        try:
            user_email = user["email"] or ""
        except (TypeError, KeyError, IndexError):
            user_email = user[1] or ""
        try:
            currency_symbol = user["currency_symbol"] or "₹"
        except (TypeError, KeyError, IndexError):
            currency_symbol = user[2] or "₹"
        try:
            user_lang = user["language"] or "en"
        except (TypeError, KeyError, IndexError):
            user_lang = user[3] or "en"

    from flask import has_request_context, session
    if has_request_context() and "lang" in session:
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

    # ── Fetch transactions for the month ──
    # Note: Using substr to support both SQLite and PostgreSQL.
    transactions_raw = conn.execute('''
        SELECT amount, category, description, transaction_type, transaction_date
        FROM transactions
        WHERE user_id = ?
          AND substr(transaction_date, 6, 2) = ?
          AND substr(transaction_date, 1, 4) = ?
        ORDER BY transaction_date DESC
    ''', (user_id, str(month).zfill(2), str(year))).fetchall()

    # ── Calculate totals ──
    total_income = sum(
        t['amount'] for t in transactions_raw
        if t['transaction_type'] == 'income'
    )
    total_expenses = sum(
        t['amount'] for t in transactions_raw
        if t['transaction_type'] == 'expense'
    )
    net_savings = total_income - total_expenses
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0

    # ── Category breakdown ──
    category_totals = {}
    for t in transactions_raw:
        if t['transaction_type'] == 'expense':
            cat = t['category'] or 'Other'
            category_totals[cat] = category_totals.get(cat, 0) + t['amount']

    categories = []
    for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        percent = round((amount / total_expenses * 100), 1) if total_expenses > 0 else 0
        categories.append({
            'name': cat,
            'amount': f'{amount:,.2f}',
            'percent': percent,
            'color': CATEGORY_COLORS.get(cat, '#78716c'),
        })

    # ── Budget status ──
    budgets_raw = conn.execute('''
        SELECT category, budget_amount FROM budgets
        WHERE user_id = ? AND month = ?
    ''', (user_id, f'{year}-{str(month).zfill(2)}')).fetchall()

    budgets = []
    for b in budgets_raw:
        spent = category_totals.get(b['category'], 0)
        limit = b['budget_amount']
        percent_used = (spent / limit * 100) if limit > 0 else 0
        status = 'over' if percent_used >= 100 else 'warning' if percent_used >= 80 else 'ok'
        budgets.append({
            'category': b['category'],
            'spent': f'{spent:,.2f}',
            'limit': f'{limit:,.2f}',
            'status': status,
            'emoji': CATEGORY_EMOJIS.get(b['category'], '📦'),
        })

    # ── Savings goals ──
    goals_raw = conn.execute('''
        SELECT title, target_amount, current_amount FROM goals
        WHERE user_id = ?
    ''', (user_id,)).fetchall()

    goals = []
    for g in goals_raw:
        progress = round(
            (g['current_amount'] / g['target_amount'] * 100), 1
        ) if g['target_amount'] > 0 else 0
        goals.append({
            'title': g['title'],
            'current': f"{g['current_amount']:,.2f}",
            'target': f"{g['target_amount']:,.2f}",
            'progress': min(progress, 100),
        })

    # ── Format transactions ──
    transactions = []
    for t in transactions_raw:
        transactions.append({
            'date': t['transaction_date'],
            'description': t['description'] or 'No description',
            'category': t['category'] or 'Other',
            'type': t['transaction_type'],
            'amount': f"{t['amount']:,.2f}",
        })

    # ── AI Summary from Gemini ──
    ai_summary = "Financial summary not available."
    ai_tips = []

    if gemini_service and total_income > 0:
        try:
            prompt = f"""
            Generate a brief 2-sentence financial summary and 3 actionable tips for:
            - User: {user_name}
            - Month: {datetime(year, month, 1).strftime('%B %Y')}
            - Income: {currency_symbol}{total_income:,.2f}
            - Expenses: {currency_symbol}{total_expenses:,.2f}
            - Savings: {currency_symbol}{net_savings:,.2f} ({savings_rate}%)
            - Top category: {categories[0]['name'] if categories else 'N/A'}

            You MUST write the entire response strictly in the language: {target_language}. Do not write in any other language.
            Format your response as:
            SUMMARY: [2 sentence summary]
            TIP1: [tip 1]
            TIP2: [tip 2]
            TIP3: [tip 3]

            Use {currency_symbol} for all amounts. Be specific and actionable.
            """
            response = gemini_service.generate_content(prompt)
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('SUMMARY:'):
                    ai_summary = line.replace('SUMMARY:', '').strip()
                elif line.startswith('TIP'):
                    tip = line.split(':', 1)[-1].strip()
                    if tip:
                        ai_tips.append(tip)
        except Exception as e:
            print(f"[PDF] Gemini AI summary failed: {e}")
            from services.translation import translate
            fallback_fmt = translate(user_lang, "pdf_fallback_summary", "For {month_year}, {name} had total income of {income} and expenses of {expenses}, resulting in net savings of {savings}.")
            try:
                ai_summary = fallback_fmt.format(
                    month_year=datetime(year, month, 1).strftime('%B %Y'),
                    name=user_name,
                    income=f"{currency_symbol}{total_income:,.2f}",
                    expenses=f"{currency_symbol}{total_expenses:,.2f}",
                    savings=f"{currency_symbol}{net_savings:,.2f}"
                )
            except Exception:
                ai_summary = (
                    f"For {datetime(year, month, 1).strftime('%B %Y')}, "
                    f"{user_name} had total income of {currency_symbol}{total_income:,.2f} "
                    f"and expenses of {currency_symbol}{total_expenses:,.2f}, "
                    f"resulting in net savings of {currency_symbol}{net_savings:,.2f}."
                )

    # ── Month name ──
    from services.translation import translate
    month_key = datetime(year, month, 1).strftime('%B').lower()
    month_name = translate(user_lang, month_key, datetime(year, month, 1).strftime('%B'))
    generated_date = datetime.now().strftime('%d %b %Y, %I:%M %p')

    # ── Load HTML template ──
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'templates',
        'report_template.html'
    )
    with open(template_path, 'r', encoding='utf-8') as f:
        template_str = f.read()

    def translate_key(key, default=None):
        return translate(user_lang, key, default)

    # ── Render Jinja2 template ──
    rendered_html = render_template_string(
        template_str,
        _ = translate_key,
        user_name=user_name,
        user_email=user_email,
        month_name=month_name,
        year=year,
        generated_date=generated_date,
        currency_symbol=currency_symbol,
        total_income=f'{total_income:,.2f}',
        total_expenses=f'{total_expenses:,.2f}',
        net_savings=f'{net_savings:,.2f}',
        savings_rate=savings_rate,
        categories=categories,
        budgets=budgets,
        goals=goals,
        transactions=transactions,
        ai_summary=ai_summary,
        ai_tips=ai_tips,
    )

    # ── Convert HTML to PDF ──
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    return pdf_bytes
