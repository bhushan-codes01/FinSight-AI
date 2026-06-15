import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__)

# Initialize Authlib OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Enable insecure transport for development/local testing
if os.getenv("AUTHLIB_INSECURE_TRANSPORT") is None:
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@auth_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# Token Helpers
def generate_and_save_token(db, user_id, token_type, hours=24):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps({"user_id": user_id, "type": token_type, "created": datetime.now().isoformat()}, salt="auth-salt")
    expires_at = datetime.now() + timedelta(hours=hours)
    
    db.execute(
        "INSERT INTO auth_tokens (user_id, token, token_type, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, token, token_type, expires_at.strftime("%Y-%m-%d %H:%M:%S"))
    )
    db.commit()
    return token


def verify_and_consume_token(db, token, expected_type):
    # Verify signature
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = serializer.loads(token, salt="auth-salt")
    except Exception:
        return None
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = db.execute(
        "SELECT * FROM auth_tokens WHERE token = ? AND token_type = ? AND used = 0 AND expires_at > ?",
        (token, expected_type, now_str)
    ).fetchone()
    
    if row:
        db.execute("UPDATE auth_tokens SET used = 1 WHERE id = ?", (row["id"],))
        db.commit()
        return row["user_id"]
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not name or not email or not password:
            flash("Please complete all required fields.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        db = get_db()
        cursor = db.cursor()
        try:
            # Create user with email_verified = 0, plan = 'free'
            cursor.execute(
                "INSERT INTO users (name, email, password, email_verified, plan) VALUES (?, ?, ?, 0, 'free')",
                (name, email, hashed_password),
            )
            db.commit()
            user_id = cursor.lastrowid
            
            # Generate verification token
            token = generate_and_save_token(db, user_id, 'email_verify', hours=24)
            
            # Send verification email using current_app.email_service
            if hasattr(current_app, 'email_service') and current_app.email_service:
                current_app.email_service.send_verification_email(email, token)
            
            return render_template("verify-email-sent.html", email=email)
        except sqlite3.IntegrityError:
            flash("This email is already registered.", "danger")
            return render_template("register.html")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# Google Sign-In Routes
@auth_bp.route("/auth/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        user_info = oauth.google.parse_id_token(token)
    
    email = user_info.get('email').strip().lower()
    google_id = user_info.get('sub')
    name = user_info.get('name')
    picture = user_info.get('picture')

    db = get_db()
    # Check if Google user exists
    user = db.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash("Logged in with Google successfully.", "success")
        return redirect(url_for("dashboard"))
    
    # Check if user with this email already exists
    user_by_email = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user_by_email:
        # Account linking: link google_id to existing account
        db.execute(
            "UPDATE users SET google_id = ?, auth_provider = 'google', profile_picture = ?, email_verified = 1 WHERE id = ?",
            (google_id, picture, user_by_email["id"])
        )
        db.commit()
        session["user_id"] = user_by_email["id"]
        session["user_name"] = user_by_email["name"]
        flash("Linked your Google account and logged in successfully.", "success")
        return redirect(url_for("dashboard"))
    
    # Create new Google user
    dummy_password = generate_password_hash(secrets.token_hex(16))
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password, google_id, auth_provider, profile_picture, email_verified, plan) VALUES (?, ?, ?, ?, 'google', ?, 1, 'free')",
        (name, email, dummy_password, google_id, picture)
    )
    db.commit()
    new_user_id = cursor.lastrowid
    
    session["user_id"] = new_user_id
    session["user_name"] = name
    flash("Registered and logged in with Google successfully.", "success")
    return redirect(url_for("dashboard"))


# Email Verification Link Callback Route
@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    db = get_db()
    user_id = verify_and_consume_token(db, token, 'email_verify')
    
    if user_id:
        db.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
        db.commit()
        flash("Email verified successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    else:
        flash("The verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))


# Resend Verification Route
@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
        
    user_id = session["user_id"]
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user and not user["email_verified"]:
        # Generate new verification token
        token = generate_and_save_token(db, user_id, 'email_verify', hours=24)
        
        # Send verification email
        if hasattr(current_app, 'email_service') and current_app.email_service:
            current_app.email_service.send_verification_email(user["email"], token)
            
        flash("Verification email resent. Please check your inbox.", "info")
    else:
        flash("Your email is already verified.", "warning")
        
    return redirect(url_for("dashboard"))


# Forgot Password Flow Routes
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        
        # Security: Do not reveal if the email exists in the DB or not
        flash("If that email exists, we've sent a reset link to it.", "info")
        
        if user:
            # Generate reset token (expires in 1 hour)
            token = generate_and_save_token(db, user["id"], 'password_reset', hours=1)
            
            # Send password reset email
            if hasattr(current_app, 'email_service') and current_app.email_service:
                current_app.email_service.send_password_reset_email(email, token)
                
        return redirect(url_for("auth.login"))
        
    return render_template("forgot-password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    db = get_db()
    # Decode token to verify signature first
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = serializer.loads(token, salt="auth-salt")
        user_id = data.get("user_id")
    except Exception:
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))
        
    # Check token in database (without marking it used yet, so GET doesn't consume it)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = db.execute(
        "SELECT * FROM auth_tokens WHERE token = ? AND token_type = 'password_reset' AND used = 0 AND expires_at > ?",
        (token, now_str)
    ).fetchone()
    
    if not row:
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        if not password:
            flash("Password cannot be empty.", "danger")
            return render_template("reset-password.html", token=token)
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("reset-password.html", token=token)
            
        # Hash new password and update user
        hashed_password = generate_password_hash(password)
        db.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
        
        # Mark token used
        db.execute("UPDATE auth_tokens SET used = 1 WHERE id = ?", (row["id"],))
        db.commit()
        
        flash("Your password has been reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))
        
    return render_template("reset-password.html", token=token)
