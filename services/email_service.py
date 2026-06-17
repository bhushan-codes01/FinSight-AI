import os
from flask_mail import Mail, Message
from flask import current_app


class EmailAlertsService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        # Retrieve the mail instance already configured on app, or initialize if missing
        self.mail = getattr(app, 'mail', None)
        if not self.mail:
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
            email_pass = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS") or ""
            app.config["MAIL_PASSWORD"] = email_pass.replace(' ', '')
            app.config["MAIL_DEFAULT_SENDER"] = os.getenv("EMAIL_USER")
            self.mail = Mail(app)
            app.mail = self.mail

    def send_budget_warning(self, user_email, user_name, category, spent, budget, currency_symbol="₹"):
        return send_budget_warning(user_email, user_name, category, spent, budget, currency_symbol)

    def send_budget_exceeded(self, user_email, user_name, category, spent, budget, currency_symbol="₹"):
        return send_budget_exceeded(user_email, user_name, category, spent, budget, currency_symbol)

    def send_report_ready(self, user_email, user_name, month_year):
        return send_report_ready(user_email, user_name, month_year)

    def send_unusual_spending_alert(self, user_email, user_name, amount, category, currency_symbol="₹"):
        return send_unusual_spending_alert(user_email, user_name, amount, category, currency_symbol)

    def send_upcoming_recurring_reminder(self, user_email, user_name, description, amount, due_date, currency_symbol="₹"):
        return send_upcoming_recurring_reminder(user_email, user_name, description, amount, due_date, currency_symbol)

    def send_verification_email(self, user_email, token):
        return send_verification_email(user_email, token)

    def send_password_reset_email(self, user_email, token):
        return send_password_reset_email(user_email, token)


# Standalone email functions to support absolute imports in test routes and routes
def send_verification_email(user_email, token):
    from flask import current_app, url_for
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")
            
        try:
            verify_url = url_for('auth.verify_email', token=token, _external=True)
        except Exception:
            verify_url = f"http://localhost:5000/verify-email/{token}"
        msg = Message(
            subject="Verify your FinSight AI account",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                    <h2 style="color: #7c3aed;">Welcome to FinSight AI 🎉</h2>
                    <p>Click the button below to verify your email address:</p>
                    <a href="{verify_url}" style="display: inline-block; padding: 12px 24px; 
                       background: linear-gradient(135deg, #7c3aed, #2563eb); color: white; 
                       text-decoration: none; border-radius: 8px; margin: 16px 0;">
                       Verify Email
                    </a>
                    <p style="color: #666; font-size: 14px;">This link expires in 24 hours.</p>
                </div>
            """
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Verification email sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send verification email to {user_email}: {str(e)}", flush=True)
        return False


def send_password_reset_email(user_email, token):
    from flask import current_app, url_for
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        try:
                reset_url = url_for('auth.reset_password', token=token, _external=True)
        except Exception:
                reset_url = f"http://localhost:5000/reset-password/{token}"
        msg = Message(
            subject="Reset your FinSight AI password",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                    <h2 style="color: #7c3aed;">Reset Your Password 🔒</h2>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; 
                       background: linear-gradient(135deg, #7c3aed, #2563eb); color: white; 
                       text-decoration: none; border-radius: 8px; margin: 16px 0;">
                       Reset Password
                    </a>
                    <p style="color: #666; font-size: 14px;">This link expires in 1 hour.</p>
                </div>
            """
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Password reset email sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send password reset email to {user_email}: {str(e)}", flush=True)
        return False


def send_budget_warning(user_email, user_name, category, spent, budget, currency_symbol="₹"):
    from flask import current_app
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        subject = f"⚠️ Budget Alert: {category} is {(spent/budget*100):.0f}% used"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>Your <strong>{category}</strong> budget is <strong>{(spent/budget*100):.0f}%</strong> used!</p>
        <p>Spent: {currency_symbol}{spent:,.0f} of {currency_symbol}{budget:,.0f}</p>
        <p>Remaining: {currency_symbol}{budget-spent:,.0f}</p>
        <p><a href="https://financeai.app/budgets" style="background: #7c3aed; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Budgets</a></p>
        """
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=html
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Budget warning email sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send budget warning email to {user_email}: {str(e)}", flush=True)
        return False


def send_budget_exceeded(user_email, user_name, category, spent, budget, currency_symbol="₹"):
    from flask import current_app
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        subject = f"🔴 Budget Exceeded: {category}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>You've exceeded your <strong>{category}</strong> budget!</p>
        <p>Spent: {currency_symbol}{spent:,.0f}</p>
        <p>Budget: {currency_symbol}{budget:,.0f}</p>
        <p>Overspent by: {currency_symbol}{spent-budget:,.0f}</p>
        <p><a href="https://financeai.app/transactions" style="background: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Transactions</a></p>
        """
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=html
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Budget exceeded email sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send budget exceeded email to {user_email}: {str(e)}", flush=True)
        return False


def send_unusual_spending_alert(user_email, user_name, amount, category, currency_symbol="₹"):
    from flask import current_app
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        subject = f"💡 Unusual Spending Detected"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>We detected an unusual transaction in your account:</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Amount:</strong> {currency_symbol}{amount:,.0f}</p>
        <p>This amount is significantly higher than your typical {category} spending.</p>
        <p><a href="https://financeai.app/transactions" style="background: #f59e0b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Review Transactions</a></p>
        """
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=html
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Unusual spending alert sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send unusual spending alert to {user_email}: {str(e)}", flush=True)
        return False


def send_upcoming_recurring_reminder(user_email, user_name, description, amount, due_date, currency_symbol="₹"):
    from flask import current_app
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        subject = f"📅 Upcoming Expense: {description}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>You have an upcoming recurring expense:</p>
        <p><strong>Description:</strong> {description}</p>
        <p><strong>Amount:</strong> {currency_symbol}{amount:,.0f}</p>
        <p><strong>Due:</strong> {due_date}</p>
        <p>Make sure you have enough balance in your account.</p>
        <p><a href="https://financeai.app/transactions" style="background: #06b6d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Details</a></p>
        """
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=html
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Upcoming recurring reminder sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send upcoming recurring reminder email to {user_email}: {str(e)}", flush=True)
        return False


def send_report_ready(user_email, user_name, month_year):
    from flask import current_app
    from flask_mail import Message
    try:
        mail = current_app.extensions.get('mail') or getattr(current_app, 'mail', None)
        if not mail:
            raise RuntimeError("Flask-Mail extension not initialized on current_app")

        subject = f"📊 Your Monthly Report is Ready - {month_year}"
        html = f"""
        <h2>Hi {user_name},</h2>
        <p>Your financial report for <strong>{month_year}</strong> is ready to download!</p>
        <p>Get insights into your spending, savings, and recommendations from AI.</p>
        <p><a href="https://financeai.app/reports" style="background: #7c3aed; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Download Report</a></p>
        """
        msg = Message(
            subject=subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email],
            html=html
        )
        mail.send(msg)
        print(f"[EMAIL SUCCESS] Report ready email sent to {user_email}", flush=True)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send report ready email to {user_email}: {str(e)}", flush=True)
        return False
