#!/bin/bash
# Não usar set -e aqui pois queremos que o gunicorn inicie mesmo se houver erros nas etapas anteriores
set -o pipefail  # Apenas falha em pipes, não em comandos individuais

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

# Executa migrações (com timeout para não travar)
echo "Executando migrações do banco de dados..."

# Tenta criar migrações se houver mudanças não migradas (com timeout)
echo "Verificando se há migrações pendentes..."
timeout 30 python manage.py makemigrations --noinput 2>&1 || {
    echo "AVISO: makemigrations falhou ou demorou muito, mas continuando..."
}

# Aplica migrações (com timeout para não travar)
echo "Aplicando migrações..."
timeout 60 python manage.py migrate --noinput 2>&1 || {
    echo "AVISO: migrate falhou ou demorou muito"
    echo "Tentando novamente com timeout maior..."
    timeout 90 python manage.py migrate --noinput 2>&1 || {
        echo "ERRO: Não foi possível aplicar migrações após múltiplas tentativas"
        echo "Continuando com a inicialização mesmo assim..."
    }
}

# Carrega fixtures iniciais (se existirem)
if [ -f "agendamentos/fixtures/servicos_iniciais.json" ]; then
    echo "Carregando dados iniciais..."
    python manage.py loaddata agendamentos/fixtures/servicos_iniciais.json || true
fi

# Coleta arquivos estáticos (com timeout para não travar)
echo "Coletando arquivos estáticos..."
timeout 60 python manage.py collectstatic --noinput 2>&1 || {
    echo "AVISO: collectstatic falhou ou demorou muito, mas continuando..."
}

# Executa setup (com timeout para não travar)
echo "Executando setup..."
timeout 30 python setup.py 2>&1 || {
    echo "AVISO: Setup falhou ou demorou muito, mas continuando..."
}

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
    echo "Verificando se a porta $PORT está disponível..."
    
    # Verifica se consegue escutar na porta (teste rápido)
    timeout 2 bash -c "echo > /dev/tcp/0.0.0.0/$PORT" 2>/dev/null && echo "AVISO: Porta $PORT já está em uso!" || echo "Porta $PORT está disponível"
    
    echo "Executando: gunicorn barbearia.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --log-level info"
    
    # Inicia o gunicorn - SEMPRE executa, mesmo se houver erros anteriores
    exec gunicorn barbearia.wsgi:application \
        --bind "0.0.0.0:$PORT" \
        --workers 3 \
        --timeout 120 \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        --preload \
        --capture-output
else
    # Executa o comando passado como argumento
    echo "Executando comando customizado: $@"
    exec "$@"
fi

