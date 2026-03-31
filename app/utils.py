import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def procesar_serie(series_data):
    """Auxiliar: Convierte Series de xarray/pandas a formato JSON para el frontend."""
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
