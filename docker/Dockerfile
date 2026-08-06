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

# Copiar código fuente de la aplicación
COPY . .

# Exponer el puerto de FastAPI
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
