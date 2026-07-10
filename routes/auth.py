"""Auth routes: login, logout, change password."""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.db import verify_admin
import re

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to protect routes from unauthenticated access."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session:
        return redirect(url_for('dashboard.index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Basic input validation
        if not username or not password:
            error = 'Username and password are required.'
        elif len(username) > 64 or len(password) > 128:
            error = 'Invalid input length.'
        else:
            admin = verify_admin(username, password)
            if admin:
                session.permanent = True
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session['admin_role'] = admin['role']
                flash(f'Welcome back, {admin["username"]}!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
