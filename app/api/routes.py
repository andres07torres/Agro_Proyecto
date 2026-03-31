import os
import xarray as xr
import pandas as pd
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import DatasetHistory
from ..utils import allowed_file, procesar_serie

api_bp = Blueprint('api', __name__)

@api_bp.route('/procesar_netcdf', methods=['POST'])
@login_required
def procesar_netcdf():
    if 'archivo_nc' not in request.files:
        return jsonify({'error': 'No se envió el archivo'}), 400
    
    file = request.files['archivo_nc']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if file:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Extensión de archivo no permitida (.nc o .zip)'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
            current_app.logger.error(f"Error procesando NetCDF: {e}")
            return jsonify({'error': 'Error interno al procesar el archivo. Verifique el formato.'}), 500

@api_bp.route('/consultar_punto', methods=['POST'])
@login_required
def consultar_punto():
    data = request.json
    filename = secure_filename(data.get('filename'))
    try:
        lat, lon = float(data.get('lat')), float(data.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'error': "Coordenadas inválidas"}), 400
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    try:
        ds = xr.open_dataset(filepath)
        var_name = list(ds.data_vars)[0]
        data_array = ds[var_name]

        lat_name = 'lat' if 'lat' in ds.coords else 'latitude' if 'latitude' in ds.coords else None
        lon_name = 'lon' if 'lon' in ds.coords else 'longitude' if 'longitude' in ds.coords else None

        if not lat_name or not lon_name:
            return jsonify({'error': "Coordenadas no encontradas en el dataset"}), 500

        lon_ajustada = lon + 360 if ds.coords[lon_name].max() > 180 and lon < 0 else lon
        punto = data_array.sel(**{lat_name: lat, lon_name: lon_ajustada, 'method': 'nearest'})
        resultados = procesar_serie(punto)
        ds.close()

        return jsonify({'exito': True, 'variable': var_name, 'datos': resultados, 'coords': f"Lat: {round(lat, 3)}, Lon: {round(lon, 3)}"})
    except Exception as e:
        current_app.logger.error(f"Error en consultar_punto: {e}")
        return jsonify({'error': 'Error consultando coordenadas en el dataset.'}), 500

@api_bp.route('/api/get_trends/<filename>')
@login_required
def get_trends(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    lat_val = request.args.get('lat', type=float)
    lon_val = request.args.get('lon', type=float)
    
    try:
        ds = xr.open_dataset(filepath)
        var_name = list(ds.data_vars)[0]
        data_array = ds[var_name]
        
        if lat_val is not None and lon_val is not None:
            sel_dict = {}
            if 'lat' in data_array.dims: sel_dict['lat'] = lat_val
            elif 'latitude' in data_array.dims: sel_dict['latitude'] = lat_val
            if 'lon' in data_array.dims: sel_dict['lon'] = lon_val
            elif 'longitude' in data_array.dims: sel_dict['longitude'] = lon_val
            series = data_array.sel(**sel_dict, method='nearest')
            ubicacion = f"Lat: {round(lat_val, 3)}, Lon: {round(lon_val, 3)}"
        else:
            dims_to_reduce = [d for d in data_array.dims if d in ['lat', 'lon', 'latitude', 'longitude']]
            series = data_array.mean(dim=dims_to_reduce) if dims_to_reduce else data_array
            ubicacion = "Resumen Regional"
        
        df = series.to_dataframe(name='valor').reset_index()
        df['fecha'] = pd.to_datetime(df['time'])
        df['mes'] = df['fecha'].dt.month
        df['anio'] = df['fecha'].dt.year
        
        anio_min = df['anio'].min()
        df = df[df['anio'] >= 1980]
        
        if df.empty:
            return jsonify({'exito': False, 'error': f'El archivo no contiene datos históricos válidos.'}), 400

        ciclo_raw = df.groupby('mes')['valor'].mean().round(2).to_dict()
        ciclo_final = [float(ciclo_raw.get(m, 0)) for m in range(1, 13)]
        
        anual_dist = {}
        for anio, g in df.groupby('anio'):
            m_raw = g.groupby('mes')['valor'].mean().round(2).to_dict()
            anual_dist[str(anio)] = [float(m_raw.get(m, 0)) for m in range(1, 13)]
        
        anual_raw = df.groupby('anio')['valor'].mean().round(2).sort_index().to_dict()
        anual_labels = [str(a) for a in anual_raw.keys()]
        anual_values = [float(v) for v in anual_raw.values()]
        
        promedio_total = float(df['valor'].mean())
        ultimo_anio = anual_values[-1] if anual_values else 0
        anomalia = ultimo_anio - promedio_total

        std_val = float(df['valor'].std())
        cv = std_val / promedio_total if promedio_total > 0 else 0
        estabilidad = "Alta" if cv < 0.25 else ("Moderada" if cv < 0.5 else "Baja")
        
        if anomalia > (0.15 * promedio_total):
            rec_text = "Se observa un excedente hídrico significativo. Se recomienda optimizar sistemas de drenaje."
        elif anomalia < (-0.15 * promedio_total):
            rec_text = "Déficit hídrico detectado respecto al histórico. Se sugiere priorizar el riego suplementario."
        else:
            rec_text = "Condiciones hídricas normales. Mantener prácticas culturales programadas."
        
        ds.close()
        
        return jsonify({
            'exito': True,
            'ubicacion': ubicacion,
            'ciclo_labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            'ciclo_values': ciclo_final,
            'anual_dist': anual_dist,
            'anual_labels': anual_labels,
            'anual_values': anual_values,
            'promedio_total': round(promedio_total, 2),
            'anomalia': round(anomalia, 2),
            'estabilidad': estabilidad,
            'recomendacion': rec_text
        })
    except Exception as e:
        if 'ds' in locals(): ds.close()
        current_app.logger.error(f"Error en tendencias API: {e}")
        return jsonify({'exito': False, 'error': 'Fallo en análisis de tendencias.'}), 500
