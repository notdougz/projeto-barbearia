#!/bin/bash
set -e

# Logs iniciais
echo "=========================================="
echo "=== Iniciando Container ==="
echo "=========================================="
echo "Data/Hora: $(date)"
echo "Diretório de trabalho: $(pwd)"
echo "Variáveis de ambiente importantes:"
echo "  - PORT: ${PORT:-não definida (usará 8000)}"
echo "  - DATABASE_URL: ${DATABASE_URL:+definida}"
echo "=========================================="

# Função para aguardar o banco de dados estar pronto (com timeout)
wait_for_db() {
    if [ -n "$DATABASE_URL" ]; then
        echo "Aguardando banco de dados PostgreSQL estar pronto..."
        MAX_ATTEMPTS=30  # Máximo de 30 tentativas (60 segundos)
        ATTEMPT=0
        
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
            dbname=parsed.path[1:],
            connect_timeout=5
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
            ATTEMPT=$((ATTEMPT + 1))
            if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
                echo "ERRO: Timeout aguardando banco de dados após $MAX_ATTEMPTS tentativas"
                echo "Continuando com a inicialização mesmo assim..."
                break
            fi
            echo "Banco de dados não está pronto ainda. Tentativa $ATTEMPT/$MAX_ATTEMPTS..."
            sleep 2
        done
        
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
            echo "Banco de dados conectado com sucesso!"
        fi
    else
        echo "Usando SQLite (sem necessidade de aguardar banco externo)"
    fi
}

# Aguarda o banco de dados estar pronto
wait_for_db

# Executa migrações (desabilita set -e temporariamente para não parar em avisos)
set +e
echo "Executando migrações do banco de dados..."

# Tenta criar migrações se houver mudanças não migradas
echo "Verificando se há migrações pendentes..."
python manage.py makemigrations --noinput 2>&1
MAKEMIGRATIONS_EXIT=$?
if [ $MAKEMIGRATIONS_EXIT -eq 0 ]; then
    echo "Migrações verificadas/criadas com sucesso"
elif [ $MAKEMIGRATIONS_EXIT -eq 1 ]; then
    echo "Nenhuma migração nova necessária"
else
    echo "AVISO: Erro ao verificar migrações (código $MAKEMIGRATIONS_EXIT), continuando..."
fi

# Aplica migrações
echo "Aplicando migrações..."
python manage.py migrate --noinput 2>&1
MIGRATE_EXIT=$?
if [ $MIGRATE_EXIT -eq 0 ]; then
    echo "Migrações aplicadas com sucesso"
else
    echo "AVISO: migrate retornou código $MIGRATE_EXIT"
    echo "Tentando criar e aplicar migrações novamente..."
    python manage.py makemigrations --noinput 2>&1 || true
    python manage.py migrate --noinput 2>&1 || {
        echo "ERRO: Não foi possível aplicar migrações, mas continuando com a inicialização..."
        echo "A aplicação pode não funcionar corretamente. Verifique os logs acima."
    }
fi

# Reabilita set -e para o resto do script
set -e

# Carrega fixtures iniciais (se existirem)
if [ -f "agendamentos/fixtures/servicos_iniciais.json" ]; then
    echo "Carregando dados iniciais..."
    python manage.py loaddata agendamentos/fixtures/servicos_iniciais.json || true
fi

# Coleta arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput || true

# Executa setup
echo "Executando setup..."
python setup.py || echo "AVISO: Setup falhou, mas continuando..."

# Determina a porta (Railway usa $PORT, senão usa 8000)
PORT=${PORT:-8000}
echo "=========================================="
echo "=== Iniciando Gunicorn ==="
echo "=========================================="
echo "Porta: $PORT"
echo "Workers: 3"
echo "Timeout: 120s"
echo "Log Level: info"
echo "=========================================="

# Executa o comando passado como argumento, ou inicia gunicorn se nenhum comando foi passado
if [ $# -eq 0 ]; then
    # Se nenhum comando foi passado, inicia gunicorn
    echo "Iniciando Gunicorn..."
    exec gunicorn barbearia.wsgi:application \
        --bind "0.0.0.0:$PORT" \
        --workers 3 \
        --timeout 120 \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        --preload
else
    # Executa o comando passado como argumento
    echo "Executando comando customizado: $@"
    exec "$@"
fi

