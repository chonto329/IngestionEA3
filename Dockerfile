FROM python:3.11-slim

# 1. Instalar la versión JRE por defecto de Debian (totalmente compatible con PySpark)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Configurar JAVA_HOME apuntando al enlace simbólico estándar de Debian
ENV JAVA_HOME=/usr/lib/jvm/default-java

WORKDIR /app

# 2. Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar todo el proyecto al contenedor
COPY . .

# 4. Comando de ejecución por defecto
CMD ["python", "src/enrichement_spark.py"]