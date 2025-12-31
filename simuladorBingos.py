"""
Simulador de Jugadas de Bingo
=============================
Simula jugadas aleatorias sobre cartones generados en formato Corel.
Genera estadísticas detalladas y gráficos de análisis.

Uso:
    python simuladorBingos.py
    python simuladorBingos.py --jugadas 100 --archivo bingos/Bingos_1000_20251231/Bingos_1000_20251231_corel.csv

Autor: DiogoMix8
Versión: 1.1
"""

import pandas as pd
import random
import argparse
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime

# =====================================================================
# === CONFIGURACIÓN POR DEFECTO ===
# =====================================================================

NUMERO_DE_JUGADAS = 50
ARCHIVO_COREL_DEFAULT = None  # Se busca automáticamente el más reciente
SEED = None  # None = aleatorio cada vez
CARPETA_SALIDA = 'simulaciones'  # Carpeta principal de salida
CARPETA_BINGOS = 'bingos'        # Carpeta donde buscar archivos Corel
BOLILLAS_TOTALES = 60
NUMEROS_POR_CARTON = 10

# =====================================================================
# === ARGUMENTOS DE LÍNEA DE COMANDOS ===
# =====================================================================

def parsear_argumentos():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Simulador de Jugadas de Bingo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python simuladorBingos.py
  python simuladorBingos.py --jugadas 100
  python simuladorBingos.py --archivo bingos/Bingos_1000_20251231/Bingos_1000_20251231_corel.csv --seed 12345
        '''
    )
    
    parser.add_argument(
        '--jugadas', '-j',
        type=int,
        default=NUMERO_DE_JUGADAS,
        help=f'Número de jugadas a simular (default: {NUMERO_DE_JUGADAS})'
    )
    
    parser.add_argument(
        '--archivo', '-a',
        type=str,
        default=None,
        help='Archivo CSV en formato Corel (default: busca el más reciente)'
    )
    
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=SEED,
        help='Semilla para reproducibilidad (default: aleatorio)'
    )
    
    parser.add_argument(
        '--carpeta-salida', '-o',
        type=str,
        default=CARPETA_SALIDA,
        help=f'Carpeta para guardar resultados (default: {CARPETA_SALIDA})'
    )
    
    return parser.parse_args()

# =====================================================================
# === BÚSQUEDA DE ARCHIVO COREL ===
# =====================================================================

def buscar_archivo_corel():
    """Busca el archivo Corel más reciente en bingos/*/ o en el directorio actual."""
    archivos_corel = []
    
    # Buscar en carpeta bingos/*/ (nueva estructura)
    patron_bingos = os.path.join(CARPETA_BINGOS, '*', '*_corel.csv')
    archivos_corel.extend(glob.glob(patron_bingos))
    
    # También buscar en raíz (compatibilidad con archivos antiguos)
    archivos_corel.extend(glob.glob('*_corel.csv'))
    
    if not archivos_corel:
        raise FileNotFoundError(
            "No se encontró ningún archivo *_corel.csv.\n"
            "Genera uno primero con: python generationBingosRandomAudit.py"
        )
    
    # Ordenar por fecha de modificación (más reciente primero)
    archivos_corel.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return archivos_corel[0]

# =====================================================================
# === CARGA DE DATOS ===
# =====================================================================

def cargar_cartones_corel(archivo_csv: str) -> list:
    """
    Carga el archivo Corel y extrae todos los cartones individuales.
    
    Retorna lista de diccionarios:
    [
        {'bingo_id': '0001', 'carton_tipo': 'A', 'numeros': set([1,2,3,...])},
        {'bingo_id': '0001', 'carton_tipo': 'B', 'numeros': set([4,5,6,...])},
        ...
    ]
    """
    print(f"\nCargando cartones desde: {archivo_csv}")
    
    df = pd.read_csv(archivo_csv, sep=';')
    cartones = []
    
    # Mapeo de columnas a tipos de cartón
    # CARTON 1: A (cols 1-10), B (cols 11-20), C (cols 21-30)
    # CARTON 2: D (cols 32-41), E (cols 42-51), F (cols 52-61)
    
    tipos_carton = {
        'A': (1, 11),    # Columnas 1-10 (índice 1-10 en df)
        'B': (11, 21),   # Columnas 11-20
        'C': (21, 31),   # Columnas 21-30
        'D': (32, 42),   # Columnas 32-41 (después de CARTON 2)
        'E': (42, 52),   # Columnas 42-51
        'F': (52, 62),   # Columnas 52-61
    }
    
    for _, fila in df.iterrows():
        bingo_id_1 = str(fila.iloc[0])  # CARTON 1
        bingo_id_2 = str(fila.iloc[31])  # CARTON 2
        
        # Extraer cartones del bingo izquierdo (A, B, C)
        for tipo in ['A', 'B', 'C']:
            inicio, fin = tipos_carton[tipo]
            numeros = set(int(x) for x in fila.iloc[inicio:fin])
            cartones.append({
                'bingo_id': bingo_id_1,
                'carton_tipo': tipo,
                'numeros': numeros
            })
        
        # Extraer cartones del bingo derecho (D, E, F)
        for tipo in ['D', 'E', 'F']:
            inicio, fin = tipos_carton[tipo]
            numeros = set(int(x) for x in fila.iloc[inicio:fin])
            cartones.append({
                'bingo_id': bingo_id_2,
                'carton_tipo': tipo,
                'numeros': numeros
            })
    
    print(f"[✓] Cargados {len(cartones)} cartones de {len(df)} filas")
    
    return cartones

# =====================================================================
# === MOTOR DE SIMULACIÓN ===
# =====================================================================

def generar_orden_bolillas() -> list:
    """Genera orden aleatorio de bolillas 1-60."""
    bolillas = list(range(1, BOLILLAS_TOTALES + 1))
    random.shuffle(bolillas)
    return bolillas

def simular_jugada(cartones: list) -> dict:
    """
    Simula una jugada completa de bingo.
    
    Retorna:
    {
        'bolillas_hasta_ganador': int,
        'ganadores': [{'bingo_id': str, 'carton_tipo': str}],
        'cantidad_ganadores': int,
        'orden_bolillas': list[int]
    }
    """
    orden_bolillas = generar_orden_bolillas()
    
    # Inicializar aciertos por cartón
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
        
        # Marcar aciertos en todos los cartones
        for carton in aciertos:
            if bolilla in carton['numeros']:
                carton['aciertos'].add(bolilla)
                
                # Verificar si completó el cartón (BINGO!)
                if len(carton['aciertos']) == NUMEROS_POR_CARTON:
                    ganadores.append({
                        'bingo_id': carton['bingo_id'],
                        'carton_tipo': carton['carton_tipo']
                    })
        
        # Si hay al menos un ganador, terminar la jugada
        if ganadores:
            break
    
    return {
        'bolillas_hasta_ganador': bolillas_cantadas,
        'ganadores': ganadores,
        'cantidad_ganadores': len(ganadores),
        'orden_bolillas': orden_bolillas[:bolillas_cantadas]
    }

def ejecutar_simulacion(cartones: list, num_jugadas: int, seed: int = None) -> list:
    """Ejecuta N jugadas y retorna lista de resultados."""
    
    if seed is not None:
        random.seed(seed)
        print(f"[✓] Seed establecido: {seed}")
    
    print(f"\nSimulando {num_jugadas} jugadas...")
    
    resultados = []
    
    for i in range(num_jugadas):
        resultado = simular_jugada(cartones)
        resultado['jugada_num'] = i + 1
        resultados.append(resultado)
        
        # Progreso cada 10 jugadas
        if (i + 1) % 10 == 0:
            print(f"    Progreso: {i + 1}/{num_jugadas}")
    
    print(f"[✓] Simulación completa: {num_jugadas} jugadas")
    
    return resultados

# =====================================================================
# === ANÁLISIS ESTADÍSTICO ===
# =====================================================================

def calcular_estadisticas(resultados: list) -> dict:
    """Calcula estadísticas de la simulación."""
    
    bolillas = [r['bolillas_hasta_ganador'] for r in resultados]
    cantidades_ganadores = [r['cantidad_ganadores'] for r in resultados]
    
    # Frecuencia de bingos ganadores
    bingos_ganadores = []
    cartones_ganadores = []
    
    for r in resultados:
        for g in r['ganadores']:
            bingos_ganadores.append(g['bingo_id'])
            cartones_ganadores.append(g['carton_tipo'])
    
    return {
        'bolillas': {
            'min': min(bolillas),
            'max': max(bolillas),
            'media': np.mean(bolillas),
            'mediana': np.median(bolillas),
            'desviacion': np.std(bolillas)
        },
        'ganadores_por_jugada': {
            'min': min(cantidades_ganadores),
            'max': max(cantidades_ganadores),
            'media': np.mean(cantidades_ganadores),
            'distribucion': Counter(cantidades_ganadores)
        },
        'frecuencia_bingos': Counter(bingos_ganadores),
        'frecuencia_cartones': Counter(cartones_ganadores),
        'total_jugadas': len(resultados)
    }

# =====================================================================
# === CREAR CARPETAS ===
# =====================================================================

def crear_carpetas(carpeta_destino: str, carpeta_graficos: str):
    """Crea la estructura de carpetas si no existe."""
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"[✓] Carpeta creada: {carpeta_destino}")
    
    if not os.path.exists(carpeta_graficos):
        os.makedirs(carpeta_graficos)

# =====================================================================
# === EXPORTACIÓN CSV ===
# =====================================================================

def exportar_resultados_csv(resultados: list, archivo: str):
    """Exporta resultados detallados a CSV."""
    
    filas = []
    
    for r in resultados:
        ganadores_str = '; '.join([
            f"{g['bingo_id']}-{g['carton_tipo']}" 
            for g in r['ganadores']
        ])
        
        filas.append({
            'Jugada': r['jugada_num'],
            'Bolillas_Hasta_Ganador': r['bolillas_hasta_ganador'],
            'Cantidad_Ganadores': r['cantidad_ganadores'],
            'Ganadores': ganadores_str,
            'Bolillas_Cantadas': ', '.join(map(str, r['orden_bolillas']))
        })
    
    df = pd.DataFrame(filas)
    df.to_csv(archivo, sep=';', index=False, encoding='utf-8')
    
    print(f"[✓] Resultados exportados: {archivo}")

# =====================================================================
# === GENERACIÓN DE GRÁFICOS ===
# =====================================================================

def generar_graficos(resultados: list, estadisticas: dict, carpeta: str):
    """Genera gráficos estadísticos."""
    
    # Configuración general de estilo
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 1. Histograma de bolillas hasta primer ganador
    plt.figure(figsize=(10, 6))
    bolillas = [r['bolillas_hasta_ganador'] for r in resultados]
    plt.hist(bolillas, bins=range(min(bolillas), max(bolillas) + 2), 
             edgecolor='black', alpha=0.7, color='#3498db')
    plt.axvline(estadisticas['bolillas']['media'], color='red', 
                linestyle='--', linewidth=2, label=f"Media: {estadisticas['bolillas']['media']:.1f}")
    plt.xlabel('Bolillas hasta el primer ganador', fontsize=12)
    plt.ylabel('Frecuencia', fontsize=12)
    plt.title('Distribución de Bolillas hasta el Primer BINGO', fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, 'histograma_bolillas.png'), dpi=150)
    plt.close()
    
    # 2. Barras de ganadores simultáneos por jugada
    plt.figure(figsize=(8, 6))
    dist = estadisticas['ganadores_por_jugada']['distribucion']
    cantidades = sorted(dist.keys())
    frecuencias = [dist[c] for c in cantidades]
    plt.bar(cantidades, frecuencias, color='#2ecc71', edgecolor='black')
    plt.xlabel('Cantidad de Ganadores Simultáneos', fontsize=12)
    plt.ylabel('Número de Jugadas', fontsize=12)
    plt.title('Ganadores Simultáneos por Jugada', fontsize=14)
    plt.xticks(cantidades)
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, 'ganadores_por_jugada.png'), dpi=150)
    plt.close()
    
    # 3. Ranking de bingos más ganadores (top 10)
    plt.figure(figsize=(10, 6))
    top_bingos = estadisticas['frecuencia_bingos'].most_common(10)
    if top_bingos:
        bingos = [b[0] for b in top_bingos]
        victorias = [b[1] for b in top_bingos]
        plt.barh(range(len(bingos)), victorias, color='#9b59b6', edgecolor='black')
        plt.yticks(range(len(bingos)), [f'Bingo {b}' for b in bingos])
        plt.xlabel('Victorias', fontsize=12)
        plt.ylabel('Bingo ID', fontsize=12)
        plt.title('Top 10 Bingos Más Ganadores', fontsize=14)
        plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, 'ranking_bingos.png'), dpi=150)
    plt.close()
    
    # 4. Distribución por tipo de cartón (A-F)
    plt.figure(figsize=(8, 6))
    tipos = ['A', 'B', 'C', 'D', 'E', 'F']
    freq = estadisticas['frecuencia_cartones']
    victorias = [freq.get(t, 0) for t in tipos]
    colores = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
    plt.bar(tipos, victorias, color=colores, edgecolor='black')
    plt.xlabel('Tipo de Cartón', fontsize=12)
    plt.ylabel('Victorias', fontsize=12)
    plt.title('Distribución de Victorias por Tipo de Cartón', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(carpeta, 'distribucion_cartones.png'), dpi=150)
    plt.close()
    
    print(f"[✓] Gráficos generados en: {carpeta}/")

# =====================================================================
# === RESUMEN EN CONSOLA ===
# =====================================================================

def imprimir_resumen(estadisticas: dict, carpeta_destino: str, nombre_simulacion: str, archivo_corel: str):
    """Imprime resumen de la simulación en consola."""
    
    e = estadisticas
    top_bingo = e['frecuencia_bingos'].most_common(1)
    top_carton = e['frecuencia_cartones'].most_common(1)
    
    print(f"""
============================================
       RESUMEN DE SIMULACIÓN DE BINGO
============================================
Archivo analizado:     {archivo_corel}
Total de jugadas:      {e['total_jugadas']}

--- Bolillas hasta el primer BINGO ---
  Mínimo:              {e['bolillas']['min']}
  Máximo:              {e['bolillas']['max']}
  Media:               {e['bolillas']['media']:.2f}
  Mediana:             {e['bolillas']['mediana']:.1f}
  Desviación estándar: {e['bolillas']['desviacion']:.2f}

--- Ganadores por Jugada ---
  Promedio:            {e['ganadores_por_jugada']['media']:.2f}
  Máximo simultáneo:   {e['ganadores_por_jugada']['max']}

--- Ranking de Ganadores ---
  Bingo más ganador:   {top_bingo[0][0] if top_bingo else 'N/A'} ({top_bingo[0][1] if top_bingo else 0} victorias)
  Cartón más ganador:  Tipo {top_carton[0][0] if top_carton else 'N/A'} ({top_carton[0][1] if top_carton else 0} victorias)

--- Carpeta de Salida ---
  {carpeta_destino}/
    ✓ {nombre_simulacion}_resultados.csv
    ✓ graficos/histograma_bolillas.png
    ✓ graficos/ganadores_por_jugada.png
    ✓ graficos/ranking_bingos.png
    ✓ graficos/distribucion_cartones.png
============================================
""")

# =====================================================================
# === EJECUCIÓN PRINCIPAL ===
# =====================================================================

def main():
    print("=" * 50)
    print("   SIMULADOR DE JUGADAS DE BINGO v1.1")
    print("=" * 50)
    
    # Parsear argumentos
    args = parsear_argumentos()
    
    # Buscar archivo Corel si no se especificó
    archivo_corel = args.archivo or buscar_archivo_corel()
    
    if not os.path.exists(archivo_corel):
        print(f"\n[✗] ERROR: No se encontró el archivo: {archivo_corel}")
        return
    
    # Generar nombres de carpeta y archivo de salida
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    nombre_simulacion = f'Simulacion_{args.jugadas}_{fecha_hoy}'
    carpeta_destino = os.path.join(args.carpeta_salida, nombre_simulacion)
    carpeta_graficos = os.path.join(carpeta_destino, 'graficos')
    archivo_csv = os.path.join(carpeta_destino, f'{nombre_simulacion}_resultados.csv')
    
    # Paso 1: Crear carpetas
    crear_carpetas(carpeta_destino, carpeta_graficos)
    
    # Paso 2: Cargar cartones
    cartones = cargar_cartones_corel(archivo_corel)
    
    # Paso 3: Ejecutar simulación
    resultados = ejecutar_simulacion(cartones, args.jugadas, args.seed)
    
    # Paso 4: Calcular estadísticas
    print("\nCalculando estadísticas...")
    estadisticas = calcular_estadisticas(resultados)
    print("[✓] Estadísticas calculadas")
    
    # Paso 5: Exportar CSV
    print("\nExportando resultados...")
    exportar_resultados_csv(resultados, archivo_csv)
    
    # Paso 6: Generar gráficos
    print("\nGenerando gráficos...")
    generar_graficos(resultados, estadisticas, carpeta_graficos)
    
    # Paso 7: Mostrar resumen
    imprimir_resumen(estadisticas, carpeta_destino, nombre_simulacion, archivo_corel)


if __name__ == "__main__":
    main()
