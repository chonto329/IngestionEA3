"""
EA2 - Proyecto integrador Big Data
Etapa 2: Ingesta desde API (Socrata - datos.gov.co), almacenamiento en SQLite,
limpieza de datos, exportación en Excel y generación de reporte de auditoría.
"""

import os
import sqlite3
import pandas as pd
import requests

# ---------------------------------------------------------------
# Configuración de URLs y Rutas del Sistema de Archivos
# ---------------------------------------------------------------
API_URL = "https://www.datos.gov.co/resource/v8qi-smj7.json?$limit=50000"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "src", "db", "ingestion.db")
XLSX_PATH = os.path.join(BASE_DIR, "src", "xlsx", "ingestion.xlsx")
AUDIT_PATH = os.path.join(BASE_DIR, "src", "static", "auditoria", "ingestion.txt")


# ---------------------------------------------------------------
# 1. Extracción desde la API de Datos Abiertos
# ---------------------------------------------------------------
def cargar_datos_api(url):
    """
    Se conecta a la API REST de datos.gov.co y obtiene el dataset en JSON.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    return df


# ---------------------------------------------------------------
# 2. Análisis exploratorio pre-limpieza
# ---------------------------------------------------------------
def analizar(df):
    """
    Genera estadísticas de calidad iniciales del DataFrame.
    """
    return {
        "registros": len(df),
        "columnas": list(df.columns),
        "nulos_por_columna": df.isna().sum().to_dict(),
        "duplicados_completos": int(df.duplicated().sum()),
    }


# ---------------------------------------------------------------
# 3. Limpieza y Transformación
# ---------------------------------------------------------------
def limpiar(df, log):
    """
    Aplica transformaciones, limpieza y homologación de campos.
    """
    # 3.1 Renombrar campo erróneo de la API ('cobertuta_4g' -> 'cobertura_4g')
    if "cobertuta_4g" in df.columns:
        df = df.rename(columns={"cobertuta_4g": "cobertura_4g"})
        log.append("Columna 'cobertuta_4g' corregida a 'cobertura_4g'")

    # 3.2 Eliminación de duplicados exactos
    antes = len(df)
    df = df.drop_duplicates()
    log.append(f"Registros duplicados eliminados: {antes - len(df)}")

    # 3.3 Homologación e imputación de nulos en columnas categóricas
    columnas_texto = [
        "a_o", "trimestre", "proveedor", "cod_municipio", "municipio",
        "cabecera_municipal", "cod_centro_poblado", "centro_poblado",
        "cobertura_2g", "cobertura_3g", "cobertura_hspa_hspa_dc",
        "cobertura_4g", "cobertura_lte", "cobertura_5g"
    ]
    
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].fillna("NO REGISTRA").astype(str).str.strip()

    log.append("Imputación de nulos realizada en campos categóricos ('NO REGISTRA')")

    # 3.4 Creación de columna analítica (Total de coberturas soportadas por registro)
    columnas_cobertura = [c for c in df.columns if c.startswith("cobertura_")]
    if columnas_cobertura:
        df["total_tecnologias_cobertura"] = df[columnas_cobertura].apply(
            lambda row: sum(1 for val in row if str(val).upper() in ["SI", "SÍ", "TRUE", "1"]),
            axis=1
        )
        log.append("Variable analítica agregada: 'total_tecnologias_cobertura'")

    return df


# ---------------------------------------------------------------
# 4. Almacenamiento en SQLite y Generación de Excel
# ---------------------------------------------------------------
def guardar(df_bruto, df_limpio):
    """
    Guarda los datos en la base de datos SQLite y genera una muestra en Excel.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conexion = sqlite3.connect(DB_PATH)

    # Tabla 1: Datos brutos extraídos directamente del API
    df_bruto.to_sql("cobertura_movil_raw", conexion, if_exists="replace", index=False)

    # Tabla 2: Datos limpios procesados
    df_limpio.to_sql("cobertura_movil_limpios", conexion, if_exists="replace", index=False)
    
    conexion.close()

    # Generación de archivo Excel con muestra representativa (primeros 500 registros)
    os.makedirs(os.path.dirname(XLSX_PATH), exist_ok=True)
    df_limpio.head(500).to_excel(XLSX_PATH, index=False, engine="openpyxl")


# ---------------------------------------------------------------
# 5. Auditoría de Extracción e Ingesta
# ---------------------------------------------------------------
def generar_auditoria(stats_api, stats_db, log):
    """
    Compara los registros extraídos de la API contra los guardados en SQLite
    y genera el archivo de texto .txt.
    """
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)

    lineas = [
        "REPORTE DE AUDITORÍA Y CALIDAD DE DATOS - COBERTURA MÓVIL",
        "=" * 60,
        "--- Extracción desde API (Socrata) ---",
        f"Registros obtenidos de la API  : {stats_api['registros']}",
        f"Columnas detectadas           : {len(stats_api['columnas'])}",
        f"Duplicados en API             : {stats_api['duplicados_completos']}",
        "",
        "--- Operaciones de Limpieza ---",
        *[f"* {linea}" for linea in log],
        "",
        "--- Validación de Almacenamiento en SQLite ---",
        f"Registros en 'cobertura_movil_raw'     : {stats_db['raw_count']}",
        f"Registros en 'cobertura_movil_limpios' : {stats_db['clean_count']}",
        f"Diferencia (Registros filtrados)       : {stats_api['registros'] - stats_db['clean_count']}",
        "",
        "--- Estado de Conciliación ---",
        "ÉXITO: Los registros de la API coinciden con los insertados en SQLite."
        if stats_api['registros'] == stats_db['raw_count']
        else "ADVERTENCIA: Existe discrepancia entre API y SQLite."
    ]

    with open(AUDIT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


# ---------------------------------------------------------------
# Flujo Principal
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("Iniciando extracción desde la API...")
    df_raw = cargar_datos_api(API_URL)
    stats_api = analizar(df_raw)

    log_operaciones = []
    df_clean = limpiar(df_raw.copy(), log_operaciones)

    print("Guardando datos en SQLite y Excel...")
    guardar(df_raw, df_clean)

    # Consulta de validación a SQLite
    conn = sqlite3.connect(DB_PATH)
    raw_count = pd.read_sql("SELECT COUNT(*) AS total FROM cobertura_movil_raw", conn)["total"].iloc[0]
    clean_count = pd.read_sql("SELECT COUNT(*) AS total FROM cobertura_movil_limpios", conn)["total"].iloc[0]
    conn.close()

    stats_db = {"raw_count": raw_count, "clean_count": clean_count}

    print("Generando reporte de auditoría...")
    generar_auditoria(stats_api, stats_db, log_operaciones)
    print(f"Proceso finalizado con éxito. Registros procesados: {stats_api['registros']}")