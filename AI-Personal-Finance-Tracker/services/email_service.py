import os
from flask_mail import Mail, Message
from flask import current_app


class EmailAlertsService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
        app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", True)
        app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
        app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")
        app.config["MAIL_DEFAULT_SENDER"] = os.getenv("EMAIL_USER")
        self.mail = Mail(app)

    def send_budget_warning(self, user_email, user_name, category, spent, budget):
        """Send warning when budget is 80% used"""
        subject = f"⚠️ Budget Alert: {category} is {(spent/budget*100):.0f}% used"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>Your <strong>{category}</strong> budget is <strong>{(spent/budget*100):.0f}%</strong> used!</p>
        <p>Spent: ₹{spent:,.0f} of ₹{budget:,.0f}</p>
        <p>Remaining: ₹{budget-spent:,.0f}</p>
        <p><a href="https://financeai.app/budgets" style="background: #7c3aed; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Budgets</a></p>
        """
        self._send_email(user_email, subject, html)

    def send_budget_exceeded(self, user_email, user_name, category, spent, budget):
        """Send alert when budget is exceeded"""
        subject = f"🔴 Budget Exceeded: {category}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>You've exceeded your <strong>{category}</strong> budget!</p>
        <p>Spent: ₹{spent:,.0f}</p>
        <p>Budget: ₹{budget:,.0f}</p>
        <p>Overspent by: ₹{spent-budget:,.0f}</p>
        <p><a href="https://financeai.app/transactions" style="background: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Transactions</a></p>
        """
        self._send_email(user_email, subject, html)

    def send_report_ready(self, user_email, user_name, month_year):
        """Send notification when monthly report is ready"""
        subject = f"📊 Your Monthly Report is Ready - {month_year}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>Your financial report for <strong>{month_year}</strong> is ready to download!</p>
        <p>Get insights into your spending, savings, and recommendations from AI.</p>
        <p><a href="https://financeai.app/reports" style="background: #7c3aed; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Download Report</a></p>
        """
        self._send_email(user_email, subject, html)

    def send_unusual_spending_alert(self, user_email, user_name, amount, category):
        """Send alert for unusual spending patterns"""
        subject = f"💡 Unusual Spending Detected"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>We detected an unusual transaction in your account:</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Amount:</strong> ₹{amount:,.0f}</p>
        <p>This amount is significantly higher than your typical {category} spending.</p>
        <p><a href="https://financeai.app/transactions" style="background: #f59e0b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Transactions</a></p>
        """
        self._send_email(user_email, subject, html)

    def send_upcoming_recurring_reminder(self, user_email, user_name, description, amount, due_date):
        """Send reminder for upcoming recurring transactions"""
        subject = f"📅 Upcoming Expense: {description}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>You have an upcoming recurring expense:</p>
        <p><strong>Description:</strong> {description}</p>
        <p><strong>Amount:</strong> ₹{amount:,.0f}</p>
        <p><strong>Due:</strong> {due_date}</p>
        <p>Make sure you have enough balance in your account.</p>
        <p><a href="https://financeai.app/transactions" style="background: #06b6d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Details</a></p>
        """
        self._send_email(user_email, subject, html)

    def _send_email(self, recipient, subject, html):
        """Internal method to send email"""
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                html=html
            )
            self.mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")
            return False
