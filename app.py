import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import config
from models import db, User
from auth import auth, setup_rate_limiting
from routes import main

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup CSRF Protection
    csrf = CSRFProtect(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Setup rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)
    setup_rate_limiting(limiter)
    
    # Register blueprints
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main)
    
    # Currency template filter
    @app.template_filter('currency')
    def currency_filter(amount):
        """Format amount as currency with configured symbol and no decimals"""
        if amount is None:
            amount = 0
        return app.config['CURRENCY_FORMAT'].format(
            symbol=app.config['CURRENCY_SYMBOL'],
            amount=float(amount)
        )
    
    # Make currency config available to all templates
    @app.context_processor
    def inject_currency_config():
        return {
            'CURRENCY_SYMBOL': app.config['CURRENCY_SYMBOL'],
            'CURRENCY_CODE': app.config['CURRENCY_CODE']
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html'), 429
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Create database tables (but don't initialize data automatically)
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Development server settings
    port = int(os.environ.get('PORT', 5000))
    # debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("🔐 Secure Order Management System")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port)
