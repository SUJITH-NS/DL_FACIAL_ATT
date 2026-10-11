import unittest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth import hash_password, verify_password, register_student_account, register_staff_account
from database import get_student_by_id, get_staff_by_id

class TestAuthentication(unittest.TestCase):

    def test_password_hashing(self):
        password = "SecretPassword123"
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "WrongPassword"))

    def test_student_registration_validation(self):
        # Invalid email syntax
        success, msg = register_student_account("TEST001", "Test Student", "invalid_email", "pass", "CSE", 4, "C", "123")
        self.assertFalse(success)
        self.assertIn("email", msg.lower())

if __name__ == '__main__':
    unittest.main()
