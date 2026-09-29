Pipeline ETL de Cobertura Móvil

Este script automatiza la ingesta, limpieza, enriquecimiento y auditoría de datos de cobertura móvil a partir de 6 fuentes heterogéneas con procesamiento incremental.

Funcionalidades ClaveIngesta Multi-formato: 

Lee 6 fuentes distintas (JSON, XLSX, CSV, XML, HTML y TXT).
Base de Datos SQLite (ingestion.db):Tabla cobertura_movil_raw: Guarda los datos originales sin alterar.
Tabla cobertura_movil_limpios: Guarda únicamente las transformaciones incrementales (append)

.Transformaciones:

Corrige el error tipográfico de la columna cobertuta_4g -->cobertura_4g.
Calcula el campo total_tecnologias_cobertura (conteo de redes en 'S' entre 2G, 3G, HSPA, 4G, LTE y 5G)

.Generación de Reportes Automáticos:

Excel (enriched_data.xlsx): Incluye KPI cards, desglose por fuente, estilos ejecutivos y datos limpios.
Auditoría (enriched_report.txt): Log detallado con balance de registros, porcentajes por año/proveedor y validación de reglas de negocio.


Uso rápido 

En la consola ejecuta el comando pip install pandas openpyxl lxml html5lib para instalas la dependencias necesarias.

Despues ejecuta python enrichement.py para que realize la ingesta de la fuentes a la base de datos y te genere los archivos de auditoria.    