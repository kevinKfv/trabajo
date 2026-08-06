# Job Hunter AI 🚀

**Job Hunter AI** es un agregador inteligente de ofertas laborales desarrollado con **Python 3.12+**, **FastAPI**, **Playwright**, **SQLAlchemy 2.0**, **PostgreSQL**, **Pydantic v2** e **Inteligencia Artificial**.

Su propósito es automatizar la búsqueda de empleos en múltiples plataformas (LinkedIn, Bumeran, Computrabajo), unificar los resultados, eliminar ofertas duplicadas, clasificarlas mediante modelos de lenguaje (OpenAI / Ollama), enviar notificaciones personalizadas (Telegram / Email) para ofertas que coincidan con tu perfil profesional y visualizarlas en un **Dashboard Web Interactivo**.

---

## 🛠️ Stack Tecnológico

* **Lenguaje**: Python 3.12+
* **Framework Web**: FastAPI + Uvicorn
* **Scraping & Automatización**: Playwright, BeautifulSoup4, Requests, HTTPX
* **ORM & Base de Datos**: SQLAlchemy 2.0 (Async), PostgreSQL 16, Asyncpg, Alembic
* **Validación de Datos**: Pydantic v2, Pydantic-Settings
* **Inteligencia Artificial**: Interface para OpenAI (GPT-4o) y Ollama (local)
* **Notificaciones**: Telegram Bot API, SMTP Email
* **Programación de Tareas**: APScheduler
* **Interfaz de Usuario**: HTML5, Vanilla CSS (Dark Mode & Glassmorphic UI), JavaScript ES6+ SPA
* **Contenedorización**: Docker & Docker Compose
* **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## 🗺️ Roadmap de Desarrollos (Etapas Completadas)

- [x] **Etapa 1**: Arquitectura Base, FastAPI, SQLAlchemy 2.0, PostgreSQL, Docker & Docker Compose, Interfaces base.
- [x] **Etapa 2**: Implementación de Scrapers específicos (LinkedIn, Bumeran, Computrabajo) con Playwright y BS4.
- [x] **Etapa 3**: Normalización, deduplicación avanzada cross-platform y estrategia de persistencia.
- [x] **Etapa 4**: Integración de servicio de IA con proveedores OpenAI / Ollama y scoring contra CV.
- [x] **Etapa 5**: Módulo de notificaciones (Telegram & Email).
- [x] **Etapa 6**: Scheduler automático con APScheduler.
- [x] **Etapa 7**: Dashboard / Frontend web interactivo.

---

## 🚀 Ejecución Rápida con Docker Compose

```bash
# 1. Copiar plantilla de variables de entorno
cp .env.example .env

# 2. Levantar la aplicación con Docker Compose
docker compose up --build -d
```

Una vez en ejecución:
* 📊 **Dashboard Web Interactivo**: `http://localhost:8000/`
* 📖 **Documentación API REST (Swagger)**: `http://localhost:8000/api/v1/docs`

---

## 📄 Licencia

MIT License
