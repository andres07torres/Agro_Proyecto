from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, limiter
from ..models import User, DatasetHistory

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not nombre or not email or not password:
            flash('Por favor completa todos los campos.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('auth.register'))

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(nombre=nombre, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Credenciales incorrectas.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect(url_for('site.dashboard')) # Assuming dashboard is in 'site' BP

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('site.inicio'))

# API Profile routes moved to auth
@auth_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')

    if email != current_user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'exito': False, 'error': 'El correo ya está en uso'}), 400
    
    current_user.nombre = nombre
    current_user.email = email
    db.session.commit()
    return jsonify({'exito': True})

@auth_bp.route('/api/profile/password', methods=['POST'])
@login_required
def update_password():
    data = request.json
    current_pass = data.get('current_password')
    new_pass = data.get('new_password')

    if not check_password_hash(current_user.password, current_pass):
        return jsonify({'exito': False, 'error': 'La contraseña actual es incorrecta'}), 400

    current_user.password = generate_password_hash(new_pass, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'exito': True})

@auth_bp.route('/api/profile/2fa', methods=['POST'])
@login_required
def toggle_2fa():
    current_user.two_factor_enabled = not current_user.two_factor_enabled
    db.session.commit()
    return jsonify({'exito': True, 'two_factor_enabled': current_user.two_factor_enabled})

@auth_bp.route('/api/profile/delete', methods=['DELETE'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    DatasetHistory.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return jsonify({'exito': True})
