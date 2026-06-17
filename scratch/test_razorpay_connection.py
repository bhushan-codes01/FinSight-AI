import os
import razorpay
from dotenv import load_dotenv

load_dotenv(".env")

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

print(f"Testing Razorpay keys...")
print(f"Key ID: {key_id}")
print(f"Key Secret: {'*' * len(key_secret) if key_secret else 'None'}")

try:
    client = razorpay.Client(auth=(key_id, key_secret))
    # Try listing orders to see if the authentication succeeds
    orders = client.order.all()
    print("SUCCESS: Connection to Razorpay was successful! The keys are valid.")
    print("Orders retrieved:", len(orders) if hasattr(orders, '__len__') else "unknown")
except Exception as e:
    print("FAILED: Failed to connect to Razorpay with the provided keys.")
    print("Error details:", e)
