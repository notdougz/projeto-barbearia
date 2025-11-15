#!/bin/bash
set -e

# Função para aguardar o banco de dados estar pronto
wait_for_db() {
    if [ -n "$DATABASE_URL" ]; then
        echo "Aguardando banco de dados PostgreSQL estar pronto..."
        until python -c "
import sys
import os
import psycopg2
from urllib.parse import urlparse

try:
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path[1:]
        )
        conn.close()
        print('Banco de dados está pronto!')
        sys.exit(0)
    else:
        print('DATABASE_URL não configurada, usando SQLite')
        sys.exit(0)
except Exception as e:
    print(f'Aguardando... {e}')
    sys.exit(1)
" 2>/dev/null; do
            echo "Banco de dados não está pronto ainda. Aguardando..."
            sleep 2
        done
    else
        echo "Usando SQLite (sem necessidade de aguardar banco externo)"
    fi
}

# Aguarda o banco de dados estar pronto
wait_for_db

# Executa migrações
echo "Executando migrações do banco de dados..."
python manage.py migrate --noinput

# Carrega fixtures iniciais (se existirem)
if [ -f "agendamentos/fixtures/servicos_iniciais.json" ]; then
    echo "Carregando dados iniciais..."
    python manage.py loaddata agendamentos/fixtures/servicos_iniciais.json || true
fi

# Coleta arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || true

# Executa o comando passado como argumento
exec "$@"

