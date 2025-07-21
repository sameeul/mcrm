import os
from datetime import timedelta

class Config:
    # Security Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///order_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 30 minute timeout
    SESSION_COOKIE_SECURE = True  # Set to False for development without HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Application Settings
    ITEMS_PER_PAGE = 20
    
    # Currency Configuration
    CURRENCY_SYMBOL = '৳'
    CURRENCY_FORMAT = '{symbol}{amount:.0f}'  # ৳150 (no decimals)
    CURRENCY_CODE = 'BDT'
    
    # Pathao API Configuration
    PATHAO_BASE_URL = os.environ.get('PATHAO_BASE_URL')
    PATHAO_CLIENT_ID = os.environ.get('PATHAO_CLIENT_ID')
    PATHAO_CLIENT_SECRET = os.environ.get('PATHAO_CLIENT_SECRET')
    PATHAO_USERNAME = os.environ.get('PATHAO_USERNAME')
    PATHAO_PASSWORD = os.environ.get('PATHAO_PASSWORD')
    PATHAO_GRANT_TYPE = os.environ.get('PATHAO_GRANT_TYPE')
    CACHE_DURATION_HOURS = 24  # Cache location data for 24 hours

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
