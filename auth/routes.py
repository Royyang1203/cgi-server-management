from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from .ldap_client import ldap_authenticate

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if ldap_authenticate(username, password):
            session['user'] = username
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login')) 