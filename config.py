import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///banking.db'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    
    # JWT settings
    JWT_EXPIRATION_DELTA = 3600  # 1 hour
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'