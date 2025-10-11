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
    try:
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("   OK - Migrations executadas")
    except Exception as e:
        print(f"   ERRO - Falha nas migrations: {e}")
        return False
    
    # 2. Coletar arquivos estáticos
    print("2. Coletando arquivos estaticos...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])
        print("   OK - Arquivos estaticos coletados")
    except Exception as e:
        print(f"   ERRO - Falha ao coletar estaticos: {e}")
        return False
    
    # 3. Criar superusuário se não existir
    print("3. Verificando superusuario...")
    try:
        if not User.objects.filter(username='kevem').exists():
            User.objects.create_superuser('kevem', 'denbinsk4853@gmail.com', '123456')
            print("   OK - Superusuario criado: kevem / 123456")
        else:
            print("   OK - Superusuario ja existe")
    except Exception as e:
        print(f"   ERRO - Falha ao criar superusuario: {e}")
        return False
    
    print("=== Sistema configurado com sucesso! ===")
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)
