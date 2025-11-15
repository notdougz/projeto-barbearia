# Script para verificar qual servidor está rodando na porta 8000
# Uso: .\scripts\verificar-servidor.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICADOR DE SERVIDOR - PORTA 8000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica processos na porta 8000
Write-Host "1. Processos escutando na porta 8000:" -ForegroundColor Yellow
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq "Listen"}
if ($connections) {
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            $isDocker = $process.Path -like "*docker*" -or $process.ProcessName -like "*docker*" -or $process.ProcessName -eq "wslrelay"
            $tipo = if ($isDocker) { "🐳 DOCKER" } else { "🐍 PYTHON (Tradicional)" }
            Write-Host "   PID: $($conn.OwningProcess) | $tipo | $($process.ProcessName) | Iniciado: $($process.StartTime)" -ForegroundColor $(if ($isDocker) { "Green" } else { "Yellow" })
        }
    }
} else {
    Write-Host "   Nenhum processo encontrado na porta 8000" -ForegroundColor Red
}

Write-Host ""

# Verifica containers Docker
Write-Host "2. Containers Docker:" -ForegroundColor Yellow
$dockerContainers = docker ps --filter "publish=8000" --format "{{.Names}}: {{.Status}}" 2>$null
if ($dockerContainers) {
    Write-Host "   $dockerContainers" -ForegroundColor Green
} else {
    Write-Host "   Nenhum container Docker na porta 8000" -ForegroundColor Gray
}

Write-Host ""

# Testa qual servidor está respondendo
Write-Host "3. Testando resposta do servidor:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "   ✅ Servidor respondendo (Status: $($response.StatusCode))" -ForegroundColor Green
    
    # Verifica headers para identificar Docker
    $serverHeader = $response.Headers["Server"]
    $viaHeader = $response.Headers["Via"]
    
    if ($serverHeader -like "*gunicorn*" -or $viaHeader) {
        Write-Host "   🐳 Provavelmente DOCKER (Gunicorn detectado)" -ForegroundColor Green
    } else {
        Write-Host "   🐍 Provavelmente PYTHON tradicional (Django runserver)" -ForegroundColor Yellow
    }
    
    Write-Host "   Headers Server: $serverHeader" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Nenhum servidor respondendo" -ForegroundColor Red
}

Write-Host ""

# Verifica processos Python relacionados ao projeto
Write-Host "4. Processos Python do projeto:" -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*manage.py*" -or 
    $_.Path -like "*projeto-barbeiro*" -or
    $_.CommandLine -like "*runserver*"
}
if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        Write-Host "   PID: $($proc.Id) | $($proc.Path) | Iniciado: $($proc.StartTime)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Nenhum processo Python do projeto encontrado" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RECOMENDAÇÃO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para usar apenas o Docker:" -ForegroundColor Yellow
Write-Host "  1. Pare o servidor tradicional:" -ForegroundColor White
Write-Host "     Ctrl+C no terminal onde está rodando" -ForegroundColor Gray
Write-Host "     OU" -ForegroundColor Gray
Write-Host "     Stop-Process -Id <PID> -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Verifique se o Docker está rodando:" -ForegroundColor White
Write-Host "     docker-compose ps" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Acesse: http://localhost:8000" -ForegroundColor White
Write-Host ""

