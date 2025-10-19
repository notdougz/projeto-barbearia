# Script PowerShell para testar qualidade de código localmente
# Execute: .\scripts\test_quality.ps1

Write-Host "🔍 TESTE DE QUALIDADE DE CÓDIGO" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Função para verificar se comando existe
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Verificar dependências
Write-Host "📦 Verificando dependências..." -ForegroundColor Yellow
if (-not (Test-Command "python")) {
    Write-Host "❌ Python não encontrado" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "pip")) {
    Write-Host "❌ pip não encontrado" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python e pip encontrados" -ForegroundColor Green

# Instalar dependências se necessário
Write-Host "📥 Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt | Out-Null

# Teste 1: Black (formatação)
Write-Host ""
Write-Host "🎨 Testando formatação com Black..." -ForegroundColor Yellow
$blackResult = & black --check . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Formatação OK" -ForegroundColor Green
} else {
    Write-Host "⚠️  Formatação precisa ser corrigida" -ForegroundColor Yellow
    Write-Host "Execute: black ." -ForegroundColor Cyan
}

# Teste 2: isort (imports)
Write-Host ""
Write-Host "📚 Testando organização de imports com isort..." -ForegroundColor Yellow
$isortResult = & isort --check-only . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Imports organizados" -ForegroundColor Green
} else {
    Write-Host "⚠️  Imports precisam ser organizados" -ForegroundColor Yellow
    Write-Host "Execute: isort ." -ForegroundColor Cyan
}

# Teste 3: flake8 (linting)
Write-Host ""
Write-Host "🔍 Testando linting com flake8..." -ForegroundColor Yellow
$flake8Result = & flake8 . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Linting OK" -ForegroundColor Green
} else {
    Write-Host "⚠️  Problemas de linting encontrados" -ForegroundColor Yellow
    Write-Host "Execute: flake8 ." -ForegroundColor Cyan
}

# Teste 4: bandit (segurança)
Write-Host ""
Write-Host "🔒 Testando segurança com bandit..." -ForegroundColor Yellow
$banditResult = & bandit -r agendamentos/ -q 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Segurança OK" -ForegroundColor Green
} else {
    Write-Host "⚠️  Problemas de segurança encontrados" -ForegroundColor Yellow
    Write-Host "Execute: bandit -r agendamentos/" -ForegroundColor Cyan
}

# Teste 5: safety (vulnerabilidades)
Write-Host ""
Write-Host "🛡️  Testando vulnerabilidades com safety..." -ForegroundColor Yellow
$safetyResult = & safety check 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Nenhuma vulnerabilidade encontrada" -ForegroundColor Green
} else {
    Write-Host "⚠️  Vulnerabilidades encontradas" -ForegroundColor Yellow
    Write-Host "Execute: safety check" -ForegroundColor Cyan
}

# Teste 6: Testes básicos
Write-Host ""
Write-Host "🧪 Executando testes básicos..." -ForegroundColor Yellow
$testResult = & python manage.py test agendamentos.tests.ClienteModelTest agendamentos.tests.ServicoModelTest 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Testes básicos passaram" -ForegroundColor Green
} else {
    Write-Host "❌ Testes básicos falharam" -ForegroundColor Red
    Write-Host "Execute: python manage.py test" -ForegroundColor Cyan
}

# Resumo final
Write-Host ""
Write-Host "📊 RESUMO DO TESTE DE QUALIDADE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎨 Black: Verificação de formatação" -ForegroundColor White
Write-Host "📚 isort: Verificação de imports" -ForegroundColor White
Write-Host "🔍 flake8: Verificação de linting" -ForegroundColor White
Write-Host "🔒 bandit: Verificação de segurança" -ForegroundColor White
Write-Host "🛡️  safety: Verificação de vulnerabilidades" -ForegroundColor White
Write-Host "🧪 Django: Testes básicos" -ForegroundColor White
Write-Host ""
Write-Host "💡 Para corrigir problemas automaticamente:" -ForegroundColor Yellow
Write-Host "   black ." -ForegroundColor Cyan
Write-Host "   isort ." -ForegroundColor Cyan
Write-Host "   flake8 ." -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Para executar todos os testes:" -ForegroundColor Yellow
Write-Host "   python -m pytest --cov=agendamentos" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Teste de qualidade concluído!" -ForegroundColor Green
