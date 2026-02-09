from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, UTC
from models import db, User, LoginAttempt
from forms import LoginForm, CreateUserForm, ChangePasswordForm
import functools

auth = Blueprint('auth', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def log_login_attempt(username, success, ip_address):
    """Log login attempt for security monitoring"""
    attempt = LoginAttempt(
        username=username,
        success=success,
        ip_address=ip_address
    )
    db.session.add(attempt)
    db.session.commit()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        ip_address = get_remote_address()
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Successful login
            login_user(user, remember=False)
            user.last_login = datetime.now(UTC)
            db.session.commit()
            
            log_login_attempt(form.username.data, True, ip_address)
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            # Failed login
            log_login_attempt(form.username.data, False, ip_address)
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    session.clear()  # Clear all session data
    flash(f'You have been logged out, {username}.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} created successfully!', 'success')
            return redirect(url_for('main.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating user. Please try again.', 'error')
    
    return render_template('auth/create_user.html', form=form)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Current password is incorrect', 'error')
    
    return render_template('auth/change_password.html', form=form)

@auth.route('/deactivate_user/<int:user_id>')
@login_required
@admin_required
def deactivate_user(user_id):
    if user_id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('main.manage_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been deactivated', 'success')
    return redirect(url_for('main.manage_users'))

@auth.route('/activate_user/<int:user_id>')
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been activated', 'success')
    return redirect(url_for('main.manage_users'))

# Rate limiting decorator for login attempts
def setup_rate_limiting(limiter):
    """Setup rate limiting for authentication routes"""
    limiter.limit("5 per minute")(login)
    return limiter
