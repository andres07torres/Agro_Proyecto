from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import DatasetHistory

main_bp = Blueprint('site', __name__) # Using 'site' as the name to match previous auth redirects

@main_bp.route('/')
def index():
    return render_template('Inicio.html')

@main_bp.route('/inicio')
def inicio():
    return render_template('Inicio.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('Dashboard.html')

@main_bp.route('/tendencias')
@login_required
def tendencias():
    return render_template('tendencias.html')

@main_bp.route('/carga-datos')
@login_required
def carga_datos():
    historial = DatasetHistory.query.filter_by(user_id=current_user.id).order_by(DatasetHistory.fecha.desc()).all()
    return render_template('carga_datos.html', historial=historial)

@main_bp.route('/configuracion')
@login_required
def configuracion():
    return render_template('configuracion.html')
