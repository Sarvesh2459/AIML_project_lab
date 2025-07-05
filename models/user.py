import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from config import Config

class User:
    def __init__(self, name, account_number, balance, auth_code):
        self.name = name
        self.account_number = account_number
        self.balance = float(balance)
        self.auth_code_hash = self._hash_auth_code(auth_code)
        self.created_at = datetime.utcnow()
        self.last_login = None
        self.is_active = True

    def _hash_auth_code(self, auth_code):
        """Hash the authentication code for secure storage"""
        return bcrypt.hashpw(auth_code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_auth_code(self, auth_code):
        """Verify the provided auth code against the stored hash"""
        return bcrypt.checkpw(auth_code.encode('utf-8'), self.auth_code_hash.encode('utf-8'))

    def generate_token(self):
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': self.account_number,
            'name': self.name,
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION_DELTA),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

    def update_balance(self, amount):
        """Update user balance with validation"""
        if self.balance + amount < 0:
            raise ValueError("Insufficient funds")
        self.balance += amount

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'name': self.name,
            'account_number': self.account_number,
            'balance': self.balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data):
        """Create user object from dictionary"""
        user = cls(
            data['name'],
            data['account_number'],
            data['balance'],
            ''  # Empty auth code since we store the hash
        )
        user.auth_code_hash = data.get('auth_code_hash', '')
        user.created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow()
        user.last_login = datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        user.is_active = data.get('is_active', True)
        return user