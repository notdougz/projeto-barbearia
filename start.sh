#!/bin/bash
set -e

echo "=== Iniciando aplicação ==="
echo "Porta: ${PORT:-8000}"

echo "=== Aplicando migrações ==="
python manage.py migrate --noinput

echo "=== Coletando arquivos estáticos ==="
python manage.py collectstatic --noinput --clear

echo "=== Executando setup ==="
python setup.py

echo "=== Iniciando Gunicorn ==="
echo "Porta: ${PORT:-8000}"
echo "Workers: 3"
echo "Timeout: 120"

exec gunicorn barbearia.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -

