"""
Servicio de Generación de Bingos
================================
Lógica refactorizada para uso en web y CLI.
"""

import random
import os
import pandas as pd
from math import comb
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any


@dataclass
class ConfiguracionBingo:
    """Configuración para la generación de bingos."""
    seed: int
    numero_de_bingos: int
    numeros_por_carton: int = 10
    numero_maximo: int = 60
    cartones_por_bingo: int = 3
    bingos_por_fila: int = 2
    nombre_base: str = 'Bingos'
    carpeta_salida: str = 'bingos'


@dataclass
class ResultadoGeneracion:
    """Resultado de una generación de bingos."""
    exito: bool
    mensaje: str
    carpeta_destino: str = ''
    archivo_simple: str = ''
    archivo_corel: str = ''
    archivo_info: str = ''
    combinaciones_generadas: int = 0
    filas_corel: int = 0
    auditoria_pasada: bool = False
    verificaciones: List[Dict[str, Any]] = None
    df_simple: pd.DataFrame = None
    df_corel: pd.DataFrame = None


def validar_configuracion(config: ConfiguracionBingo) -> Tuple[bool, List[str]]:
    """Valida que la configuración sea matemáticamente posible y coherente."""
    errores = []
    
    if config.numero_de_bingos <= 0:
        errores.append("NUMERO_DE_BINGOS debe ser mayor a 0")
    if config.numeros_por_carton <= 0:
        errores.append("NUMEROS_POR_CARTON debe ser mayor a 0")
    if config.numero_maximo <= 0:
        errores.append("NUMERO_MAXIMO debe ser mayor a 0")
    
    if config.numeros_por_carton > config.numero_maximo:
        errores.append(f"NUMEROS_POR_CARTON ({config.numeros_por_carton}) no puede ser mayor que NUMERO_MAXIMO ({config.numero_maximo})")
    
    if config.numero_de_bingos % config.bingos_por_fila != 0:
        errores.append(f"NUMERO_DE_BINGOS ({config.numero_de_bingos}) debe ser divisible por BINGOS_POR_FILA ({config.bingos_por_fila})")
    
    combinaciones_necesarias = config.numero_de_bingos * config.cartones_por_bingo
    max_combinaciones = comb(config.numero_maximo, config.numeros_por_carton)
    
    if combinaciones_necesarias > max_combinaciones:
        errores.append(
            f"Imposible generar {combinaciones_necesarias} combinaciones. "
            f"Máximo posible: {max_combinaciones:,}"
        )
    
    return len(errores) == 0, errores


def generar_combinaciones(config: ConfiguracionBingo, callback=None) -> List[Tuple[int, ...]]:
    """Genera combinaciones únicas de cartones."""
    random.seed(config.seed)
    cartones_unicos = set()
    combinaciones_necesarias = config.numero_de_bingos * config.cartones_por_bingo
    
    while len(cartones_unicos) < combinaciones_necesarias:
        carton = tuple(sorted(random.sample(range(1, config.numero_maximo + 1), config.numeros_por_carton)))
        cartones_unicos.add(carton)
        
        if callback and len(cartones_unicos) % 500 == 0:
            callback(len(cartones_unicos), combinaciones_necesarias)
    
    return list(cartones_unicos)


def crear_dataframe_simple(cartones_lista: List[Tuple[int, ...]], config: ConfiguracionBingo) -> pd.DataFrame:
    """Crea DataFrame en formato simple (1 fila = 1 cartón)."""
    df = pd.DataFrame(cartones_lista)
    df.columns = [f'Num_{i+1}' for i in range(config.numeros_por_carton)]
    df.index.name = 'ID_Carton'
    df.index = df.index + 1
    return df


def crear_dataframe_corel(cartones_lista: List[Tuple[int, ...]], config: ConfiguracionBingo) -> pd.DataFrame:
    """Crea DataFrame en formato Corel (2 bingos por fila, 3 cartones cada uno)."""
    filas_corel = config.numero_de_bingos // config.bingos_por_fila
    inicio_carton_2 = config.numero_de_bingos // 2 + 1
    
    filas_agrupadas = []
    idx_carton1 = 1
    idx_carton2 = inicio_carton_2
    
    for fila in range(filas_corel):
        base_izq = fila * config.cartones_por_bingo
        base_der = (filas_corel + fila) * config.cartones_por_bingo
        
        fila_datos = []
        
        # CARTON 1 (izquierda): A, B, C
        fila_datos.append(f"{idx_carton1:04d}")
        for i in range(config.cartones_por_bingo):
            fila_datos.extend(cartones_lista[base_izq + i])
        
        # CARTON 2 (derecha): D, E, F
        fila_datos.append(f"{idx_carton2:04d}")
        for i in range(config.cartones_por_bingo):
            fila_datos.extend(cartones_lista[base_der + i])
        
        filas_agrupadas.append(fila_datos)
        idx_carton1 += 1
        idx_carton2 += 1
    
    # Crear encabezados
    columnas = ['CARTON 1']
    for letra in ['A', 'B', 'C']:
        columnas.extend([f'{letra}{i}' for i in range(1, config.numeros_por_carton + 1)])
    columnas.append('CARTON 2')
    for letra in ['D', 'E', 'F']:
        columnas.extend([f'{letra}{i}' for i in range(1, config.numeros_por_carton + 1)])
    
    return pd.DataFrame(filas_agrupadas, columns=columnas)


def ejecutar_auditoria(df_simple: pd.DataFrame, df_corel: pd.DataFrame, config: ConfiguracionBingo) -> Tuple[bool, List[Dict[str, Any]]]:
    """Ejecuta verificaciones de integridad."""
    verificaciones = []
    combinaciones_necesarias = config.numero_de_bingos * config.cartones_por_bingo
    filas_corel = config.numero_de_bingos // config.bingos_por_fila
    
    # 1. Cantidad total
    ok = len(df_simple) == combinaciones_necesarias
    verificaciones.append({
        'nombre': 'Cantidad de combinaciones',
        'ok': ok,
        'detalle': f'{len(df_simple)} de {combinaciones_necesarias}'
    })
    
    # 2. Números por cartón
    ok = df_simple.shape[1] == config.numeros_por_carton
    verificaciones.append({
        'nombre': 'Números por cartón',
        'ok': ok,
        'detalle': f'{df_simple.shape[1]} de {config.numeros_por_carton}'
    })
    
    # 3. Unicidad
    ok = len(df_simple) == df_simple.drop_duplicates().shape[0]
    verificaciones.append({
        'nombre': 'Combinaciones únicas',
        'ok': ok,
        'detalle': 'Sin duplicados' if ok else 'Hay duplicados'
    })
    
    # 4. Rango
    valor_min = df_simple.min().min()
    valor_max = df_simple.max().max()
    ok = valor_min >= 1 and valor_max <= config.numero_maximo
    verificaciones.append({
        'nombre': 'Rango de números',
        'ok': ok,
        'detalle': f'[{valor_min}, {valor_max}]'
    })
    
    # 5. Sin repetidos internos
    ok = df_simple.apply(lambda row: len(row) == len(set(row)), axis=1).all()
    verificaciones.append({
        'nombre': 'Sin repetidos internos',
        'ok': ok,
        'detalle': 'OK' if ok else 'Hay repetidos'
    })
    
    # 6. Filas Corel
    ok = len(df_corel) == filas_corel
    verificaciones.append({
        'nombre': 'Filas Corel',
        'ok': ok,
        'detalle': f'{len(df_corel)} de {filas_corel}'
    })
    
    todas_ok = all(v['ok'] for v in verificaciones)
    return todas_ok, verificaciones


def generar_metadatos(config: ConfiguracionBingo, carpeta_destino: str, archivos: Dict[str, str]) -> str:
    """Genera contenido del archivo de metadatos."""
    combinaciones = config.numero_de_bingos * config.cartones_por_bingo
    filas_corel = config.numero_de_bingos // config.bingos_por_fila
    inicio_carton_2 = config.numero_de_bingos // 2 + 1
    fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return f"""============================================
     METADATOS DE GENERACIÓN DE BINGOS
============================================
Fecha y hora:          {fecha_hora}
Seed:                  {config.seed}

Configuración:
  Bingos físicos:      {config.numero_de_bingos}
  Cartones por bingo:  {config.cartones_por_bingo}
  Combinaciones:       {combinaciones}
  Números por cartón:  {config.numeros_por_carton}
  Rango de números:    1 - {config.numero_maximo}

Numeración:
  CARTON 1:            0001 - {filas_corel:04d}
  CARTON 2:            {inicio_carton_2:04d} - {config.numero_de_bingos:04d}

Archivos generados:
  - {os.path.basename(archivos['simple'])}
  - {os.path.basename(archivos['corel'])}
  - {os.path.basename(archivos['info'])}
============================================
"""


def generar_bingos(config: ConfiguracionBingo, callback=None) -> ResultadoGeneracion:
    """
    Función principal para generar bingos.
    
    Args:
        config: Configuración de generación
        callback: Función opcional para reportar progreso
    
    Returns:
        ResultadoGeneracion con todos los datos y archivos
    """
    # Validar configuración
    valido, errores = validar_configuracion(config)
    if not valido:
        return ResultadoGeneracion(
            exito=False,
            mensaje="Errores de configuración: " + "; ".join(errores)
        )
    
    # Preparar rutas
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    nombre_subcarpeta = f'{config.nombre_base}_{config.numero_de_bingos}_{fecha_hoy}'
    carpeta_destino = os.path.join(config.carpeta_salida, nombre_subcarpeta)
    
    archivo_simple = os.path.join(carpeta_destino, f'{nombre_subcarpeta}_simple.csv')
    archivo_corel = os.path.join(carpeta_destino, f'{nombre_subcarpeta}_corel.csv')
    archivo_info = os.path.join(carpeta_destino, f'{nombre_subcarpeta}_info.txt')
    
    # Crear carpeta
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    # Generar combinaciones
    cartones_lista = generar_combinaciones(config, callback)
    
    # Crear DataFrames
    df_simple = crear_dataframe_simple(cartones_lista, config)
    df_corel = crear_dataframe_corel(cartones_lista, config)
    
    # Guardar archivos
    df_simple.to_csv(archivo_simple, sep=';', encoding='utf-8')
    df_corel.to_csv(archivo_corel, sep=';', index=False, encoding='utf-8')
    
    archivos = {'simple': archivo_simple, 'corel': archivo_corel, 'info': archivo_info}
    metadatos = generar_metadatos(config, carpeta_destino, archivos)
    
    with open(archivo_info, 'w', encoding='utf-8') as f:
        f.write(metadatos)
    
    # Auditoría
    auditoria_ok, verificaciones = ejecutar_auditoria(df_simple, df_corel, config)
    
    return ResultadoGeneracion(
        exito=True,
        mensaje="Generación completada exitosamente",
        carpeta_destino=carpeta_destino,
        archivo_simple=archivo_simple,
        archivo_corel=archivo_corel,
        archivo_info=archivo_info,
        combinaciones_generadas=len(cartones_lista),
        filas_corel=len(df_corel),
        auditoria_pasada=auditoria_ok,
        verificaciones=verificaciones,
        df_simple=df_simple,
        df_corel=df_corel
    )


def obtener_generaciones_existentes(carpeta_salida: str = 'bingos') -> List[Dict[str, Any]]:
    """Obtiene lista de generaciones existentes."""
    generaciones = []
    
    if not os.path.exists(carpeta_salida):
        return generaciones
    
    for nombre in os.listdir(carpeta_salida):
        ruta = os.path.join(carpeta_salida, nombre)
        if os.path.isdir(ruta):
            archivo_corel = os.path.join(ruta, f'{nombre}_corel.csv')
            archivo_info = os.path.join(ruta, f'{nombre}_info.txt')
            
            if os.path.exists(archivo_corel):
                # Extraer información del nombre
                partes = nombre.split('_')
                generaciones.append({
                    'nombre': nombre,
                    'ruta': ruta,
                    'archivo_corel': archivo_corel,
                    'archivo_info': archivo_info if os.path.exists(archivo_info) else None,
                    'fecha_modificacion': datetime.fromtimestamp(os.path.getmtime(archivo_corel))
                })
    
    # Ordenar por fecha (más reciente primero)
    generaciones.sort(key=lambda x: x['fecha_modificacion'], reverse=True)
    
    return generaciones
