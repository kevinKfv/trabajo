FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema requeridas para Playwright y compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright y sus dependencias de sistema
RUN playwright install chromium --with-deps

# Copiar código fuente y script de inicio
COPY . .
RUN chmod +x start.sh

# Railway inyectará la variable de entorno PORT automáticamente
CMD ["./start.sh"]
