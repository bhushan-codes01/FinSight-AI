import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add application directory to path
sys.path.insert(0, r"c:\Users\Bhushan\OneDrive\Desktop\finance tracker\AI-Personal-Finance-Tracker")

from app import app, get_db

class TestBilling(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Ensure database is set up
        with self.app.app_context():
            db = get_db()
            # Create a test user if not exists
            db.execute("INSERT OR IGNORE INTO users (id, name, email, password, plan) VALUES (999, 'Test User', 'billing_test@example.com', 'pwd123', 'free')")
            db.commit()

    def tearDown(self):
        with self.app.app_context():
            db = get_db()
            db.execute("DELETE FROM users WHERE id = 999")
            db.execute("DELETE FROM subscriptions WHERE user_id = 999")
            db.commit()

    def test_upgrade_requires_login(self):
        """Test that accessing /upgrade redirects to login when not logged in."""
        response = self.client.get('/upgrade')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_upgrade_page_loads_with_login(self):
        """Test that /upgrade page loads for a logged in user."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 999
            
        response = self.client.get('/upgrade')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Choose the Perfect Plan", response.data)

    @patch('razorpay.Client')
    def test_create_order_mock(self, mock_razorpay):
        """Test creating a mock order when placeholder keys are used."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 999
            
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_placeholder", "RAZORPAY_KEY_SECRET": "placeholder_secret"}):
            response = self.client.post('/billing/create-order', json={"billing_cycle": "monthly"})
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertTrue(data.get("is_mock"))
            self.assertTrue(data.get("order_id").startswith("order_mock_"))

    @patch('razorpay.Client')
    def test_create_order_real_api(self, mock_razorpay_client):
        """Test order creation triggers razorpay client order creation when using real keys."""
        mock_instance = MagicMock()
        mock_razorpay_client.return_value = mock_instance
        mock_instance.order.create.return_value = {"id": "order_test_12345"}

        with self.client.session_transaction() as sess:
            sess['user_id'] = 999

        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_real", "RAZORPAY_KEY_SECRET": "real_secret"}):
            response = self.client.post('/billing/create-order', json={"billing_cycle": "monthly"})
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertFalse(data.get("is_mock"))
            self.assertEqual(data.get("order_id"), "order_test_12345")
            mock_instance.order.create.assert_called_once()

    def test_verify_payment_success(self):
        """Test verification upgrades plan and logs subscription in database."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 999

        response = self.client.post('/billing/verify-payment', json={
            "razorpay_order_id": "order_mock_123",
            "razorpay_payment_id": "pay_mock_123",
            "razorpay_signature": "sig_mock_123",
            "billing_cycle": "monthly"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json.get("success"))
        
        # Verify db updates
        with self.app.app_context():
            db = get_db()
            user = db.execute("SELECT plan FROM users WHERE id = 999").fetchone()
            self.assertEqual(user['plan'], 'pro')
            
            sub = db.execute("SELECT * FROM subscriptions WHERE user_id = 999").fetchone()
            self.assertIsNotNone(sub)
            self.assertEqual(sub['razorpay_payment_id'], 'pay_mock_123')

if __name__ == '__main__':
    unittest.main()
