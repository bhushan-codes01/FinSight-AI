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
        
        port_raw = os.getenv("MAIL_PORT")
        if port_raw and str(port_raw).strip().isdigit():
            app.config["MAIL_PORT"] = int(port_raw)
        else:
            app.config["MAIL_PORT"] = 587
            
        tls_raw = os.getenv("MAIL_USE_TLS")
        if tls_raw is not None:
            app.config["MAIL_USE_TLS"] = str(tls_raw).strip().lower() in ("true", "1", "yes")
        else:
            app.config["MAIL_USE_TLS"] = True
            
        app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
        app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS")
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

    def send_verification_email(self, user_email, token):
        """Send email verification link to user"""
        subject = "🔑 Verify Your Email - FinSight AI"
        verify_url = f"http://localhost:5000/verify-email/{token}"
        from flask import request
        try:
            verify_url = f"{request.url_root.rstrip('/')}/verify-email/{token}"
        except Exception:
            pass

        html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; border-bottom: 2px solid #7c3aed; padding-bottom: 20px; margin-bottom: 20px;">
                <h1 style="color: #7c3aed; margin: 0; font-size: 24px;">FinSight AI</h1>
                <p style="color: #64748b; margin: 5px 0 0 0;">AI-Powered Personal Finance Tracker</p>
            </div>
            <h2 style="color: #1e293b; margin-top: 0;">Confirm your email address</h2>
            <p style="color: #334155; line-height: 1.6;">Thank you for signing up for FinSight AI! Please click the button below to verify your email address and activate your account. This link will expire in 24 hours.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" style="background-color: #7c3aed; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; box-shadow: 0 4px 6px -1px rgba(124, 58, 237, 0.2);">Verify Email Address</a>
            </div>
            <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px;">If you didn't create an account, you can safely ignore this email.<br>If the button doesn't work, copy and paste this link into your browser:<br><a href="{verify_url}" style="color: #7c3aed;">{verify_url}</a></p>
        </div>
        """
        return self._send_email(user_email, subject, html)

    def send_password_reset_email(self, user_email, token):
        """Send password reset link to user"""
        subject = "🔒 Reset Your Password - FinSight AI"
        reset_url = f"http://localhost:5000/reset-password/{token}"
        from flask import request
        try:
            reset_url = f"{request.url_root.rstrip('/')}/reset-password/{token}"
        except Exception:
            pass

        html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; border-bottom: 2px solid #7c3aed; padding-bottom: 20px; margin-bottom: 20px;">
                <h1 style="color: #7c3aed; margin: 0; font-size: 24px;">FinSight AI</h1>
                <p style="color: #64748b; margin: 5px 0 0 0;">AI-Powered Personal Finance Tracker</p>
            </div>
            <h2 style="color: #1e293b; margin-top: 0;">Password Reset Request</h2>
            <p style="color: #334155; line-height: 1.6;">We received a request to reset the password for your FinSight AI account. Click the button below to choose a new password. This link will expire in 1 hour.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #7c3aed; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; box-shadow: 0 4px 6px -1px rgba(124, 58, 237, 0.2);">Reset Password</a>
            </div>
            <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px;">If you did not request a password reset, please ignore this email or contact support if you have concerns.<br>If the button doesn't work, copy and paste this link into your browser:<br><a href="{reset_url}" style="color: #7c3aed;">{reset_url}</a></p>
        </div>
        """
        return self._send_email(user_email, subject, html)

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
