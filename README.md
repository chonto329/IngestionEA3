# Pipeline de Big Data: Cobertura Movil por Tecnologia (Santander, Colombia)

Este repositorio contiene la implementacion y documentacion de un pipeline *end-to-end* de procesamiento de datos de telecomunicaciones en Colombia, estructurado bajo una arquitectura por capas (**Modelo Medallion**) y automatizado mediante **GitHub Actions**.

---

##  Tabla de Contenidos
1. [Descripcion y Trazabilidad del Proceso](#-descripcion-y-trazabilidad-del-proceso)
2. [Arquitectura por Capas (Medallion)](#-arquitectura-por-capas-medallion)
3. [Requisitos Previos](#-requisitos-previos)
4. [Instalacion y Configuracion](#-instalacion-y-configuracion)
5. [Ejecucion del Pipeline](#-ejecucion-del-pipeline)
6. [Workflow Automatizado en GitHub Actions](#-workflow-automatizado-en-github-actions)
7. [Estructura del Repositorio](#-estructura-del-repositorio)

---

##  Descripcion y Trazabilidad del Proceso

El proyecto toma como insumo el conjunto de datos publico de la API de Datos Abiertos sobre **Cobertura movil por tecnologia en Santander**. A traves de un flujo automatizado de tres fases, el sistema asegura la trazabilidad, audibilidad y persistencia del dato en cada etapa:

1. **Garantia de Origen:** Los datos se capturan en bruto de la API y se almacenan sin modificaciones en la base de datos para mantener el historial intacto y auditable.
2. **Control de Calidad y Auditoria:** Cada transformacion genera reportes en texto plano (`.txt`) con estadisticas antes y despues de cada proceso.
3. **Procesamiento Incremental:** La fase de enriquecimiento utiliza lectura y transformacion incremental mediante clausulas SQL (`LIMIT -1 OFFSET ?`), evitando la duplicacion de registros y procesando unicamente las novedades de cada sesion.

---

## Arquitectura por Capas (Medallion)

* ** Capa Bronze (Landing Zone / Staging):**
  * **Script:** `main.py`
  * **Ubicacion:** Tabla `cobertura_movil_raw` en `ingestion.db`.
  * **Funcion:** Ingesta en bruto desde la API web (Socrata/JSON), preservando los 14 campos originales y generando el informe `ingestion.txt`.

* **Capa Silver (Limpieza y Saneamiento):**
  * **Script:** `cleaning.py`
  * **Ubicacion:** Tabla `cobertura_movil_limpios` en `ingestion.db`.
  * **Funcion:** Correccion de errores tipograficos (ej. `cobertuta_4g` -- `cobertura_4g`), eliminacion de duplicados, imputacion de nulos (`'NO REGISTRA'`), estandarizacion de codigos DANE y generacion de `cleaned_data.xlsx` y `cleaning_report.txt`.

* **Capa Gold (Enriquecimiento y Analitica):**
  * **Script:** `enrichment.py`
  * **Ubicacion:** Tabla `cobertura_movil_limpios` (actualizacion incremental).
  * **Funcion:** Calculo de la variable sintetica `total_tecnologias_cobertura` (sumatoria condicional de redes 2G a 5G), generacion de KPIs por operador/anio, exportacion del libro ejecutivo `enriched_data.xlsx` (con multiples pestanas) y el informe de auditoria `enriched_report.txt`.

---

## Requisitos Previos

Asegurate de contar con las siguientes herramientas instaladas en tu sistema local:

* **Python 3.11** o superior.
* **Git** instalado para la clonacion del repositorio.

---

## Instalacion y Configuracion

Sigue estos pasos para clonar el repositorio y preparar el entorno de ejecucion:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/chonto329/IngestionEA3.git](https://github.com/chonto329/IngestionEA3.git)
cd IngestionEA3

--Crear y activar un entorno virtual (Recomendado)

python -m venv venv
.\venv\Scripts\Activate.ps1

Instalar dependencias

pip install --upgrade pip
pip install -r requirements.txt

--Ejecucion del Pipeline

-Ejecutar Ingesta (Capa Bronze):
    python main.py

-Ejecutar Limpieza (Capa Silver):
   python cleaning.py

-Ejecutar Enriquecimiento (Capa Gold):
  python src/enrichment.py

Al finalizar, este script actualizara la base de datos ingestion.db, generara el libro de Excel enriched_data.xlsx y actualizara el reporte enriched_report.txt.

Workflow Automatizado en GitHub Actions

El repositorio cuenta con integracion continua (CI/CD) completamente configurada en el archivo .github/workflows/bigdata.yml.

¿Como funciona la automatizacion?
Disparadores (Triggers):

Eventos push a la rama principal (master o main).

Ejecución programada (Cron Job).

Activación manual mediante la pestana Actions en GitHub (workflow_dispatch).

Entorno de Ejecucion:

Aprovisiona automaticamente un contenedor Linux efimero (ubuntu-latest).

Configura Python 3.11 e instala todas las dependencias listadas en requirements.txt.

Secuencia del Pipeline:

Ejecuta en orden estricto: main.py -- cleaning.py -- enrichment.py.

Realiza comprobaciones del sistema para validar que la base de datos ingestion.db y los reportes finales fueron creados exitosamente.

Imprime los informes de auditoria directamente en los logs de la consola de GitHub.

Persistencia y Artefactos:

Artefactos descargables: Empaqueta enriched_data.xlsx, enriched_report.txt y ingestion.db para su descarga desde la interfaz de GitHub.

Auto-commit: Utiliza permisos de escritura (permissions: contents: write) para realizar un commit automatico de vuelta al repositorio, manteniendo la base de datos y reportes sincronizados en la nube sin intervencion humana.

├── .github/
│   └── workflows/
│       └── bigdata.yml       # Definición del flujo CI/CD en GitHub Actions
├── sources/                  # Landing Zone de archivos simulados (JSON, CSV, XML, etc.)
├── main.py                   # Script de ingesta desde API (Capa Bronze)
├── cleaning.py               # Script de saneamiento y calidad (Capa Silver)
├── enrichment.py             # Script de enriquecimiento y analítica (Capa Gold)
├── ingestion.db              # Base de datos relacional SQLite (RAW y LIMPIOS)
├── cleaned_data.xlsx         # Salida intermedia de datos limpios en Excel
├── enriched_data.xlsx        # Dashboard y reporte ejecutivo final en Excel
├── cleaning_report.txt       # Reporte de auditoría del proceso de limpieza
├── enriched_report.txt       # Reporte de auditoría final e histórico incremental
├── requirements.txt          # Lista de dependencias del proyecto
└── README.md                 # Documentación del proyecto


