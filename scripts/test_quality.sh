#!/bin/bash

# Script para testar qualidade de código localmente
# Execute: bash scripts/test_quality.sh

echo "🔍 TESTE DE QUALIDADE DE CÓDIGO"
echo "================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependências
echo "📦 Verificando dependências..."
if ! command_exists python; then
    echo -e "${RED}❌ Python não encontrado${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}❌ pip não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python e pip encontrados${NC}"

# Instalar dependências se necessário
echo "📥 Instalando dependências..."
pip install -r requirements.txt >/dev/null 2>&1

# Teste 1: Black (formatação)
echo ""
echo "🎨 Testando formatação com Black..."
if black --check . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Formatação OK${NC}"
else
    echo -e "${YELLOW}⚠️  Formatação precisa ser corrigida${NC}"
    echo "Execute: black ."
fi

# Teste 2: isort (imports)
echo ""
echo "📚 Testando organização de imports com isort..."
if isort --check-only . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Imports organizados${NC}"
else
    echo -e "${YELLOW}⚠️  Imports precisam ser organizados${NC}"
    echo "Execute: isort ."
fi

# Teste 3: flake8 (linting)
echo ""
echo "🔍 Testando linting com flake8..."
if flake8 . >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Linting OK${NC}"
else
    echo -e "${YELLOW}⚠️  Problemas de linting encontrados${NC}"
    echo "Execute: flake8 ."
fi

# Teste 4: bandit (segurança)
echo ""
echo "🔒 Testando segurança com bandit..."
if bandit -r agendamentos/ -q >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Segurança OK${NC}"
else
    echo -e "${YELLOW}⚠️  Problemas de segurança encontrados${NC}"
    echo "Execute: bandit -r agendamentos/"
fi

# Teste 5: safety (vulnerabilidades)
echo ""
echo "🛡️  Testando vulnerabilidades com safety..."
if safety check >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Nenhuma vulnerabilidade encontrada${NC}"
else
    echo -e "${YELLOW}⚠️  Vulnerabilidades encontradas${NC}"
    echo "Execute: safety check"
fi

# Teste 6: Testes básicos
echo ""
echo "🧪 Executando testes básicos..."
if python manage.py test agendamentos.tests.ClienteModelTest agendamentos.tests.ServicoModelTest >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Testes básicos passaram${NC}"
else
    echo -e "${RED}❌ Testes básicos falharam${NC}"
    echo "Execute: python manage.py test"
fi

# Resumo final
echo ""
echo "📊 RESUMO DO TESTE DE QUALIDADE"
echo "================================"
echo "🎨 Black: Verificação de formatação"
echo "📚 isort: Verificação de imports"
echo "🔍 flake8: Verificação de linting"
echo "🔒 bandit: Verificação de segurança"
echo "🛡️  safety: Verificação de vulnerabilidades"
echo "🧪 Django: Testes básicos"
echo ""
echo "💡 Para corrigir problemas automaticamente:"
echo "   black ."
echo "   isort ."
echo "   flake8 ."
echo ""
echo "🚀 Para executar todos os testes:"
echo "   python -m pytest --cov=agendamentos"
echo ""
echo "✅ Teste de qualidade concluído!"
