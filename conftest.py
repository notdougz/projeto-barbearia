import os
import django
from django.conf import settings

# Configurar Django para pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia.settings')
django.setup()

# Configurar pytest para encontrar arquivos tests.py
def pytest_collect_file(file_path, parent):
    """Permitir que pytest encontre arquivos tests.py"""
    if file_path.name == "tests.py":
        from _pytest.python import Module
        return Module.from_parent(parent, path=file_path)
