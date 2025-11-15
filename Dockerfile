# Dockerfile para o projeto Barbearia
# Usa Python 3.12 como base
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia o código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p staticfiles static_root

# Coleta arquivos estáticos (será executado novamente no entrypoint se necessário)
RUN python manage.py collectstatic --noinput || true

# Expõe a porta 8000
EXPOSE 8000

# Script de entrada que aguarda o banco estar pronto e executa migrações
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
# Usa $PORT se disponível (Railway), senão usa 8000
CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 3 barbearia.wsgi:application"

