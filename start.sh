#!/bin/bash

# Script de inicialização para Railway
echo "=== Iniciando Sistema ==="

# Executar migrations
echo "Executando migrations..."
python manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao executar migrations"
    exit 1
fi

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao coletar arquivos estáticos"
    exit 1
fi

# Criar superusuário (ignora erro se já existir)
echo "Criando superusuário..."
python setup.py
# Não falha se o superusuário já existe

# Iniciar aplicação
echo "Iniciando aplicação..."
exec gunicorn barbearia.wsgi:application --bind 0.0.0.0:$PORT --log-level info
