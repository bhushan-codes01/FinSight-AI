import os
import time
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, g, jsonify, flash
import razorpay
from services.db import get_db

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/upgrade")
def upgrade():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
        
    user_id = session["user_id"]
    db = get_db()
    
    # Get user's current plan info
    user = db.execute("SELECT plan, plan_expiry FROM users WHERE id = ?", (user_id,)).fetchone()
    current_plan = user["plan"] if user else "free"
    plan_expiry = user["plan_expiry"] if user else None
    
    # Format expiry date
    expiry_str = None
    if plan_expiry:
        try:
            if isinstance(plan_expiry, str):
                expiry_str = datetime.strptime(plan_expiry.split(" ")[0], "%Y-%m-%d").strftime("%B %d, %Y")
            elif hasattr(plan_expiry, 'strftime'):
                expiry_str = plan_expiry.strftime("%B %d, %Y")
            else:
                expiry_str = str(plan_expiry)
        except Exception:
            expiry_str = str(plan_expiry)
            
    # Check subscriptions table
    active_sub = db.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY started_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    
    return render_template(
        "upgrade.html", 
        current_plan=current_plan, 
        expiry_date=expiry_str, 
        active_sub=active_sub,
        razorpay_key_id=os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    )


@billing_bp.route("/billing/create-order", methods=["POST"])
def create_order():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = session["user_id"]
    json_data = request.get_json(silent=True) or {}
    billing_cycle = json_data.get("billing_cycle", "monthly")
    
    # Amounts in Paise (e.g. ₹199 -> 19900 paise, ₹1999 -> 199900 paise)
    if billing_cycle == "yearly":
        amount = 199900
    else:
        amount = 19900
        
    key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
    
    is_mock = "placeholder" in key_id or "placeholder" in key_secret
    
    if is_mock:
        mock_order_id = f"order_mock_{secrets.token_hex(8)}"
        return jsonify({
            "order_id": mock_order_id,
            "amount": amount,
            "key_id": key_id,
            "is_mock": True
        })
        
    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": f"receipt_{user_id}_{int(time.time())}"
        })
        return jsonify({
            "order_id": order["id"],
            "amount": amount,
            "key_id": key_id,
            "is_mock": False
        })
    except Exception as e:
        mock_order_id = f"order_mock_fallback_{secrets.token_hex(8)}"
        return jsonify({
            "order_id": mock_order_id,
            "amount": amount,
            "key_id": key_id,
            "is_mock": True,
            "warning": f"Razorpay API error: {e}. Falling back to mock order."
        })


@billing_bp.route("/billing/verify-payment", methods=["POST"])
def verify_payment():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = session["user_id"]
    json_data = request.get_json(silent=True) or {}
    
    payment_id = json_data.get("razorpay_payment_id")
    order_id = json_data.get("razorpay_order_id")
    signature = json_data.get("razorpay_signature")
    billing_cycle = json_data.get("billing_cycle", "monthly")
    
    if not order_id or not payment_id:
        return jsonify({"success": False, "error": "Missing payment details"}), 400
        
    key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
    
    is_valid = False
    
    # If using mock checkout or keys are placeholder
    if order_id.startswith("order_mock") or "placeholder" in key_id:
        is_valid = True
    else:
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            is_valid = True
        except Exception as e:
            current_app.logger.error(f"Razorpay signature verification failed: {e}")
            is_valid = False
            
    if is_valid:
        try:
            db = get_db()
            
            # Check if user exists (to handle cases where session persists but DB was reset/recreated)
            user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return jsonify({
                    "success": False, 
                    "error": "User session is invalid or the database was recently reset. Please logout and log back in to recreate your user account, then try again."
                }), 400
            
            # Calculate expiry date
            now = datetime.now()
            if billing_cycle == "yearly":
                expiry = now + timedelta(days=365)
            else:
                expiry = now + timedelta(days=30)
                
            expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
            
            # Update user plan
            db.execute(
                "UPDATE users SET plan = 'pro', plan_expiry = ? WHERE id = ?",
                (expiry.strftime("%Y-%m-%d"), user_id)
            )
            
            # Insert subscription record
            db.execute(
                "INSERT INTO subscriptions (user_id, plan, billing_cycle, razorpay_subscription_id, razorpay_payment_id, status, started_at, expires_at) "
                "VALUES (?, 'pro', ?, ?, ?, 'active', ?, ?)",
                (user_id, billing_cycle, order_id, payment_id, now.strftime("%Y-%m-%d %H:%M:%S"), expiry_str)
            )
            db.commit()
            
            # Send invoice email
            try:
                user = db.execute(
                    'SELECT name, email FROM users WHERE id = ?', 
                    (user_id,)
                ).fetchone()
                if user:
                    from services.email_service import send_invoice_email
                    send_invoice_email(
                        user_email=user['email'],
                        user_name=user['name'],
                        payment_id=payment_id,
                        amount=199 if billing_cycle == 'monthly' else 1999,
                        billing_cycle=billing_cycle,
                        expiry_date=expiry
                    )
            except Exception as email_err:
                current_app.logger.error(f"Failed to send invoice email: {email_err}")
            
            # Update user session details (optional but helpful)
            session["user_plan"] = "pro"
            
            return jsonify({"success": True, "message": "Successfully upgraded to Pro!"})
        except Exception as e:
            current_app.logger.error(f"Database update failed during payment verification: {e}")
            return jsonify({"success": False, "error": f"Database update failed: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "error": "Invalid signature or payment verification failed"}), 400


@billing_bp.route("/billing/history")
def billing_history():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
        
    user_id = session["user_id"]
    db = get_db()
    
    # Fetch subscriptions history
    subs = db.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY started_at DESC",
        (user_id,)
    ).fetchall()
    
    return render_template("billing_history.html", subscriptions=subs)


@billing_bp.route("/billing/cancel", methods=["POST"])
def cancel_subscription():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
        
    user_id = session["user_id"]
    db = get_db()
    
    # Update active subscriptions status to cancelled
    db.execute(
        "UPDATE subscriptions SET status = 'cancelled' WHERE user_id = ? AND status = 'active'",
        (user_id,)
    )
    db.commit()
    
    flash("Subscription cancelled. You will continue to have access to Pro features until your expiry date.", "info")
    return redirect(url_for("billing.billing_history"))
