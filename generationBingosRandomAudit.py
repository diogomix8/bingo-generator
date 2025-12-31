"""
Generador de Bingos Aleatorios con Doble Salida
================================================
Genera combinaciones únicas de bingo y exporta en dos formatos:
- Simple: 1 fila = 1 cartón (para auditoría)
- Corel: 2 bingos por fila con 3 cartones cada uno (para diseño)

Autor: DiogoMix8
Versión: 2.0
"""

import pandas as pd
import random
import os
from math import comb
from datetime import datetime

# =====================================================================
# === CONFIGURACIÓN PRINCIPAL ===
# =====================================================================

# Semilla para reproducibilidad (cambiar para generar diferentes juegos)
SEED = 31122025

# Cantidad de bingos físicos a generar (parámetro principal)
NUMERO_DE_BINGOS = 1200

# Configuración del cartón
NUMEROS_POR_CARTON = 10      # Números por cada cartón individual
NUMERO_MAXIMO = 60           # Rango de números: 1 a NUMERO_MAXIMO

# Configuración de agrupación
CARTONES_POR_BINGO = 3       # Cartones por bingo físico (A, B, C)
BINGOS_POR_FILA = 2          # Bingos lado a lado en formato Corel

# Configuración de exportación
CARPETA_SALIDA = 'bingos'         # Carpeta principal de salida
SEPARADOR_CSV = ';'
NOMBRE_BASE = 'Bingos'
ENCODING = 'utf-8'

# =====================================================================
# === CÁLCULOS AUTOMÁTICOS ===
# =====================================================================

# Calcular valores derivados
COMBINACIONES_NECESARIAS = NUMERO_DE_BINGOS * CARTONES_POR_BINGO
FILAS_COREL = NUMERO_DE_BINGOS // BINGOS_POR_FILA
INICIO_CARTON_2 = NUMERO_DE_BINGOS // 2 + 1

# Generar fecha para nombres de archivo
FECHA_HOY = datetime.now().strftime('%Y%m%d')
FECHA_HORA_COMPLETA = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Nombre de la subcarpeta (incluye nombre base)
NOMBRE_SUBCARPETA = f'{NOMBRE_BASE}_{NUMERO_DE_BINGOS}_{FECHA_HOY}'
CARPETA_DESTINO = os.path.join(CARPETA_SALIDA, NOMBRE_SUBCARPETA)

# Nombres de archivos (rutas completas)
ARCHIVO_SIMPLE = os.path.join(CARPETA_DESTINO, f'{NOMBRE_SUBCARPETA}_simple.csv')
ARCHIVO_COREL = os.path.join(CARPETA_DESTINO, f'{NOMBRE_SUBCARPETA}_corel.csv')
ARCHIVO_INFO = os.path.join(CARPETA_DESTINO, f'{NOMBRE_SUBCARPETA}_info.txt')

# =====================================================================
# === VALIDACIONES ===
# =====================================================================

def validar_configuracion():
    """Valida que la configuración sea matemáticamente posible y coherente."""
    errores = []
    
    # Validar parámetros positivos
    if NUMERO_DE_BINGOS <= 0:
        errores.append("NUMERO_DE_BINGOS debe ser mayor a 0")
    if NUMEROS_POR_CARTON <= 0:
        errores.append("NUMEROS_POR_CARTON debe ser mayor a 0")
    if NUMERO_MAXIMO <= 0:
        errores.append("NUMERO_MAXIMO debe ser mayor a 0")
    
    # Validar que se puedan formar cartones
    if NUMEROS_POR_CARTON > NUMERO_MAXIMO:
        errores.append(f"NUMEROS_POR_CARTON ({NUMEROS_POR_CARTON}) no puede ser mayor que NUMERO_MAXIMO ({NUMERO_MAXIMO})")
    
    # Validar divisibilidad para formato Corel
    if NUMERO_DE_BINGOS % BINGOS_POR_FILA != 0:
        errores.append(f"NUMERO_DE_BINGOS ({NUMERO_DE_BINGOS}) debe ser divisible por BINGOS_POR_FILA ({BINGOS_POR_FILA})")
    
    # Validar factibilidad matemática
    max_combinaciones = comb(NUMERO_MAXIMO, NUMEROS_POR_CARTON)
    if COMBINACIONES_NECESARIAS > max_combinaciones:
        errores.append(
            f"Imposible generar {COMBINACIONES_NECESARIAS} combinaciones. "
            f"Máximo posible con C({NUMERO_MAXIMO},{NUMEROS_POR_CARTON}): {max_combinaciones:,}"
        )
    
    if errores:
        print("\n" + "=" * 50)
        print("ERRORES DE CONFIGURACIÓN")
        print("=" * 50)
        for error in errores:
            print(f"  ✗ {error}")
        print("=" * 50)
        raise ValueError("Configuración inválida. Corrige los errores anteriores.")
    
    # Mostrar información de factibilidad
    porcentaje_uso = (COMBINACIONES_NECESARIAS / max_combinaciones) * 100
    print(f"\n[✓] Configuración validada")
    print(f"    Combinaciones posibles: {max_combinaciones:,}")
    print(f"    Combinaciones a generar: {COMBINACIONES_NECESARIAS:,}")
    print(f"    Uso del espacio: {porcentaje_uso:.6f}%")

# =====================================================================
# === CREAR CARPETAS ===
# =====================================================================

def crear_carpetas():
    """Crea la estructura de carpetas si no existe."""
    if not os.path.exists(CARPETA_DESTINO):
        os.makedirs(CARPETA_DESTINO)
        print(f"[✓] Carpeta creada: {CARPETA_DESTINO}")
    else:
        print(f"[i] Carpeta existente: {CARPETA_DESTINO}")

# =====================================================================
# === VERIFICAR SOBRESCRITURA ===
# =====================================================================

def verificar_archivos_existentes():
    """Verifica si los archivos de salida ya existen y pide confirmación."""
    archivos_existentes = []
    
    for archivo in [ARCHIVO_SIMPLE, ARCHIVO_COREL, ARCHIVO_INFO]:
        if os.path.exists(archivo):
            archivos_existentes.append(archivo)
    
    if archivos_existentes:
        print("\n" + "=" * 50)
        print("⚠️  ADVERTENCIA: Los siguientes archivos ya existen:")
        print("=" * 50)
        for archivo in archivos_existentes:
            print(f"    - {archivo}")
        print("=" * 50)
        
        respuesta = input("\n¿Deseas sobrescribirlos? (s/n): ").strip().lower()
        if respuesta != 's':
            print("\nOperación cancelada por el usuario.")
            raise SystemExit(0)
        print()

# =====================================================================
# === GENERACIÓN DE COMBINACIONES ===
# =====================================================================

def generar_combinaciones():
    """Genera las combinaciones únicas de cartones."""
    random.seed(SEED)
    cartones_unicos = set()
    
    print(f"\nGenerando {COMBINACIONES_NECESARIAS} combinaciones únicas...")
    
    while len(cartones_unicos) < COMBINACIONES_NECESARIAS:
        carton = tuple(sorted(random.sample(range(1, NUMERO_MAXIMO + 1), NUMEROS_POR_CARTON)))
        cartones_unicos.add(carton)
        
        # Indicador de progreso cada 500 cartones
        if len(cartones_unicos) % 500 == 0:
            print(f"    Progreso: {len(cartones_unicos)}/{COMBINACIONES_NECESARIAS}")
    
    print(f"[✓] Generación completa: {len(cartones_unicos)} combinaciones únicas")
    return list(cartones_unicos)

# =====================================================================
# === EXPORTACIÓN FORMATO SIMPLE ===
# =====================================================================

def exportar_formato_simple(cartones_lista):
    """Exporta las combinaciones en formato simple (1 fila = 1 cartón)."""
    df = pd.DataFrame(cartones_lista)
    df.columns = [f'Num_{i+1}' for i in range(NUMEROS_POR_CARTON)]
    df.index.name = 'ID_Carton'
    df.index = df.index + 1
    
    try:
        df.to_csv(ARCHIVO_SIMPLE, sep=SEPARADOR_CSV, encoding=ENCODING)
        print(f"[✓] Archivo simple exportado: {ARCHIVO_SIMPLE}")
        return df
    except PermissionError:
        print(f"[✗] ERROR: No se puede escribir '{ARCHIVO_SIMPLE}'. ¿Está abierto en otro programa?")
        raise

# =====================================================================
# === EXPORTACIÓN FORMATO COREL ===
# =====================================================================

def exportar_formato_corel(cartones_lista):
    """Exporta las combinaciones en formato Corel (2 bingos por fila, 3 cartones cada uno)."""
    filas_agrupadas = []
    
    # Índices de numeración
    idx_carton1 = 1
    idx_carton2 = INICIO_CARTON_2
    
    for fila in range(FILAS_COREL):
        # Calcular índices base para esta fila
        base_izq = fila * CARTONES_POR_BINGO
        base_der = (FILAS_COREL + fila) * CARTONES_POR_BINGO
        
        fila_datos = []
        
        # CARTON 1 (izquierda): A, B, C
        fila_datos.append(f"{idx_carton1:04d}")
        for i in range(CARTONES_POR_BINGO):
            fila_datos.extend(cartones_lista[base_izq + i])
        
        # CARTON 2 (derecha): D, E, F
        fila_datos.append(f"{idx_carton2:04d}")
        for i in range(CARTONES_POR_BINGO):
            fila_datos.extend(cartones_lista[base_der + i])
        
        filas_agrupadas.append(fila_datos)
        idx_carton1 += 1
        idx_carton2 += 1
    
    # Crear encabezados
    columnas = ['CARTON 1']
    for letra in ['A', 'B', 'C']:
        columnas.extend([f'{letra}{i}' for i in range(1, NUMEROS_POR_CARTON + 1)])
    columnas.append('CARTON 2')
    for letra in ['D', 'E', 'F']:
        columnas.extend([f'{letra}{i}' for i in range(1, NUMEROS_POR_CARTON + 1)])
    
    df = pd.DataFrame(filas_agrupadas, columns=columnas)
    
    try:
        df.to_csv(ARCHIVO_COREL, sep=SEPARADOR_CSV, index=False, encoding=ENCODING)
        print(f"[✓] Archivo Corel exportado: {ARCHIVO_COREL}")
        return df
    except PermissionError:
        print(f"[✗] ERROR: No se puede escribir '{ARCHIVO_COREL}'. ¿Está abierto en otro programa?")
        raise

# =====================================================================
# === EXPORTACIÓN ARCHIVO DE METADATOS ===
# =====================================================================

def exportar_metadatos():
    """Genera archivo de texto con metadatos de la generación."""
    contenido = f"""============================================
     METADATOS DE GENERACIÓN DE BINGOS
============================================
Fecha y hora:          {FECHA_HORA_COMPLETA}
Seed:                  {SEED}

Configuración:
  Bingos físicos:      {NUMERO_DE_BINGOS}
  Cartones por bingo:  {CARTONES_POR_BINGO}
  Combinaciones:       {COMBINACIONES_NECESARIAS}
  Números por cartón:  {NUMEROS_POR_CARTON}
  Rango de números:    1 - {NUMERO_MAXIMO}

Numeración:
  CARTON 1:            0001 - {FILAS_COREL:04d}
  CARTON 2:            {INICIO_CARTON_2:04d} - {NUMERO_DE_BINGOS:04d}

Archivos generados:
  - {ARCHIVO_SIMPLE}
  - {ARCHIVO_COREL}
  - {ARCHIVO_INFO}
============================================
"""
    
    try:
        with open(ARCHIVO_INFO, 'w', encoding=ENCODING) as f:
            f.write(contenido)
        print(f"[✓] Archivo de metadatos exportado: {ARCHIVO_INFO}")
    except PermissionError:
        print(f"[✗] ERROR: No se puede escribir '{ARCHIVO_INFO}'. ¿Está abierto en otro programa?")
        raise

# =====================================================================
# === AUDITORÍA ===
# =====================================================================

def ejecutar_auditoria(df_simple, df_corel):
    """Ejecuta verificaciones de integridad en ambos archivos."""
    print("\n" + "=" * 50)
    print("AUDITORÍA AUTOMÁTICA")
    print("=" * 50)
    
    verificaciones_pasadas = 0
    total_verificaciones = 6
    
    # 1. Verificar cantidad total de combinaciones (simple)
    try:
        assert len(df_simple) == COMBINACIONES_NECESARIAS
        print(f"[✓] Verificación 1: Cantidad de combinaciones correcta ({len(df_simple)})")
        verificaciones_pasadas += 1
    except AssertionError:
        print(f"[✗] ERROR 1: Se generaron {len(df_simple)} en lugar de {COMBINACIONES_NECESARIAS}")
    
    # 2. Verificar números por cartón
    try:
        assert df_simple.shape[1] == NUMEROS_POR_CARTON
        print(f"[✓] Verificación 2: Números por cartón correctos ({df_simple.shape[1]})")
        verificaciones_pasadas += 1
    except AssertionError:
        print(f"[✗] ERROR 2: Hay {df_simple.shape[1]} números en lugar de {NUMEROS_POR_CARTON}")
    
    # 3. Verificar unicidad de combinaciones
    try:
        assert len(df_simple) == df_simple.drop_duplicates().shape[0]
        print("[✓] Verificación 3: Todas las combinaciones son únicas")
        verificaciones_pasadas += 1
    except AssertionError:
        print("[✗] ERROR 3: Se encontraron combinaciones duplicadas")
    
    # 4. Verificar rango de números
    try:
        valor_min = df_simple.min().min()
        valor_max = df_simple.max().max()
        assert valor_min >= 1 and valor_max <= NUMERO_MAXIMO
        print(f"[✓] Verificación 4: Rango correcto [{valor_min}, {valor_max}]")
        verificaciones_pasadas += 1
    except AssertionError:
        print(f"[✗] ERROR 4: Números fuera de rango [1, {NUMERO_MAXIMO}]")
    
    # 5. Verificar no hay repetidos dentro de cada cartón
    try:
        sin_duplicados = df_simple.apply(lambda row: len(row) == len(set(row)), axis=1).all()
        assert sin_duplicados
        print("[✓] Verificación 5: Sin números repetidos dentro de cartones")
        verificaciones_pasadas += 1
    except AssertionError:
        print("[✗] ERROR 5: Hay cartones con números internos repetidos")
    
    # 6. Verificar cantidad de filas en formato Corel
    try:
        assert len(df_corel) == FILAS_COREL
        print(f"[✓] Verificación 6: Filas Corel correctas ({len(df_corel)})")
        verificaciones_pasadas += 1
    except AssertionError:
        print(f"[✗] ERROR 6: Hay {len(df_corel)} filas en lugar de {FILAS_COREL}")
    
    print("=" * 50)
    
    return verificaciones_pasadas, total_verificaciones

# =====================================================================
# === RESUMEN FINAL ===
# =====================================================================

def imprimir_resumen(verificaciones_pasadas, total_verificaciones):
    """Imprime el resumen final de la generación."""
    estado_auditoria = "✓ PASADA" if verificaciones_pasadas == total_verificaciones else "✗ FALLIDA"
    
    print(f"""
============================================
           RESUMEN DE GENERACIÓN
============================================
Bingos físicos generados:  {NUMERO_DE_BINGOS}
Combinaciones totales:     {COMBINACIONES_NECESARIAS}
Filas formato Corel:       {FILAS_COREL}

Numeración CARTON 1:       0001 - {FILAS_COREL:04d}
Numeración CARTON 2:       {INICIO_CARTON_2:04d} - {NUMERO_DE_BINGOS:04d}

Carpeta de salida:         {CARPETA_DESTINO}/
Archivos generados:
  ✓ {NOMBRE_SUBCARPETA}_simple.csv  ({COMBINACIONES_NECESARIAS} filas)
  ✓ {NOMBRE_SUBCARPETA}_corel.csv   ({FILAS_COREL} filas)
  ✓ {NOMBRE_SUBCARPETA}_info.txt

Auditoría: {estado_auditoria} ({verificaciones_pasadas}/{total_verificaciones} verificaciones)
Seed utilizado: {SEED}
============================================
""")

# =====================================================================
# === EJECUCIÓN PRINCIPAL ===
# =====================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("   GENERADOR DE BINGOS ALEATORIOS v2.0")
    print("=" * 50)
    
    # Paso 1: Validar configuración
    validar_configuracion()
    
    # Paso 2: Crear carpetas
    crear_carpetas()
    
    # Paso 3: Verificar archivos existentes
    verificar_archivos_existentes()
    
    # Paso 4: Generar combinaciones
    cartones_lista = generar_combinaciones()
    
    # Paso 5: Exportar archivos
    print("\nExportando archivos...")
    df_simple = exportar_formato_simple(cartones_lista)
    df_corel = exportar_formato_corel(cartones_lista)
    exportar_metadatos()
    
    # Paso 6: Ejecutar auditoría
    verificaciones_pasadas, total = ejecutar_auditoria(df_simple, df_corel)
    
    # Paso 7: Mostrar resumen
    imprimir_resumen(verificaciones_pasadas, total)