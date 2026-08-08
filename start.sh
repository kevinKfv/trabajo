#!/bin/bash
# Script de inicio para garantizar que uvicorn tome el puerto correcto en Railway
BIND_PORT="${PORT:-8000}"
echo "========================================================="
echo "=== INICIANDO SERVIDOR EN PUERTO: $BIND_PORT ==="
echo "========================================================="
exec uvicorn app.main:app --host 0.0.0.0 --port "$BIND_PORT"
