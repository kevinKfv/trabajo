# 🛠️ Guía Completa de Configuración y Ejecución - Job Hunter AI

Esta guía explica detalladamente cómo configurar y ejecutar el proyecto **Job Hunter AI**, y cómo solucionar el error `ConnectionDoesNotExistError` o fallos de conexión a la base de datos PostgreSQL.

---

## ❓ ¿Por qué ocurrió el error `ConnectionDoesNotExistError`?

El error ocurre porque la aplicación FastAPI intenta conectarse a **PostgreSQL** en `localhost:5432`, pero el servidor de base de datos no está iniciado en tu computadora.

Tienes **dos opciones** muy sencillas para solucionarlo y ejecutar el sistema:

---

## 🚀 Opción A: Ejecución con Docker Compose (Recomendada - 100% Automática)

Esta es la forma más fácil y rápida, ya que Docker levanta tanto la **Base de Datos PostgreSQL 16** como la **API con el Dashboard Web** en contenedores aislados sin instalar nada más en Windows.

### Pasos:

1. **Asegúrate de tener Docker Desktop iniciado** en tu computadora.

2. **Crear tu archivo `.env`** copiando la plantilla:
   ```powershell
   copy .env.example .env
   ```

3. **Ejecutar el proyecto con Docker Compose**:
   ```powershell
   docker compose up --build -d
   ```

4. **¡Listo! Abrir en el navegador**:
   * 📊 **Dashboard Web Interactivo**: [http://localhost:8000/](http://localhost:8000/)
   * 📖 **Documentación API REST (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

5. **Para ver logs o detener los contenedores**:
   ```powershell
   # Ver logs en tiempo real
   docker compose logs -f api

   # Detener los servicios
   docker compose down
   ```

---

## 💻 Opción B: Ejecución Local en tu Consola (Uvicorn + PostgreSQL)

Si prefieres ejecutar el servidor localmente con `uvicorn app.main:app --reload` en tu terminal, necesitas tener PostgreSQL corriendo en el puerto `5432`.

### Pasos:

1. **Levantar únicamente la Base de Datos PostgreSQL con Docker**:
   ```powershell
   docker compose up -d db
   ```

2. **Asegurarte de tener el entorno virtual activado**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Crear tu archivo `.env`**:
   ```powershell
   copy .env.example .env
   ```

4. **Iniciar Uvicorn**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

5. **Abrir en tu navegador**:
   * 👉 [http://localhost:8000/](http://localhost:8000/)

---

## ⚙️ Configuración del Archivo `.env`

El archivo `.env` contiene las credenciales del sistema. A continuación se detallan las variables requeridas y opcionales:

### 1. Base de Datos PostgreSQL
```ini
POSTGRES_SERVER=localhost   # Usar 'db' si estás dentro de Docker Compose
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=job_hunter_db
```

---

### 2. Clasificación con Inteligencia Artificial (OpenAI / Ollama)

Puedes elegir entre utilizar **OpenAI** (requiere API Key) u **Ollama** (100% gratuito y local):

#### Para usar OpenAI (GPT-4o / GPT-4o-mini):
```ini
AI_PROVIDER=openai
OPENAI_API_KEY=sk-tu-api-key-de-openai-aqui
AI_MODEL=gpt-4o-mini
```

#### Para usar Ollama (Ejecución Local Gratuita):
1. Instala y ejecuta [Ollama](https://ollama.com/).
2. Descarga un modelo (ej: `ollama run llama3`).
3. En tu `.env`:
```ini
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

### 3. Notificaciones y Alertas (Telegram / Email)

#### Para recibir alertas por Telegram:
1. Crea un Bot con [@BotFather](https://t.me/BotFather) en Telegram y copia el Token.
2. Obtén tu ID de Chat (puedes usar [@userinfobot](https://t.me/userinfobot)).
3. En tu `.env`:
```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
```

#### Para recibir alertas por Correo Electrónico (SMTP):
```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion_gmail
NOTIFICATION_EMAIL_TO=destino@gmail.com
```

---

### 4. Scheduler (Ejecución Periódica Automática)

Configura cada cuántas horas quieres que el bot busque empleos, los analice con IA y te envíe alertas automáticamente:

```ini
SCRAPE_INTERVAL_HOURS=6
```

---

## 🧪 Verificación de Tests

Para verificar que todo el código y la arquitectura funcionan correctamente sin requerir base de datos activa:

```powershell
pytest -v
```

Debe retornar **`18 passed`**.

---

## 📌 Resumen de Rutas de la Aplicación

| Ruta | Descripción |
|---|---|
| `GET /` o `/dashboard` | Dashboard Web Interactivo (SPA) |
| `GET /api/v1/docs` | Documentación Swagger de la API |
| `GET /api/v1/health` | Estado de la API y conexión a BD |
| `GET /api/v1/jobs` | Lista paginada y filtrada de empleos |
| `GET /api/v1/jobs/stats` | Métricas y estadísticas generales |
| `POST /api/v1/scrape` | Disparar proceso de scraping |
| `POST /api/v1/analyze` | Disparar análisis masivo con IA |
| `POST /api/v1/notify` | Disparar alertas por Telegram/Email |
