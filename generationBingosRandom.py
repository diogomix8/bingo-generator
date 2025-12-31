import pandas as pd
import random

# --- Parámetros del Bingo ---
numero_de_cartones = 1800
numeros_por_carton = 10
numero_maximo = 60
# --------------------------

cartones_unicos = set()

while len(cartones_unicos) < numero_de_cartones:
    carton = tuple(sorted(random.sample(range(1, numero_maximo + 1), numeros_por_carton)))
    cartones_unicos.add(carton)

# --- Creación del DataFrame y exportación a CSV ---
df_cartones = pd.DataFrame(list(cartones_unicos))
df_cartones.columns = [f'Num_{i+1}' for i in range(numeros_por_carton)]
df_cartones.index.name = 'ID_Carton'
df_cartones.index = df_cartones.index + 1


# --- Guardar en un archivo CSV ---
nombre_archivo = 'Combinaciones x1500 Bingos Pampa Blanca.csv'
df_cartones.to_csv(nombre_archivo, sep=';') # Usamos ';' como separador para compatibilidad con Excel en español

print(f"Se han generado {numero_de_cartones} cartones únicos en el archivo '{nombre_archivo}'")