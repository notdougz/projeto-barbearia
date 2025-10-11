#!/bin/bash

# Script de inicialização para Railway
echo "=== Iniciando Sistema ==="

# Executar setup se necessário
echo "Executando setup..."
python setup.py

# Iniciar aplicação
echo "Iniciando aplicação..."
exec gunicorn barbearia.wsgi:application --bind 0.0.0.0:$PORT
