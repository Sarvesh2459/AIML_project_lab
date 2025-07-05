import jwt
from datetime import datetime
from functools import wraps
from flask import request, jsonify, session
from config import Config

class AuthService:
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def token_required(f):
        """Decorator to require valid token"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token.split(' ')[1]
            else:
                token = session.get('token')
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            payload = AuthService.verify_token(token)
            if not payload:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            request.current_user = payload
            return f(*args, **kwargs)
        
        return decorated

    @staticmethod
    def get_current_user():
        """Get current authenticated user from request"""
        return getattr(request, 'current_user', None)