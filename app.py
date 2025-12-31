"""
Aplicación Web - Generador y Simulador de Bingos
=================================================
Servidor Flask para interfaz web local.

Uso:
    python app.py
    
    Abrir: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from services.generador_service import (
    ConfiguracionBingo,
    generar_bingos,
    obtener_generaciones_existentes
)
from services.simulador_service import (
    ConfiguracionSimulacion,
    ejecutar_simulacion,
    buscar_archivo_corel,
    obtener_simulaciones_existentes
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# =====================================================================
# === RUTAS PRINCIPALES ===
# =====================================================================

@app.route('/')
def index():
    """Página principal."""
    generaciones = obtener_generaciones_existentes()[:5]  # Últimas 5
    simulaciones = obtener_simulaciones_existentes()[:5]
    
    return render_template('index.html', 
                         generaciones=generaciones,
                         simulaciones=simulaciones)


# =====================================================================
# === RUTAS DEL GENERADOR ===
# =====================================================================

@app.route('/generador', methods=['GET', 'POST'])
def generador():
    """Página del generador de bingos."""
    if request.method == 'POST':
        try:
            # Obtener parámetros del formulario
            config = ConfiguracionBingo(
                seed=int(request.form.get('seed', datetime.now().strftime('%d%m%Y'))),
                numero_de_bingos=int(request.form.get('numero_bingos', 1000)),
                numeros_por_carton=int(request.form.get('numeros_por_carton', 10)),
                numero_maximo=int(request.form.get('numero_maximo', 60)),
                cartones_por_bingo=int(request.form.get('cartones_por_bingo', 3)),
                bingos_por_fila=int(request.form.get('bingos_por_fila', 2)),
                nombre_base=request.form.get('nombre_base', 'Bingos')
            )
            
            # Generar bingos
            resultado = generar_bingos(config)
            
            if resultado.exito:
                flash(f'✓ Generación exitosa: {resultado.combinaciones_generadas} combinaciones', 'success')
                return redirect(url_for('generador_resultado', carpeta=os.path.basename(resultado.carpeta_destino)))
            else:
                flash(f'✗ Error: {resultado.mensaje}', 'error')
                
        except ValueError as e:
            flash(f'✗ Error en parámetros: {str(e)}', 'error')
        except Exception as e:
            flash(f'✗ Error inesperado: {str(e)}', 'error')
    
    # Valores por defecto
    defaults = {
        'seed': datetime.now().strftime('%d%m%Y'),
        'numero_bingos': 1000,
        'numeros_por_carton': 10,
        'numero_maximo': 60,
        'cartones_por_bingo': 3,
        'bingos_por_fila': 2,
        'nombre_base': 'Bingos'
    }
    
    return render_template('generador.html', defaults=defaults)


@app.route('/generador/resultado/<carpeta>')
def generador_resultado(carpeta):
    """Muestra resultado de una generación."""
    ruta = os.path.join('bingos', carpeta)
    
    if not os.path.exists(ruta):
        flash('Carpeta no encontrada', 'error')
        return redirect(url_for('generador'))
    
    # Leer archivo info
    archivo_info = os.path.join(ruta, f'{carpeta}_info.txt')
    info_contenido = ''
    if os.path.exists(archivo_info):
        with open(archivo_info, 'r', encoding='utf-8') as f:
            info_contenido = f.read()
    
    # Leer primeras filas del CSV simple para preview
    archivo_simple = os.path.join(ruta, f'{carpeta}_simple.csv')
    preview_simple = []
    if os.path.exists(archivo_simple):
        import pandas as pd
        df = pd.read_csv(archivo_simple, sep=';', nrows=10)
        preview_simple = df.values.tolist()
        columnas_simple = df.columns.tolist()
    else:
        columnas_simple = []
    
    archivos = {
        'simple': f'{carpeta}_simple.csv',
        'corel': f'{carpeta}_corel.csv',
        'info': f'{carpeta}_info.txt'
    }
    
    return render_template('generador_resultado.html',
                         carpeta=carpeta,
                         info_contenido=info_contenido,
                         preview_simple=preview_simple,
                         columnas_simple=columnas_simple,
                         archivos=archivos)


@app.route('/generador/historial')
def generador_historial():
    """Historial de generaciones."""
    generaciones = obtener_generaciones_existentes()
    return render_template('generador_historial.html', generaciones=generaciones)


# =====================================================================
# === RUTAS DEL SIMULADOR ===
# =====================================================================

@app.route('/simulador', methods=['GET', 'POST'])
def simulador():
    """Página del simulador de jugadas."""
    generaciones = obtener_generaciones_existentes()
    
    if request.method == 'POST':
        try:
            archivo_corel = request.form.get('archivo_corel')
            
            if not archivo_corel:
                archivo_corel = buscar_archivo_corel()
                if not archivo_corel:
                    flash('No se encontró ningún archivo Corel. Genera bingos primero.', 'error')
                    return redirect(url_for('simulador'))
            
            config = ConfiguracionSimulacion(
                archivo_corel=archivo_corel,
                numero_jugadas=int(request.form.get('numero_jugadas', 50)),
                seed=int(request.form.get('seed')) if request.form.get('seed') else None
            )
            
            # Ejecutar simulación
            resultado = ejecutar_simulacion(config)
            
            if resultado.exito:
                flash(f'✓ Simulación completada: {resultado.total_jugadas} jugadas', 'success')
                
                # Guardar datos de gráficos en sesión o archivo temporal
                graficos_file = os.path.join(resultado.carpeta_destino, 'graficos_data.json')
                with open(graficos_file, 'w') as f:
                    json.dump(resultado.graficos_data, f)
                
                return redirect(url_for('simulador_resultado', 
                                       carpeta=os.path.basename(resultado.carpeta_destino)))
            else:
                flash(f'✗ Error: {resultado.mensaje}', 'error')
                
        except ValueError as e:
            flash(f'✗ Error en parámetros: {str(e)}', 'error')
        except Exception as e:
            flash(f'✗ Error inesperado: {str(e)}', 'error')
    
    defaults = {
        'numero_jugadas': 50,
        'seed': ''
    }
    
    return render_template('simulador.html', 
                         defaults=defaults,
                         generaciones=generaciones)


@app.route('/simulador/resultado/<carpeta>')
def simulador_resultado(carpeta):
    """Muestra resultado de una simulación."""
    ruta = os.path.join('simulaciones', carpeta)
    
    if not os.path.exists(ruta):
        flash('Carpeta no encontrada', 'error')
        return redirect(url_for('simulador'))
    
    # Leer datos de gráficos
    graficos_file = os.path.join(ruta, 'graficos_data.json')
    graficos_data = {}
    if os.path.exists(graficos_file):
        with open(graficos_file, 'r') as f:
            graficos_data = json.load(f)
    
    # Leer primeras filas del CSV para preview
    archivo_resultados = os.path.join(ruta, f'{carpeta}_resultados.csv')
    preview_resultados = []
    if os.path.exists(archivo_resultados):
        import pandas as pd
        df = pd.read_csv(archivo_resultados, sep=';', nrows=10)
        preview_resultados = df.to_dict('records')
    
    return render_template('simulador_resultado.html',
                         carpeta=carpeta,
                         graficos_data=json.dumps(graficos_data),
                         preview_resultados=preview_resultados)


@app.route('/simulador/historial')
def simulador_historial():
    """Historial de simulaciones."""
    simulaciones = obtener_simulaciones_existentes()
    return render_template('simulador_historial.html', simulaciones=simulaciones)


# =====================================================================
# === RUTAS DE DESCARGA ===
# =====================================================================

@app.route('/descargar/bingos/<carpeta>/<archivo>')
def descargar_bingo(carpeta, archivo):
    """Descarga archivo de generación."""
    # Sanitizar nombres para prevenir path traversal
    carpeta_segura = secure_filename(carpeta)
    archivo_seguro = secure_filename(archivo)
    
    ruta = os.path.join('bingos', carpeta_segura, archivo_seguro)
    ruta_absoluta = os.path.abspath(ruta)
    carpeta_base = os.path.abspath('bingos')
    
    # Verificar que la ruta está dentro de la carpeta permitida
    if not ruta_absoluta.startswith(carpeta_base):
        flash('Acceso no permitido', 'error')
        return redirect(url_for('generador_historial'))
    
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    flash('Archivo no encontrado', 'error')
    return redirect(url_for('generador'))


@app.route('/descargar/simulaciones/<carpeta>/<archivo>')
def descargar_simulacion(carpeta, archivo):
    """Descarga archivo de simulación."""
    # Sanitizar nombres para prevenir path traversal
    carpeta_segura = secure_filename(carpeta)
    archivo_seguro = secure_filename(archivo)
    
    ruta = os.path.join('simulaciones', carpeta_segura, archivo_seguro)
    ruta_absoluta = os.path.abspath(ruta)
    carpeta_base = os.path.abspath('simulaciones')
    
    # Verificar que la ruta está dentro de la carpeta permitida
    if not ruta_absoluta.startswith(carpeta_base):
        flash('Acceso no permitido', 'error')
        return redirect(url_for('simulador_historial'))
    
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    flash('Archivo no encontrado', 'error')
    return redirect(url_for('simulador'))


# =====================================================================
# === API JSON (para uso futuro) ===
# =====================================================================

@app.route('/api/generaciones')
def api_generaciones():
    """API: Lista de generaciones."""
    generaciones = obtener_generaciones_existentes()
    return jsonify([{
        'nombre': g['nombre'],
        'fecha': g['fecha_modificacion'].isoformat()
    } for g in generaciones])


@app.route('/api/simulaciones')
def api_simulaciones():
    """API: Lista de simulaciones."""
    simulaciones = obtener_simulaciones_existentes()
    return jsonify([{
        'nombre': s['nombre'],
        'fecha': s['fecha_modificacion'].isoformat()
    } for s in simulaciones])


# =====================================================================
# === MAIN ===
# =====================================================================

if __name__ == '__main__':
    # Configuración desde variables de entorno
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 50)
    print("   BINGO WEB - Servidor Local")
    print("=" * 50)
    print(f"\n   Abre en tu navegador: http://localhost:{port}\n")
    print(f"   Modo debug: {debug_mode}")
    print("=" * 50)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
