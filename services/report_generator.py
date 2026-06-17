import os
from flask import render_template
from services.gemini_service import GeminiService

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except Exception:
    XHTML2PDF_AVAILABLE = False


class ReportGeneratorService:
    @staticmethod
    def generate_monthly_report_html(db, user_id, month, year):
        # Format month to 2 digits (e.g. 6 -> '06')
        month_str = f"{int(month):02d}"
        year_str = str(year)
        month_year = f"{year_str}-{month_str}"

        # Fetch user
        user = db.execute("SELECT name, email, currency_symbol FROM users WHERE id = ?", (user_id,)).fetchone()
        user_name = user["name"] if user else "Valued Client"
        currency_symbol = user["currency_symbol"] if (user and user["currency_symbol"]) else "₹"

        # Fetch transactions
        transactions = db.execute(
            "SELECT amount, category, description, transaction_type, transaction_date FROM transactions "
            "WHERE user_id = ? AND substr(transaction_date, 1, 4) = ? AND substr(transaction_date, 6, 2) = ? "
            "ORDER BY transaction_date DESC",
            (user_id, year_str, month_str)
        ).fetchall()

        income = sum(t["amount"] for t in transactions if t["transaction_type"] == "income")
        expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        net = income - expenses
        savings_rate = (net / income * 100) if income > 0 else 0.0

        # Category breakdown
        categories = {}
        for t in transactions:
            if t["transaction_type"] == "expense":
                cat = t["category"]
                categories[cat] = categories.get(cat, 0.0) + t["amount"]

        # Calculate category percentages
        category_breakdown = []
        for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / expenses * 100) if expenses > 0 else 0.0
            category_breakdown.append({
                "category": cat,
                "amount": amt,
                "percentage": round(pct, 1)
            })

        # Generate AI Summary using GeminiService
        prompt = (
            f"Please write a professional, concise financial report summary paragraph (2-3 sentences) "
            f"for {user_name} for {month_year}. "
            f"They had an income of {currency_symbol}{income:,.2f}, expenses of {currency_symbol}{expenses:,.2f}, a net balance of {currency_symbol}{net:,.2f}, "
            f"and a savings rate of {savings_rate:.1f}%. "
            f"Their top spending categories were: {', '.join([c['category'] + ' (' + currency_symbol + f'{c['amount']:,.0f}' + ')' for c in category_breakdown[:3]])}. "
            f"Offer brief financial coaching advice. Provide your response using {currency_symbol} as the currency symbol for all monetary amounts."
        )

        try:
            gemini = GeminiService()
            ai_summary = gemini.analyze(prompt)
        except Exception as e:
            ai_summary = f"AI summary currently unavailable due to an error: {e}"

        # Render report_template.html
        return render_template(
            "report_template.html",
            user_name=user_name,
            month=month_str,
            year=year_str,
            income=income,
            expenses=expenses,
            net=net,
            savings_rate=round(savings_rate, 1),
            category_breakdown=category_breakdown,
            transactions=transactions,
            ai_summary=ai_summary,
            currency_symbol=currency_symbol
        )

    @staticmethod
    def html_to_pdf(html_content):
        # Try WeasyPrint first
        if WEASYPRINT_AVAILABLE:
            try:
                return HTML(string=html_content).write_pdf()
            except Exception as e:
                # Log error or print to stderr
                print(f"WeasyPrint PDF generation failed: {e}")

        # Try xhtml2pdf as fallback
        if XHTML2PDF_AVAILABLE:
            try:
                from io import BytesIO
                result = BytesIO()
                pdf = pisa.pisaDocument(BytesIO(html_content.encode("utf-8")), result)
                if not pdf.err:
                    return result.getvalue()
                else:
                    print(f"xhtml2pdf PDF generation failed with error code: {pdf.err}")
            except Exception as e:
                print(f"xhtml2pdf PDF generation raised exception: {e}")

        return None
