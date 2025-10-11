#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth.models import User

def main():
    print("=== Configurando Sistema ===")
    
    # 1. Executar migrations
    print("1. Executando migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    print("   OK - Migrations executadas")
    
    # 2. Coletar arquivos estáticos
    print("2. Coletando arquivos estáticos...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("   OK - Arquivos estaticos coletados")
    
    # 3. Criar superusuário se não existir
    print("3. Verificando superusuario...")
    if not User.objects.filter(username='kevem').exists():
        User.objects.create_superuser('kevem', 'denbinsk4853@gmail.com', '123456')
        print("   OK - Superusuario criado: kevem / 123456")
    else:
        print("   OK - Superusuario ja existe")
    
    print("=== Sistema configurado com sucesso! ===")

if __name__ == '__main__':
    main()
