#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia.settings')
django.setup()

from django.contrib.auth.models import User

def main():
    print("=== Verificando superusuário ===")
    
    try:
        if not User.objects.filter(username='kevem').exists():
            User.objects.create_superuser('kevem', 'denbinsk4853@gmail.com', '123456')
            print("   OK - Superusuário criado: kevem / 123456")
        else:
            print("   OK - Superusuário já existe")
        return True
    except Exception as e:
        print(f"   AVISO - Não foi possível criar superusuário: {e}")
        # Não retorna False pois isso não deve impedir a aplicação de iniciar
        return True

if __name__ == '__main__':
    main()
