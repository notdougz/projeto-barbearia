#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Executar migrations
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Criar superusuário se não existir
    from django.contrib.auth.models import User
    if not User.objects.filter(username='kevem').exists():
        User.objects.create_superuser('kevem', 'admin@barbearia.com', '123456')
        print('Superusuário criado: kevem / 123456')
    else:
        print('Superusuário já existe')
