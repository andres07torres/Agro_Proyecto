import os
import xarray as xr
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from datetime import datetime
from whitenoise import WhiteNoise

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# Configuración robusta para Render/SQLAlchemy
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///agro_visor_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Seguridad: CSRF y Rate Limiting
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Carpeta de subida
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MODELO DE USUARIO
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), default='Analista')
    two_factor_enabled = db.Column(db.Boolean, default=False)

class DatasetHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    size_mb = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default='Listo')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- RUTAS DE NAVEGACION ---
@app.route('/')
def index():
    return render_template('Inicio.html')

@app.route('/inicio')
def inicio():
    return render_template('Inicio.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('Dashboard.html')

@app.route('/tendencias')
@login_required
def tendencias():
    return render_template('tendencias.html')

@app.route('/carga-datos')
@login_required
def carga_datos():
    historial = DatasetHistory.query.filter_by(user_id=current_user.id).order_by(DatasetHistory.fecha.desc()).all()
    return render_template('carga_datos.html', historial=historial)

@app.route('/configuracion')
@login_required
def configuracion():
    return render_template('configuracion.html')

# --- RUTAS DE AUTENTICACION ---
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not nombre or not email or not password:
            flash('Por favor completa todos los campos.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('register'))

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(nombre=nombre, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Credenciales incorrectas.', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('inicio'))

# --- CONFIGURACIONES (API) ---
@app.route('/api/profile/update', methods=['POST'])
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

@app.route('/api/profile/password', methods=['POST'])
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

@app.route('/api/profile/2fa', methods=['POST'])
@login_required
def toggle_2fa():
    current_user.two_factor_enabled = not current_user.two_factor_enabled
    db.session.commit()
    return jsonify({'exito': True, 'two_factor_enabled': current_user.two_factor_enabled})

@app.route('/api/profile/delete', methods=['DELETE'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    # Delete related history first to avoid FK constraint errors
    DatasetHistory.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    logout_user()
    return jsonify({'exito': True})

# --- PROCESAMIENTO DE DATOS ---
@app.route('/procesar_netcdf', methods=['POST'])
@login_required
def procesar_netcdf():
    if 'archivo_nc' not in request.files:
        return jsonify({'error': 'No se envió el archivo'}), 400
    
    file = request.files['archivo_nc']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            ds = xr.open_dataset(filepath)
            var_name = list(ds.data_vars)[0] 
            data_array = ds[var_name]

            dims_to_reduce = [d for d in data_array.dims if d in ['lat', 'lon', 'latitude', 'longitude']]
            series = data_array.mean(dim=dims_to_reduce) if dims_to_reduce else data_array

            resultados = procesar_serie(series)
            ds.close()

            # Record in Database History
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            new_record = DatasetHistory(
                user_id=current_user.id,
                filename=filename,
                size_mb=round(file_size_mb, 2),
                estado='Listo'
            )
            db.session.add(new_record)
            db.session.commit()

            return jsonify({
                'exito': True, 
                'variable': var_name,
                'filename': filename, 
                'datos': resultados,
                'tipo': 'Promedio de toda la zona',
                'record_fecha': new_record.fecha.strftime('%d %b %Y')
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/consultar_punto', methods=['POST'])
@login_required
def consultar_punto():
    data = request.json
    filename = data.get('filename')
    try:
        lat, lon = float(data.get('lat')), float(data.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'error': "Coordenadas inválidas"}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        ds = xr.open_dataset(filepath)
        var_name = list(ds.data_vars)[0]
        data_array = ds[var_name]

        lat_name = 'lat' if 'lat' in ds.coords else 'latitude' if 'latitude' in ds.coords else None
        lon_name = 'lon' if 'lon' in ds.coords else 'longitude' if 'longitude' in ds.coords else None

        if not lat_name or not lon_name:
            return jsonify({'error': "Coordenadas no encontradas"}), 500

        lon_ajustada = lon + 360 if ds.coords[lon_name].max() > 180 and lon < 0 else lon
        punto = data_array.sel(**{lat_name: lat, lon_name: lon_ajustada, 'method': 'nearest'})
        resultados = procesar_serie(punto)
        ds.close()

        return jsonify({'exito': True, 'variable': var_name, 'datos': resultados, 'coords': f"Lat: {round(lat, 3)}, Lon: {round(lon, 3)}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_trends/<filename>')
@login_required
def get_trends(filename):
    print(f"--- [ANALISIS] Procesando tendencias: {filename} ---")
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    lat_val = request.args.get('lat', type=float)
    lon_val = request.args.get('lon', type=float)
    
    try:
        ds = xr.open_dataset(filepath)
        var_name = list(ds.data_vars)[0]
        data_array = ds[var_name]
        
        # --- FILTRO GEOGRÁFICO POR PUNTO O REGIÓN ---
        if lat_val is not None and lon_val is not None:
            # Análisis de Punto (Sincronizado)
            # Manejamos posibles discrepancias en nombres de dimensiones (lat/latitude)
            sel_dict = {}
            if 'lat' in data_array.dims: sel_dict['lat'] = lat_val
            elif 'latitude' in data_array.dims: sel_dict['latitude'] = lat_val
            
            if 'lon' in data_array.dims: sel_dict['lon'] = lon_val
            elif 'longitude' in data_array.dims: sel_dict['longitude'] = lon_val
            
            series = data_array.sel(**sel_dict, method='nearest')
            ubicacion = f"Lat: {round(lat_val, 3)}, Lon: {round(lon_val, 3)}"
        else:
            # Promedio Regional
            dims_to_reduce = [d for d in data_array.dims if d in ['lat', 'lon', 'latitude', 'longitude']]
            series = data_array.mean(dim=dims_to_reduce) if dims_to_reduce else data_array
            ubicacion = "Resumen Regional"
        
        # Convertimos a DataFrame
        df = series.to_dataframe(name='valor').reset_index()
        df['fecha'] = pd.to_datetime(df['time'])
        df['mes'] = df['fecha'].dt.month
        df['anio'] = df['fecha'].dt.year
        
        # --- FILTRO HISTÓRICO INTELIGENTE ---
        # Priorizamos 1989-2014, pero si el archivo tiene un rango diferente (ej 1980), lo usamos.
        anio_min = df['anio'].min()
        rango_inicio = max(anio_min, 1989) if anio_min <= 1989 else anio_min
        
        df = df[df['anio'] >= 1980] # Límite base razonable para "histórico"
        
        if df.empty:
            return jsonify({'exito': False, 'error': f'El archivo no contiene datos históricos válidos (Min encontrado: {anio_min})'})

        # Ciclo Estacional (Basado en todo el rango disponible del archivo >= 1980)
        ciclo_raw = df.groupby('mes')['valor'].mean().round(2).to_dict()
        ciclo_final = [float(ciclo_raw.get(m, 0)) for m in range(1, 13)]
        
        # Distribución Anual por Meses
        anual_dist = {}
        for anio, g in df.groupby('anio'):
            m_raw = g.groupby('mes')['valor'].mean().round(2).to_dict()
            anual_dist[str(anio)] = [float(m_raw.get(m, 0)) for m in range(1, 13)]
        
        # Comparativa Anual (Línea)
        anual_raw = df.groupby('anio')['valor'].mean().round(2).sort_index().to_dict()
        anual_labels = [str(a) for a in anual_raw.keys()]
        anual_values = [float(v) for v in anual_raw.values()]
        
        # Estadísticas
        idx_max = df['valor'].idxmax()
        max_row = df.loc[idx_max]
        max_valor = float(max_row['valor'])
        max_fecha = max_row['fecha'].strftime('%B %Y')
        promedio_total = float(df['valor'].mean())
        
        # Anomalía (Último disponible vs promedio)
        ultimo_anio = anual_values[-1] if anual_values else 0
        anomalia = ultimo_anio - promedio_total

        # --- INTELIGENCIA ANALÍTICA: ESTABILIDAD Y RECOMENDACIÓN ---
        std_val = float(df['valor'].std())
        cv = std_val / promedio_total if promedio_total > 0 else 0
        estabilidad = "Alta" if cv < 0.25 else ("Moderada" if cv < 0.5 else "Baja")
        
        # Generar Recomendación Agronómica Dinámica
        if anomalia > (0.15 * promedio_total):
            rec_text = "Se observa un excedente hídrico significativo. Se recomienda optimizar sistemas de drenaje y monitorear riesgos de escorrentía para proteger los horizontes fértiles del suelo."
        elif anomalia < (-0.15 * promedio_total):
            rec_text = "Déficit hídrico detectado respecto al histórico. Se sugiere priorizar el riego suplementario y el uso de coberturas orgánicas (mulching) para minimizar la evapotranspiración."
        else:
            rec_text = "Condiciones hídricas dentro de los rangos históricos normales. Mantener las prácticas culturales programadas y el calendario de fertilización estándar."
        
        ds.close()
        
        return jsonify({
            'exito': True,
            'ubicacion': ubicacion,
            'ciclo_labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'ciclo_values': ciclo_final,
            'anual_dist': anual_dist,
            'anual_labels': anual_labels,
            'anual_values': anual_values,
            'max_precip': round(max_valor, 2),
            'max_fecha': max_fecha,
            'promedio_total': round(promedio_total, 2),
            'anomalia': round(anomalia, 2),
            'estabilidad': estabilidad,
            'recomendacion': rec_text
        })
    except Exception as e:
        if 'ds' in locals(): ds.close()
        return jsonify({'exito': False, 'error': str(e)}), 500

def procesar_serie(series_data):
    resultados = []
    vals, times = series_data.values, series_data.time.values
    for i, val in enumerate(vals):
        try:
            fecha_str = pd.to_datetime(times[i]).strftime('%Y-%m-%d')
        except:
            fecha_str = f"T-{i}"
        
        valor_float = float(val) if not pd.isna(float(val)) else 0
        resultados.append({'banda': i + 1, 'fecha': fecha_str, 'valor': round(valor_float, 6)})
    return resultados

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("--- Conexión PostgreSQL exitosa. ---")
        except Exception as e:
            print(f"--- FALLO PostgreSQL: {e} ---")
            print("--- CAMBIANDO AUTOMÁTICAMENTE A SQLITE PARA PRUEBAS LOCALES ---")
            
            # Reconfigurar a SQLite al vuelo
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agro_visor_local.db'
            # Es necesario re-inicializar el motor de SQLAlchemy o simplemente crear las tablas
            # En Flask-SQLAlchemy 3+ se puede usar db.engine.dispose()
            db.create_all()
            print("--- Base de datos SQLite iniciada correctamente. ---")

    app.run(debug=True)
else:
    # Para despliegue (Gunicorn), aseguramos la creación de tablas
    with app.app_context():
        try:
            db.create_all()
        except:
            pass