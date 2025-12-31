# 🎱 Generador y Simulador de Bingos Aleatorios

Sistema completo para generar combinaciones únicas de cartones de bingo y simular jugadas con análisis estadístico.

## 📋 Descripción

Este proyecto consta de dos herramientas principales:

1. **Generador de Bingos** (`generationBingosRandomAudit.py`): Genera combinaciones únicas de cartones de bingo con auditoría automática.
2. **Simulador de Jugadas** (`simuladorBingos.py`): Simula jugadas aleatorias y genera estadísticas detalladas con gráficos.

## 📁 Estructura del Proyecto

```
📁 Generación de Bingos Aleatorios/
├── 📄 generationBingosRandomAudit.py   # Generador principal
├── 📄 simuladorBingos.py               # Simulador de jugadas
├── 📄 README.md                        # Este archivo
├── 📁 bingos/                          # Resultados del generador
│   └── 📁 Bingos_1000_20251231/
│       ├── Bingos_1000_20251231_simple.csv
│       ├── Bingos_1000_20251231_corel.csv
│       └── Bingos_1000_20251231_info.txt
└── 📁 simulaciones/                    # Resultados del simulador
    └── 📁 Simulacion_50_20251231/
        ├── Simulacion_50_20251231_resultados.csv
        └── 📁 graficos/
            ├── histograma_bolillas.png
            ├── ganadores_por_jugada.png
            ├── ranking_bingos.png
            └── distribucion_cartones.png
```

## 🔧 Requisitos

- Python 3.8+
- Librerías:
  ```bash
  pip install pandas numpy matplotlib
  ```

## 🎰 Generador de Bingos

### Uso Básico

```bash
python generationBingosRandomAudit.py
```

### Configuración

Edita las constantes al inicio del archivo `generationBingosRandomAudit.py`:

```python
# === CONFIGURACIÓN PRINCIPAL ===

SEED = 31122025              # Semilla para reproducibilidad
NUMERO_DE_BINGOS = 1000      # Cantidad de bingos físicos a generar
NUMEROS_POR_CARTON = 10      # Números por cartón individual
NUMERO_MAXIMO = 60           # Rango: 1 a 60
CARTONES_POR_BINGO = 3       # Cartones por bingo físico (A, B, C)
BINGOS_POR_FILA = 2          # Bingos lado a lado en formato Corel
CARPETA_SALIDA = 'bingos'    # Carpeta de salida
NOMBRE_BASE = 'Bingos'       # Prefijo de archivos
```

### Archivos Generados

| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `*_simple.csv` | 1 fila = 1 cartón (3000 filas) | Auditoría, verificación |
| `*_corel.csv` | 2 bingos por fila, 3 cartones cada uno (500 filas) | Importar en Corel Draw |
| `*_info.txt` | Metadatos de la generación | Trazabilidad |

### Formato Corel

Cada fila del archivo Corel tiene 62 columnas:

```
CARTON 1 | A1-A10 | B1-B10 | C1-C10 | CARTON 2 | D1-D10 | E1-E10 | F1-F10
```

- **CARTON 1**: ID del bingo izquierdo (0001, 0002, ...)
- **A, B, C**: 3 cartones del bingo izquierdo (10 números cada uno)
- **CARTON 2**: ID del bingo derecho (0501, 0502, ...)
- **D, E, F**: 3 cartones del bingo derecho (10 números cada uno)

### Ejemplo de Salida

```
============================================
           RESUMEN DE GENERACIÓN
============================================
Bingos físicos generados:  1000
Combinaciones totales:     3000
Filas formato Corel:       500

Numeración CARTON 1:       0001 - 0500
Numeración CARTON 2:       0501 - 1000

Carpeta de salida:         bingos/Bingos_1000_20251231/
Archivos generados:
  ✓ Bingos_1000_20251231_simple.csv  (3000 filas)
  ✓ Bingos_1000_20251231_corel.csv   (500 filas)
  ✓ Bingos_1000_20251231_info.txt

Auditoría: ✓ PASADA (6/6 verificaciones)
Seed utilizado: 31122025
============================================
```

---

## 🎲 Simulador de Jugadas

### Uso Básico

```bash
# Con valores por defecto (50 jugadas, archivo Corel más reciente)
python simuladorBingos.py

# Personalizado
python simuladorBingos.py --jugadas 100 --seed 12345

# Con archivo específico
python simuladorBingos.py --archivo bingos/Bingos_1000_20251231/Bingos_1000_20251231_corel.csv
```

### Argumentos de Línea de Comandos

| Argumento | Abreviación | Descripción | Default |
|-----------|-------------|-------------|---------|
| `--jugadas` | `-j` | Número de jugadas a simular | 50 |
| `--archivo` | `-a` | Archivo CSV Corel a usar | Auto-detecta el más reciente |
| `--seed` | `-s` | Semilla para reproducibilidad | Aleatorio |
| `--carpeta-salida` | `-o` | Carpeta para resultados | `simulaciones` |

### Lógica de Simulación

Cada jugada:
1. Genera orden aleatorio de bolillas (1-60)
2. "Canta" bolillas una por una
3. Marca aciertos en cada cartón
4. Cuando un cartón completa 10/10 → **¡BINGO!**
5. Registra estadísticas del ganador

### Archivos Generados

| Archivo | Descripción |
|---------|-------------|
| `*_resultados.csv` | Detalle por jugada: bolillas, ganadores, IDs |
| `histograma_bolillas.png` | Distribución de bolillas hasta primer BINGO |
| `ganadores_por_jugada.png` | Cantidad de ganadores simultáneos |
| `ranking_bingos.png` | Top 10 bingos más ganadores |
| `distribucion_cartones.png` | Victorias por tipo de cartón (A-F) |

### Ejemplo de Salida

```
============================================
       RESUMEN DE SIMULACIÓN DE BINGO
============================================
Archivo analizado:     bingos/Bingos_1000_20251231/Bingos_1000_20251231_corel.csv
Total de jugadas:      50

--- Bolillas hasta el primer BINGO ---
  Mínimo:              20
  Máximo:              33
  Media:               28.44
  Mediana:             29.0
  Desviación estándar: 2.77

--- Ganadores por Jugada ---
  Promedio:            1.14
  Máximo simultáneo:   3

--- Ranking de Ganadores ---
  Bingo más ganador:   0758 (1 victorias)
  Cartón más ganador:  Tipo A (14 victorias)
============================================
```

---

## 📊 Estadísticas Generadas

### Del Simulador

- **Bolillas hasta ganador**: Min, Max, Media, Mediana, Desviación estándar
- **Ganadores simultáneos**: Cuántos cartones ganan en la misma bolilla
- **Frecuencia por bingo**: Qué bingos físicos ganan más
- **Frecuencia por tipo**: Qué cartón (A, B, C, D, E, F) gana más

---

## 🔐 Reproducibilidad

Ambos scripts soportan semillas (seeds) para generar resultados reproducibles:

```python
# Generador
SEED = 31122025  # Misma seed = mismas combinaciones

# Simulador
python simuladorBingos.py --seed 12345  # Misma seed = mismas jugadas
```

---

## 📝 Auditoría Automática

El generador incluye 6 verificaciones automáticas:

1. ✓ Cantidad total de combinaciones correcta
2. ✓ Números por cartón correctos (10)
3. ✓ Todas las combinaciones son únicas
4. ✓ Números dentro del rango [1, 60]
5. ✓ Sin números repetidos dentro de cada cartón
6. ✓ Filas formato Corel correctas

---

## 🎨 Integración con Corel Draw

El archivo `*_corel.csv` está diseñado para importarse directamente en Corel Draw:

1. Abrir Corel Draw
2. Ir a **Archivo > Importar**
3. Seleccionar el archivo CSV
4. Usar separador `;` (punto y coma)
5. Mapear columnas a campos de texto del diseño

---

## 📈 Fórmulas Matemáticas

### Combinaciones Posibles

$$C(n, k) = \binom{60}{10} = 75,394,027,566$$

Con 60 números y 10 por cartón, hay más de **75 mil millones** de combinaciones posibles.

### Cálculo de Bingos

| Parámetro | Fórmula | Ejemplo |
|-----------|---------|---------|
| Combinaciones totales | `NUMERO_DE_BINGOS × CARTONES_POR_BINGO` | 1000 × 3 = 3000 |
| Filas Corel | `NUMERO_DE_BINGOS / BINGOS_POR_FILA` | 1000 / 2 = 500 |
| Inicio CARTON 2 | `NUMERO_DE_BINGOS / 2 + 1` | 1000 / 2 + 1 = 501 |

---

## 🐛 Solución de Problemas

### Error: "No se encontró ningún archivo *_corel.csv"

Ejecuta primero el generador:
```bash
python generationBingosRandomAudit.py
```

### Error: "No module named 'matplotlib'"

Instala las dependencias:
```bash
pip install pandas numpy matplotlib
```

### Error: "No se puede escribir el archivo"

Cierra el archivo CSV si está abierto en Excel u otro programa.

---

## ☁️ Despliegue en la Nube (Render)

Esta aplicación está preparada para desplegarse gratuitamente en [Render](https://render.com).

### Requisitos Previos

1. Cuenta en [GitHub](https://github.com) con el repositorio del proyecto
2. Cuenta en [Render](https://render.com) (puedes registrarte con GitHub)

### Pasos para Desplegar

1. **Iniciar sesión en Render** → [render.com](https://render.com)

2. **Crear nuevo Web Service:**
   - Click en **"New +"** → **"Web Service"**
   - Conectar tu repositorio de GitHub
   - Seleccionar `diogomix8/bingo-generator`

3. **Configurar el servicio:**

   | Campo | Valor |
   |-------|-------|
   | **Name** | `bingo-generator` (o el nombre que prefieras) |
   | **Region** | El más cercano a ti |
   | **Branch** | `main` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app` |
   | **Plan** | `Free` |

4. **Configurar variables de entorno:**
   - En la sección **"Environment"** → **"Add Environment Variable"**
   
   | Variable | Valor |
   |----------|-------|
   | `SECRET_KEY` | Generar con: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `FLASK_DEBUG` | `False` |

5. **Click en "Create Web Service"** → Render desplegará automáticamente

6. **Acceder a la aplicación:**
   - Render asignará una URL como: `https://bingo-generator.onrender.com`

### ⚠️ Limitaciones del Tier Gratuito

- La app se "duerme" tras **15 minutos de inactividad**
- El primer request tras dormir tarda **~30 segundos**
- Almacenamiento **efímero** (archivos generados se pierden al reiniciar)
- Los archivos de bingos/simulaciones se pueden descargar mientras la sesión esté activa

### Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `requirements.txt` | Dependencias Python |
| `Procfile` | Comando de inicio para Render |
| `.env.example` | Plantilla de variables de entorno |

---

## 👤 Autor

**DiogoMix8**

---

## 📄 Licencia

Uso libre para proyectos personales y comerciales.
