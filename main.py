import os
import xarray as xr
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de carpeta de subida
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('Inicio.html')

@app.route('/inicio')
def inicio():
    return render_template('Inicio.html')

@app.route('/app')
def pagina_app():
    return render_template('App.html')

# --- RUTA 1: CARGA INICIAL (PROMEDIO GLOBAL) ---
@app.route('/procesar_netcdf', methods=['POST'])
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

            # Promedio espacial
            dims_to_reduce = [d for d in data_array.dims if d in ['lat', 'lon', 'latitude', 'longitude']]
            
            if dims_to_reduce:
                series = data_array.mean(dim=dims_to_reduce)
            else:
                series = data_array

            resultados = procesar_serie(series)
            ds.close()

            return jsonify({
                'exito': True, 
                'variable': var_name,
                'filename': filename, 
                'datos': resultados,
                'tipo': 'Promedio de toda la zona'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# --- RUTA 2: CONSULTA POR CLIC (PUNTO ESPECÍFICO) ---
@app.route('/consultar_punto', methods=['POST'])
def consultar_punto():
    data = request.json
    filename = data.get('filename')
    
    try:
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'error': "Coordenadas inválidas"}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        ds = xr.open_dataset(filepath)
        var_name = list(ds.data_vars)[0]
        data_array = ds[var_name]

        # 1. Detectar latitud
        lat_name = None
        if 'lat' in ds.coords: lat_name = 'lat'
        elif 'latitude' in ds.coords: lat_name = 'latitude'
        
        # 2. Detectar longitud
        lon_name = None
        if 'lon' in ds.coords: lon_name = 'lon'
        elif 'longitude' in ds.coords: lon_name = 'longitude'

        if not lat_name or not lon_name:
            return jsonify({'error': f"No se encontraron coordenadas lat/lon. Detectadas: {list(ds.coords)}"}), 500

        # 3. Ajustar Longitud 0-360
        lon_ajustada = lon
        if ds.coords[lon_name].max() > 180 and lon < 0:
            lon_ajustada = lon + 360

        # 4. Consulta Nearest Neighbor
        consulta = {
            lat_name: lat,
            lon_name: lon_ajustada,
            'method': 'nearest'
        }

        punto = data_array.sel(**consulta)
        resultados = procesar_serie(punto)
        ds.close()

        return jsonify({
            'exito': True,
            'variable': var_name,
            'datos': resultados,
            'coords': f"Lat: {round(lat, 3)}, Lon: {round(lon, 3)}"
        })

    except Exception as e:
        print(f"Error backend: {e}")
        return jsonify({'error': "Error consultando punto: " + str(e)}), 500

# Función auxiliar
def procesar_serie(series_data):
    resultados = []
    vals = series_data.values
    times = series_data.time.values
    
    for i, val in enumerate(vals):
        try:
            tiempo = pd.to_datetime(times[i])
            fecha_str = tiempo.strftime('%Y-%m-%d')
        except:
            fecha_str = f"T-{i}"

        valor_float = float(val)
        if pd.isna(valor_float): 
            valor_float = 0

        resultados.append({
            'banda': i + 1,
            'fecha': fecha_str,
            'valor': round(valor_float, 6)
        })
    return resultados

if __name__ == '__main__':
    app.run(debug=True)