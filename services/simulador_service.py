"""
Servicio de Simulación de Bingos
================================
Lógica refactorizada para uso en web y CLI.
"""

import random
import os
import glob
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class ConfiguracionSimulacion:
    """Configuración para la simulación."""
    archivo_corel: str
    numero_jugadas: int = 50
    seed: Optional[int] = None
    carpeta_salida: str = 'simulaciones'


@dataclass
class ResultadoJugada:
    """Resultado de una jugada individual."""
    jugada_num: int
    bolillas_hasta_ganador: int
    cantidad_ganadores: int
    ganadores: List[Dict[str, str]]
    orden_bolillas: List[int]


@dataclass
class EstadisticasSimulacion:
    """Estadísticas calculadas de la simulación."""
    bolillas_min: int
    bolillas_max: int
    bolillas_media: float
    bolillas_mediana: float
    bolillas_desviacion: float
    ganadores_media: float
    ganadores_max: int
    distribucion_ganadores: Dict[int, int]
    frecuencia_bingos: Dict[str, int]
    frecuencia_cartones: Dict[str, int]
    top_bingo: tuple
    top_carton: tuple


@dataclass
class ResultadoSimulacion:
    """Resultado completo de la simulación."""
    exito: bool
    mensaje: str
    carpeta_destino: str = ''
    archivo_resultados: str = ''
    total_jugadas: int = 0
    estadisticas: EstadisticasSimulacion = None
    resultados_jugadas: List[ResultadoJugada] = field(default_factory=list)
    graficos_data: Dict[str, Any] = field(default_factory=dict)


def buscar_archivo_corel(carpeta_bingos: str = 'bingos') -> Optional[str]:
    """Busca el archivo Corel más reciente."""
    archivos_corel = []
    
    # Buscar en carpeta bingos/*/
    patron_bingos = os.path.join(carpeta_bingos, '*', '*_corel.csv')
    archivos_corel.extend(glob.glob(patron_bingos))
    
    # También buscar en raíz
    archivos_corel.extend(glob.glob('*_corel.csv'))
    
    if not archivos_corel:
        return None
    
    archivos_corel.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return archivos_corel[0]


def cargar_cartones_corel(archivo_csv: str) -> List[Dict[str, Any]]:
    """Carga cartones desde archivo Corel."""
    df = pd.read_csv(archivo_csv, sep=';')
    cartones = []
    
    tipos_carton = {
        'A': (1, 11),
        'B': (11, 21),
        'C': (21, 31),
        'D': (32, 42),
        'E': (42, 52),
        'F': (52, 62),
    }
    
    for _, fila in df.iterrows():
        bingo_id_1 = str(fila.iloc[0])
        bingo_id_2 = str(fila.iloc[31])
        
        for tipo in ['A', 'B', 'C']:
            inicio, fin = tipos_carton[tipo]
            numeros = set(int(x) for x in fila.iloc[inicio:fin])
            cartones.append({
                'bingo_id': bingo_id_1,
                'carton_tipo': tipo,
                'numeros': numeros
            })
        
        for tipo in ['D', 'E', 'F']:
            inicio, fin = tipos_carton[tipo]
            numeros = set(int(x) for x in fila.iloc[inicio:fin])
            cartones.append({
                'bingo_id': bingo_id_2,
                'carton_tipo': tipo,
                'numeros': numeros
            })
    
    return cartones


def simular_jugada(cartones: List[Dict], bolillas_totales: int = 60, numeros_por_carton: int = 10) -> ResultadoJugada:
    """Simula una jugada de bingo."""
    orden_bolillas = list(range(1, bolillas_totales + 1))
    random.shuffle(orden_bolillas)
    
    aciertos = [{
        'bingo_id': c['bingo_id'],
        'carton_tipo': c['carton_tipo'],
        'numeros': c['numeros'].copy(),
        'aciertos': set()
    } for c in cartones]
    
    ganadores = []
    bolillas_cantadas = 0
    
    for bolilla in orden_bolillas:
        bolillas_cantadas += 1
        
        for carton in aciertos:
            if bolilla in carton['numeros']:
                carton['aciertos'].add(bolilla)
                
                if len(carton['aciertos']) == numeros_por_carton:
                    ganadores.append({
                        'bingo_id': carton['bingo_id'],
                        'carton_tipo': carton['carton_tipo']
                    })
        
        if ganadores:
            break
    
    return ResultadoJugada(
        jugada_num=0,  # Se asigna después
        bolillas_hasta_ganador=bolillas_cantadas,
        cantidad_ganadores=len(ganadores),
        ganadores=ganadores,
        orden_bolillas=orden_bolillas[:bolillas_cantadas]
    )


def calcular_estadisticas(resultados: List[ResultadoJugada]) -> EstadisticasSimulacion:
    """Calcula estadísticas de la simulación."""
    bolillas = [r.bolillas_hasta_ganador for r in resultados]
    cantidades = [r.cantidad_ganadores for r in resultados]
    
    bingos_ganadores = []
    cartones_ganadores = []
    
    for r in resultados:
        for g in r.ganadores:
            bingos_ganadores.append(g['bingo_id'])
            cartones_ganadores.append(g['carton_tipo'])
    
    freq_bingos = Counter(bingos_ganadores)
    freq_cartones = Counter(cartones_ganadores)
    
    top_bingo = freq_bingos.most_common(1)
    top_carton = freq_cartones.most_common(1)
    
    return EstadisticasSimulacion(
        bolillas_min=min(bolillas),
        bolillas_max=max(bolillas),
        bolillas_media=float(np.mean(bolillas)),
        bolillas_mediana=float(np.median(bolillas)),
        bolillas_desviacion=float(np.std(bolillas)),
        ganadores_media=float(np.mean(cantidades)),
        ganadores_max=max(cantidades),
        distribucion_ganadores=dict(Counter(cantidades)),
        frecuencia_bingos=dict(freq_bingos),
        frecuencia_cartones=dict(freq_cartones),
        top_bingo=top_bingo[0] if top_bingo else ('N/A', 0),
        top_carton=top_carton[0] if top_carton else ('N/A', 0)
    )


def generar_datos_graficos(resultados: List[ResultadoJugada], estadisticas: EstadisticasSimulacion) -> Dict[str, Any]:
    """Genera datos para gráficos Plotly."""
    bolillas = [r.bolillas_hasta_ganador for r in resultados]
    
    # Histograma de bolillas
    histograma_data = {
        'x': bolillas,
        'type': 'histogram',
        'name': 'Bolillas hasta BINGO',
        'marker': {'color': '#3498db'},
        'xbins': {'size': 1}
    }
    
    # Línea de media
    media_line = {
        'type': 'line',
        'x0': estadisticas.bolillas_media,
        'x1': estadisticas.bolillas_media,
        'y0': 0,
        'y1': 1,
        'yref': 'paper',
        'line': {'color': 'red', 'dash': 'dash', 'width': 2}
    }
    
    # Ganadores por jugada
    dist = estadisticas.distribucion_ganadores
    ganadores_data = {
        'x': list(dist.keys()),
        'y': list(dist.values()),
        'type': 'bar',
        'name': 'Frecuencia',
        'marker': {'color': '#2ecc71'}
    }
    
    # Top 10 bingos
    top_bingos = sorted(estadisticas.frecuencia_bingos.items(), key=lambda x: x[1], reverse=True)[:10]
    ranking_data = {
        'y': [f'Bingo {b[0]}' for b in top_bingos],
        'x': [b[1] for b in top_bingos],
        'type': 'bar',
        'orientation': 'h',
        'marker': {'color': '#9b59b6'}
    }
    
    # Distribución por tipo de cartón
    tipos = ['A', 'B', 'C', 'D', 'E', 'F']
    colores = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
    cartones_data = {
        'x': tipos,
        'y': [estadisticas.frecuencia_cartones.get(t, 0) for t in tipos],
        'type': 'bar',
        'marker': {'color': colores}
    }
    
    return {
        'histograma': {
            'data': [histograma_data],
            'layout': {
                'title': 'Distribución de Bolillas hasta el Primer BINGO',
                'xaxis': {'title': 'Bolillas'},
                'yaxis': {'title': 'Frecuencia'},
                'shapes': [media_line],
                'annotations': [{
                    'x': estadisticas.bolillas_media,
                    'y': 1,
                    'yref': 'paper',
                    'text': f'Media: {estadisticas.bolillas_media:.1f}',
                    'showarrow': False,
                    'yshift': 10
                }]
            }
        },
        'ganadores': {
            'data': [ganadores_data],
            'layout': {
                'title': 'Ganadores Simultáneos por Jugada',
                'xaxis': {'title': 'Cantidad de Ganadores', 'dtick': 1},
                'yaxis': {'title': 'Número de Jugadas'}
            }
        },
        'ranking': {
            'data': [ranking_data],
            'layout': {
                'title': 'Top 10 Bingos Más Ganadores',
                'xaxis': {'title': 'Victorias'},
                'yaxis': {'title': 'Bingo ID', 'autorange': 'reversed'},
                'margin': {'l': 100}
            }
        },
        'cartones': {
            'data': [cartones_data],
            'layout': {
                'title': 'Distribución de Victorias por Tipo de Cartón',
                'xaxis': {'title': 'Tipo de Cartón'},
                'yaxis': {'title': 'Victorias'}
            }
        }
    }


def exportar_resultados_csv(resultados: List[ResultadoJugada], archivo: str):
    """Exporta resultados a CSV."""
    filas = []
    
    for r in resultados:
        ganadores_str = '; '.join([
            f"{g['bingo_id']}-{g['carton_tipo']}" 
            for g in r.ganadores
        ])
        
        filas.append({
            'Jugada': r.jugada_num,
            'Bolillas_Hasta_Ganador': r.bolillas_hasta_ganador,
            'Cantidad_Ganadores': r.cantidad_ganadores,
            'Ganadores': ganadores_str,
            'Bolillas_Cantadas': ', '.join(map(str, r.orden_bolillas))
        })
    
    df = pd.DataFrame(filas)
    df.to_csv(archivo, sep=';', index=False, encoding='utf-8')


def ejecutar_simulacion(config: ConfiguracionSimulacion, callback=None) -> ResultadoSimulacion:
    """
    Función principal para ejecutar simulación.
    
    Args:
        config: Configuración de simulación
        callback: Función opcional para reportar progreso
    
    Returns:
        ResultadoSimulacion con todos los datos
    """
    # Verificar archivo
    if not os.path.exists(config.archivo_corel):
        return ResultadoSimulacion(
            exito=False,
            mensaje=f"No se encontró el archivo: {config.archivo_corel}"
        )
    
    # Preparar rutas
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    nombre_simulacion = f'Simulacion_{config.numero_jugadas}_{fecha_hoy}'
    carpeta_destino = os.path.join(config.carpeta_salida, nombre_simulacion)
    archivo_resultados = os.path.join(carpeta_destino, f'{nombre_simulacion}_resultados.csv')
    
    # Crear carpeta
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    # Configurar seed
    if config.seed is not None:
        random.seed(config.seed)
    
    # Cargar cartones
    try:
        cartones = cargar_cartones_corel(config.archivo_corel)
    except Exception as e:
        return ResultadoSimulacion(
            exito=False,
            mensaje=f"Error al cargar archivo: {str(e)}"
        )
    
    # Ejecutar simulación
    resultados = []
    for i in range(config.numero_jugadas):
        resultado = simular_jugada(cartones)
        resultado.jugada_num = i + 1
        resultados.append(resultado)
        
        if callback and (i + 1) % 10 == 0:
            callback(i + 1, config.numero_jugadas)
    
    # Calcular estadísticas
    estadisticas = calcular_estadisticas(resultados)
    
    # Generar datos para gráficos
    graficos_data = generar_datos_graficos(resultados, estadisticas)
    
    # Exportar CSV
    exportar_resultados_csv(resultados, archivo_resultados)
    
    return ResultadoSimulacion(
        exito=True,
        mensaje="Simulación completada exitosamente",
        carpeta_destino=carpeta_destino,
        archivo_resultados=archivo_resultados,
        total_jugadas=config.numero_jugadas,
        estadisticas=estadisticas,
        resultados_jugadas=resultados,
        graficos_data=graficos_data
    )


def obtener_simulaciones_existentes(carpeta_salida: str = 'simulaciones') -> List[Dict[str, Any]]:
    """Obtiene lista de simulaciones existentes."""
    simulaciones = []
    
    if not os.path.exists(carpeta_salida):
        return simulaciones
    
    for nombre in os.listdir(carpeta_salida):
        ruta = os.path.join(carpeta_salida, nombre)
        if os.path.isdir(ruta):
            archivo_resultados = os.path.join(ruta, f'{nombre}_resultados.csv')
            
            if os.path.exists(archivo_resultados):
                simulaciones.append({
                    'nombre': nombre,
                    'ruta': ruta,
                    'archivo_resultados': archivo_resultados,
                    'fecha_modificacion': datetime.fromtimestamp(os.path.getmtime(archivo_resultados))
                })
    
    simulaciones.sort(key=lambda x: x['fecha_modificacion'], reverse=True)
    
    return simulaciones
