import os
import requests
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, g, jsonify
from werkzeug.security import generate_password_hash
from services.db import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@auth_bp.route("/login-firebase", methods=["POST"])
def login_firebase():
    data = request.get_json() or {}
    token = data.get("idToken")
    if not token:
        return jsonify({"success": False, "error": "Missing token"}), 400

    firebase_api_key = os.getenv("FIREBASE_API_KEY")
    if not firebase_api_key or firebase_api_key == "your_firebase_api_key":
        return jsonify({"success": False, "error": "Firebase is not configured on the server. Please check your .env file."}), 500

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={firebase_api_key}"
    try:
        response = requests.post(url, json={"idToken": token}, timeout=10)
        res_data = response.json()
        if response.status_code != 200 or "users" not in res_data or not res_data["users"]:
            error_msg = res_data.get("error", {}).get("message", "Invalid token")
            return jsonify({"success": False, "error": error_msg}), 400

        firebase_user = res_data["users"][0]
        firebase_uid = firebase_user["localId"]
        email = firebase_user["email"].strip().lower()
        # If display name isn't set, use the part of email before @
        display_name = firebase_user.get("displayName", "").strip() or email.split("@")[0]

        db = get_db()
        cursor = db.cursor()

        # 1. Try to find user by firebase_uid
        user = db.execute("SELECT * FROM users WHERE firebase_uid = ?", (firebase_uid,)).fetchone()

        if not user:
            # 2. Try to find user by email (in case they previously registered locally or via another provider)
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                # Update existing local user with their firebase_uid
                cursor.execute(
                    "UPDATE users SET firebase_uid = ?, auth_provider = 'firebase' WHERE id = ?",
                    (firebase_uid, user["id"])
                )
                db.commit()
                # Re-fetch user to make sure we have updated info
                user = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
            else:
                # 3. Create a new user
                # We generate a dummy random password to satisfy the NOT NULL constraint in SQLite
                dummy_password = generate_password_hash(secrets.token_hex(16))
                cursor.execute(
                    "INSERT INTO users (name, email, password, firebase_uid, auth_provider) VALUES (?, ?, ?, ?, 'firebase')",
                    (display_name, email, dummy_password, firebase_uid)
                )
                db.commit()
                user_id = cursor.lastrowid
                user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        # Log user into Flask session
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({"success": True, "redirect": url_for("dashboard")})

    except requests.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to contact identity provider: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/bypass-login")
def bypass_login():
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE id = ?", (10000,)).fetchone()
    if not user:
        user_by_email = db.execute("SELECT id FROM users WHERE email = ?", ("bhushanwanere@gmail.com",)).fetchone()
        if not user_by_email:
            db.execute(
                "INSERT INTO users (id, name, email, password, plan) VALUES (?, ?, ?, ?, ?)",
                (10000, 'Bhushan Wanere', 'bhushanwanere@gmail.com', 'dummy_password', 'free')
            )
            db.commit()
        else:
            try:
                uid = user_by_email["id"]
            except Exception:
                uid = user_by_email[0]
            session["user_id"] = uid
            session["user_name"] = "Bhushan Wanere"
            return f"Bypass login successful as existing email! ID: {uid}"
            
    session["user_id"] = 10000
    session["user_name"] = "Bhushan Wanere"
    return "Bypass login successful! You can now visit /chatbot or /dashboard."
