#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia.settings')
django.setup()

from django.contrib.auth.models import User

def main():
    print("=== Verificando superusuário ===")
    
    # Pegar senha da variável de ambiente ou usar padrão
    senha_padrao = '123456'
    senha = os.getenv('SUPERUSER_PASSWORD', senha_padrao)
    
    try:
        user = User.objects.filter(username='kevem').first()
        
        if not user:
            # Criar novo usuário
            email = os.getenv('SUPERUSER_EMAIL', 'admin@barbearia.com')
            User.objects.create_superuser('kevem', email, senha)
            if senha == senha_padrao:
                print(f"   OK - Superusuário criado: kevem / {senha}")
                print("     IMPORTANTE: Mude a senha padrão em produção!")
            else:
                print("   OK - Superusuário criado com senha personalizada")
        else:
            # Atualizar senha se variável de ambiente estiver definida e for diferente da padrão
            if 'SUPERUSER_PASSWORD' in os.environ and senha != senha_padrao:
                user.set_password(senha)
                user.save()
                print("   OK - Senha do superusuário atualizada")
            else:
                print("   OK - Superusuário já existe")
        
        return True
    except Exception as e:
        print(f"   AVISO - Não foi possível configurar superusuário: {e}")
        # Não retorna False pois isso não deve impedir a aplicação de iniciar
        return True

if __name__ == '__main__':
    main()
