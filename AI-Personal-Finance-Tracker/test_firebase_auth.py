import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add application directory to path
sys.path.insert(0, r"c:\Users\Bhushan\OneDrive\Desktop\finance tracker\AI-Personal-Finance-Tracker")

from app import app, get_db

class TestFirebaseAuth(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_context_processor_injects_config(self):
        """Test that firebase_config is injected into templates context."""
        with self.app.test_request_context():
            # Trigger template context processors in Flask
            context = {}
            for processor in self.app.template_context_processors[None]:
                context.update(processor())
            self.assertIn('firebase_config', context)
            cfg = context['firebase_config']
            self.assertIn('apiKey', cfg)
            self.assertIn('authDomain', cfg)
            self.assertIn('projectId', cfg)

    @patch('requests.post')
    def test_login_firebase_missing_token(self, mock_post):
        """Test login-firebase returns 400 when token is missing."""
        response = self.client.post('/login-firebase', json={})
        print("MISSING TOKEN RESPONSE:", response.status_code, response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing token", response.data)

    @patch('requests.post')
    def test_login_firebase_invalid_token(self, mock_post):
        """Test login-firebase returns 400 when identity toolkit returns error."""
        # Mock failure response from Google Identity Toolkit
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "INVALID_ID_TOKEN"
            }
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"FIREBASE_API_KEY": "dummy_api_key"}):
            response = self.client.post('/login-firebase', json={"idToken": "fake_token"})
            print("INVALID TOKEN RESPONSE:", response.status_code, response.data)
            self.assertEqual(response.status_code, 400)
            self.assertIn(b"INVALID_ID_TOKEN", response.data)

    @patch('requests.post')
    def test_login_firebase_success_new_user(self, mock_post):
        """Test successful registration and session creation for a new Firebase user."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [{
                "localId": "test_firebase_uid_123",
                "email": "firebase_new_user@example.com",
                "displayName": "Firebase New User"
            }]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"FIREBASE_API_KEY": "dummy_api_key"}):
            import sqlite3 as sqlite
            conn = sqlite.connect(self.app.config["DATABASE"])
            conn.row_factory = sqlite.Row
            
            # Clean up existing test user if any
            conn.execute("DELETE FROM users WHERE email = ?", ("firebase_new_user@example.com",))
            conn.commit()

            response = self.client.post('/login-firebase', json={"idToken": "valid_token_123"})
            print("SUCCESS NEW USER RESPONSE:", response.status_code, response.data)
            self.assertEqual(response.status_code, 200)
            data = response.json
            self.assertTrue(data["success"])
            self.assertEqual(data["redirect"], "/dashboard")

            # Verify user was created in local database
            user = conn.execute("SELECT * FROM users WHERE email = ?", ("firebase_new_user@example.com",)).fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user["firebase_uid"], "test_firebase_uid_123")
            self.assertEqual(user["auth_provider"], "firebase")

            # Clean up
            conn.execute("DELETE FROM users WHERE email = ?", ("firebase_new_user@example.com",))
            conn.commit()
            conn.close()

if __name__ == '__main__':
    unittest.main()
