#!/bin/bash
# Script de inicialização para Docker - Railway
# Este script SEMPRE deve iniciar o gunicorn, mesmo com erros anteriores

# Força output imediato
export PYTHONUNBUFFERED=1

# Log inicial crítico - DEVE aparecer nos logs
echo "=========================================="
echo "=== DOCKER-ENTRYPOINT.SH INICIADO ==="
echo "=========================================="
echo "Timestamp: $(date)"
echo "Working dir: $(pwd)"
echo "PORT: ${PORT:-8000}"
echo "DATABASE_URL: ${DATABASE_URL:+definida}"
echo "=========================================="

# Função para aguardar banco (com timeout)
wait_for_db() {
    if [ -z "$DATABASE_URL" ]; then
        echo "DATABASE_URL não definida, pulando wait_for_db"
        return 0
    fi
    
    echo "Aguardando PostgreSQL estar pronto..."
    MAX_ATTEMPTS=15
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if python -c "
import os, sys, psycopg2
from urllib.parse import urlparse
try:
    parsed = urlparse(os.getenv('DATABASE_URL'))
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        dbname=parsed.path[1:],
        connect_timeout=3
    )
    conn.close()
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
            echo "PostgreSQL está pronto!"
            return 0
        fi
        ATTEMPT=$((ATTEMPT + 1))
        echo "Tentativa $ATTEMPT/$MAX_ATTEMPTS..."
        sleep 2
    done
    
    echo "AVISO: Timeout aguardando PostgreSQL, continuando mesmo assim..."
    return 0
}

# Executa wait_for_db (não bloqueia se falhar)
wait_for_db || echo "AVISO: wait_for_db falhou, continuando..."

# Migrações (não bloqueia se falhar)
echo "=== Executando migrações ==="
python manage.py migrate --noinput 2>&1 || echo "AVISO: migrate falhou, continuando..."

# Collectstatic (não bloqueia se falhar)
echo "=== Coletando arquivos estáticos ==="
python manage.py collectstatic --noinput 2>&1 || echo "AVISO: collectstatic falhou, continuando..."

# Setup (não bloqueia se falhar)
echo "=== Executando setup ==="
python setup.py 2>&1 || echo "AVISO: setup falhou, continuando..."

# CRÍTICO: Sempre inicia o gunicorn
PORT=${PORT:-8000}
echo "=========================================="
echo "=== INICIANDO GUNICORN ==="
echo "=========================================="
echo "Porta: $PORT"
echo "Comando: gunicorn barbearia.wsgi:application --bind 0.0.0.0:$PORT"
echo "=========================================="

# SEMPRE executa o gunicorn (nunca falha aqui)
exec gunicorn barbearia.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers 3 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --preload
