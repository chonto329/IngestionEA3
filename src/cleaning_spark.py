"""
EA2 - Proyecto integrador Big Data
Etapa 2: Preprocesamiento y limpieza de datos en un entorno que
simula una plataforma de Big Data en la nube (la base SQLite de la
Actividad 1 emula el servicio de almacenamiento cloud).
"""

import os
import sqlite3
import pandas as pd

# ---------------------------------------------------------------
# Configuración de Rutas del Sistema de Archivos
# ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "src", "db", "ingestion.db")
XLSX_PATH = os.path.join(BASE_DIR, "src", "xlsx", "cleaned_data.xlsx")
AUDIT_PATH = os.path.join(BASE_DIR, "src", "static", "auditoria", "cleaning_report.txt")


# ---------------------------------------------------------------
# 1. Extracción desde el "cloud" simulado (SQLite de la Etapa 1)
# ---------------------------------------------------------------
def cargar_datos():
    """
    Carga de forma directa los datos brutos guardados previamente en SQLite.
    """
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM cobertura_movil_raw", conexion)
    conexion.close()
    return df


# ---------------------------------------------------------------
# 2. Análisis exploratorio: estadísticas de calidad iniciales
# ---------------------------------------------------------------
def analizar(df):
    """
    Genera estadísticas de calidad de datos pre y post limpieza.
    """
    prov_series = df.get("proveedor", pd.Series(dtype=str))
    return {
        "registros": len(df),
        "duplicados": int(df.duplicated().sum()),
        "nulos_por_columna": df.isna().sum().to_dict(),
        "sin_proveedor": int((prov_series.fillna("").astype(str).str.strip() == "").sum()),
    }


# ---------------------------------------------------------------
# 3. Limpieza y transformación
# ---------------------------------------------------------------
def limpiar(df, log):
    """
    Aplica transformaciones, limpieza y homologación de campos.
    """
    # 3.1 Corrección de nombre de columna erróneo
    if "cobertuta_4g" in df.columns:
        df = df.rename(columns={"cobertuta_4g": "cobertura_4g"})
        log.append("Columna 'cobertuta_4g' renombrada a 'cobertura_4g'")

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
            n_nulos = int(df[col].isna().sum())
            df[col] = df[col].fillna("NO REGISTRA").astype(str).str.strip()
            df[col] = df[col].replace("", "NO REGISTRA")
            if n_nulos > 0:
                log.append(f"Valores vacíos/nulos en '{col}' imputados con 'NO REGISTRA': {n_nulos}")

    # 3.4 Creación de variable analítica derivada
    columnas_cobertura = [c for c in df.columns if c.startswith("cobertura_")]
    if columnas_cobertura:
        df["total_tecnologias_cobertura"] = df[columnas_cobertura].apply(
            lambda row: sum(1 for val in row if str(val).upper() in ["SI", "SÍ", "TRUE", "1"]),
            axis=1
        )
        log.append("Variable derivada creada: 'total_tecnologias_cobertura'")

    return df


# ---------------------------------------------------------------
# 4. Carga de resultados y generación de evidencias
# ---------------------------------------------------------------
def guardar(df):
    """
    Guarda la tabla limpia en SQLite y exporta la muestra a Excel.
    """
    conexion = sqlite3.connect(DB_PATH)
    df.to_sql("cobertura_movil_limpios", conexion, if_exists="replace", index=False)
    conexion.close()

    os.makedirs(os.path.dirname(XLSX_PATH), exist_ok=True)
    df.head(500).to_excel(XLSX_PATH, index=False, engine="openpyxl")


# ---------------------------------------------------------------
# 5. Generación de reporte de auditoría
# ---------------------------------------------------------------
def generar_auditoria(stats_antes, stats_despues, log):
    """
    Genera el archivo de texto .txt comparando el estado antes y después.
    """
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    lineas = [
        "REPORTE DE AUDITORIA - ETAPA DE LIMPIEZA",
        "=" * 55,
        "--- Estado ANTES de la limpieza ---",
        f"Registros            : {stats_antes['registros']}",
        f"Duplicados           : {stats_antes['duplicados']}",
        f"Sin Proveedor        : {stats_antes['sin_proveedor']}",
        f"Nulos por columna    : {stats_antes['nulos_por_columna']}",
        "",
        "--- Operaciones realizadas ---",
        *[f"* {linea}" for linea in log],
        "",
        "--- Estado DESPUES de la limpieza ---",
        f"Registros            : {stats_despues['registros']}",
        f"Duplicados           : {stats_despues['duplicados']}",
        f"Nulos por columna    : {stats_despues['nulos_por_columna']}",
    ]

    with open(AUDIT_PATH, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas))


# ---------------------------------------------------------------
# Flujo Principal
# ---------------------------------------------------------------
if __name__ == "__main__":
    df = cargar_datos()
    stats_antes = analizar(df)
    log = []
    df_limpio = limpiar(df, log)
    guardar(df_limpio)
    stats_despues = analizar(df_limpio)
    generar_auditoria(stats_antes, stats_despues, log)
    print(
        f"Limpieza completada: {stats_antes['registros']} -> "
        f"{stats_despues['registros']} registros"
    )