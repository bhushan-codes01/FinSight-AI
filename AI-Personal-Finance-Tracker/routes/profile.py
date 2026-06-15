import os
import sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint("profile", __name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@profile_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@profile_bp.route("/profile", methods=["GET"])
def view_profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    # Get user details
    user = db.execute(
        "SELECT name, email, plan, plan_expiry, email_verified, currency, currency_symbol, profile_picture, auth_provider, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))

    # Get statistics
    total_tx = db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)).fetchone()[0]
    total_income = (
        db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND transaction_type = 'income'", (user_id,)).fetchone()[0]
        or 0.0
    )
    total_expense = (
        db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND transaction_type = 'expense'", (user_id,)).fetchone()[0]
        or 0.0
    )
    total_goals = db.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,)).fetchone()[0]
    total_chats = db.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,)).fetchone()[0]

    # Predefined avatar options (under static/images/avatars/)
    predefined_avatars = [
        "avatar_1.png",
        "avatar_2.png",
        "avatar_3.png",
        "avatar_4.png",
        "avatar_5.png",
        "avatar_6.png",
    ]

    return render_template(
        "profile.html",
        user=user,
        stats={
            "total_transactions": total_tx,
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_goals": total_goals,
            "total_chats": total_chats,
        },
        predefined_avatars=predefined_avatars,
    )


@profile_bp.route("/profile/update", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    name = request.form.get("name", "").strip()
    avatar_choice = request.form.get("avatar_choice", "").strip()

    if not name:
        flash("Name cannot be empty.", "danger")
        return redirect(url_for("profile.view_profile"))

    db = get_db()

    # Update Name
    db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    session["user_name"] = name

    # Handle predefined avatar selection
    if avatar_choice:
        valid_avatars = [f"avatar_{i}.png" for i in range(1, 7)]
        if avatar_choice in valid_avatars:
            profile_pic_path = f"/static/images/avatars/{avatar_choice}"
            db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", (profile_pic_path, user_id))

    # Handle file upload
    if "profile_picture_file" in request.files:
        file = request.files["profile_picture_file"]
        if file and file.filename != "":
            # Validate extension
            allowed_extensions = {"png", "jpg", "jpeg", "gif"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_extensions:
                flash("Invalid image format. Supported formats: PNG, JPG, JPEG, GIF.", "danger")
                return redirect(url_for("profile.view_profile"))

            # Validate size (limit to 2MB)
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            if file_length > 2 * 1024 * 1024:
                flash("Image file size exceeds the 2MB limit.", "danger")
                return redirect(url_for("profile.view_profile"))
            file.seek(0)

            # Save file
            filename = f"user_{user_id}_{int(datetime.now().timestamp())}.{ext}"
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "avatars")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            # Save file path to DB
            profile_pic_path = f"/static/uploads/avatars/{filename}"
            db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", (profile_pic_path, user_id))

    db.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/profile/remove-avatar", methods=["POST"])
def remove_avatar():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()
    db.execute("UPDATE users SET profile_picture = NULL WHERE id = ?", (user_id,))
    db.commit()

    flash("Profile picture reset to default.", "success")
    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/profile/change-password", methods=["POST"])
def change_password():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    db = get_db()

    # Check if user is a standard local login user
    user = db.execute("SELECT password, auth_provider FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user["auth_provider"] != "local":
        flash("Password cannot be updated for external accounts.", "danger")
        return redirect(url_for("profile.view_profile"))

    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    confirm_new_password = request.form.get("confirm_new_password", "")

    if not old_password or not new_password or not confirm_new_password:
        flash("Please complete all password fields.", "danger")
        return redirect(url_for("profile.view_profile"))

    if not check_password_hash(user["password"], old_password):
        flash("Incorrect old password.", "danger")
        return redirect(url_for("profile.view_profile"))

    if new_password != confirm_new_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile.view_profile"))

    hashed_password = generate_password_hash(new_password)
    db.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    db.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("profile.view_profile"))
