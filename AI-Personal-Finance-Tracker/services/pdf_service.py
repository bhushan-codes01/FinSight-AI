import os
from datetime import datetime
from io import BytesIO
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except Exception:
    XHTML2PDF_AVAILABLE = False

import sqlite3


class PDFReportService:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    def generate_monthly_report(self, month_year=None):
        """Generate a PDF report for a specific month (format: YYYY-MM)"""
        if month_year is None:
            month_year = datetime.now().strftime("%Y-%m")

        user = self.db.execute(
            "SELECT name, email, currency_symbol FROM users WHERE id = ?", (self.user_id,)
        ).fetchone()
        currency_symbol = user["currency_symbol"] if (user and user["currency_symbol"]) else "₹"

        transactions = self.db.execute(
            "SELECT amount, category, description, transaction_type, transaction_date FROM transactions WHERE user_id = ? AND strftime('%Y-%m', transaction_date) = ? ORDER BY transaction_date DESC",
            (self.user_id, month_year),
        ).fetchall()

        income = sum(t["amount"] for t in transactions if t["transaction_type"] == "income")
        expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        net = income - expenses

        # Category breakdown
        categories = {}
        for t in transactions:
            if t["transaction_type"] == "expense":
                cat = t["category"]
                categories[cat] = categories.get(cat, 0) + t["amount"]

        # AI Summary
        summary_text = self._generate_summary(income, expenses, net, categories, currency_symbol)

        # Create HTML
        html_content = self._create_html(user, month_year, income, expenses, net, transactions, categories, summary_text, currency_symbol)

        # Generate PDF
        pdf_bytes = None
        if WEASYPRINT_AVAILABLE:
            try:
                pdf_bytes = HTML(string=html_content).write_pdf()
            except Exception as e:
                print(f"WeasyPrint PDF generation failed in PDFReportService: {e}")

        if pdf_bytes is None and XHTML2PDF_AVAILABLE:
            try:
                from io import BytesIO
                result = BytesIO()
                pdf = pisa.pisaDocument(BytesIO(html_content.encode("utf-8")), result)
                if not pdf.err:
                    pdf_bytes = result.getvalue()
                else:
                    print(f"xhtml2pdf PDF generation failed in PDFReportService with error code: {pdf.err}")
            except Exception as e:
                print(f"xhtml2pdf PDF generation raised exception in PDFReportService: {e}")

        if pdf_bytes:
            return pdf_bytes, f"FinanceAI_Report_{month_year}.pdf"
        else:
            return html_content.encode("utf-8"), f"FinanceAI_Report_{month_year}.html"

    def _generate_summary(self, income, expenses, net, categories, currency_symbol="₹"):
        if expenses == 0:
            return "No expenses recorded this month."

        top_category = max(categories, key=categories.get) if categories else "N/A"
        top_amount = categories.get(top_category, 0) if categories else 0

        return f"""
        Your financial summary for this period:
        - Total Income: {currency_symbol}{income:,.0f}
        - Total Expenses: {currency_symbol}{expenses:,.0f}
        - Net Balance: {currency_symbol}{net:,.0f}
        - Top Spending Category: {top_category} ({currency_symbol}{top_amount:,.0f})
        - Expense Ratio: {(expenses/income*100) if income > 0 else 0:.1f}% of income

        Recommendation: Review your {top_category} spending to identify savings opportunities.
        """

    def _create_html(self, user, month_year, income, expenses, net, transactions, categories, summary, currency_symbol="₹"):
        category_rows = "".join(
            f"<tr><td>{cat}</td><td>{currency_symbol}{amount:,.0f}</td><td>{(amount/expenses*100):.1f}%</td></tr>"
            for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        )

        transaction_rows = "".join(
            f"<tr><td>{t['transaction_date']}</td><td>{t['description']}</td><td>{t['category']}</td><td style='color: {'#10b981' if t['transaction_type'] == 'income' else '#ef4444'}'>{t['transaction_type'].upper()}</td><td>{currency_symbol}{t['amount']:,.0f}</td></tr>"
            for t in transactions
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: Arial, sans-serif; color: #333; background: white; }}
                .container {{ max-width: 900px; margin: 0 auto; padding: 40px; }}
                .header {{ border-bottom: 3px solid #7c3aed; padding-bottom: 20px; margin-bottom: 30px; }}
                h1 {{ color: #7c3aed; margin-bottom: 5px; }}
                .report-meta {{ color: #999; font-size: 14px; }}
                .summary-cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
                .card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
                .card-label {{ color: #999; font-size: 12px; margin-bottom: 8px; }}
                .card-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                .section {{ margin: 30px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; color: #7c3aed; margin-bottom: 15px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #7c3aed; color: white; padding: 12px; text-align: left; font-weight: bold; }}
                td {{ padding: 12px; border-bottom: 1px solid #f0f0f0; }}
                tr:hover {{ background: #f9f9f9; }}
                .summary-text {{ background: #f0f7ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; line-height: 1.6; }}
                .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FinanceAI Monthly Report</h1>
                    <p class="report-meta">For {user['name']} • {month_year} • {datetime.now().strftime('%B %d, %Y')}</p>
                </div>

                <div class="summary-cards">
                    <div class="card">
                        <div class="card-label">TOTAL INCOME</div>
                        <div class="card-value">{currency_symbol}{income:,.0f}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">TOTAL EXPENSES</div>
                        <div class="card-value">{currency_symbol}{expenses:,.0f}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">NET BALANCE</div>
                        <div class="card-value" style="color: {'#10b981' if net >= 0 else '#ef4444'};">{currency_symbol}{net:,.0f}</div>
                    </div>
                    <div class="card">
                        <div class="card-label">SAVINGS RATE</div>
                        <div class="card-value">{(net/income*100) if income > 0 else 0:.1f}%</div>
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">AI Insights & Recommendations</div>
                    <div class="summary-text">{summary}</div>
                </div>

                <div class="section">
                    <div class="section-title">Spending by Category</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Category</th>
                                <th>Amount</th>
                                <th>% of Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {category_rows}
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <div class="section-title">All Transactions</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Category</th>
                                <th>Type</th>
                                <th>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {transaction_rows}
                        </tbody>
                    </table>
                </div>

                <div class="footer">
                    <p>This report was generated by FinanceAI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Your financial data is encrypted and secure.</p>
                </div>
            </div>
        </body>
        </html>
        """
