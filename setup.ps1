#!/usr/bin/env powershell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SOS Drive - Setup de Desenvolvimento  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Checar se Python está instalado
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python encontrado: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Write-Host "   Instale Python 3.10+ de https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
Write-Host ""

# Instalar dependências
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Dependências instaladas com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Para iniciar a aplicação, execute:" -ForegroundColor Cyan
    Write-Host "   .venv\Scripts\reflex.exe run" -ForegroundColor White
    Write-Host ""
    Write-Host "📱 Acessar em:" -ForegroundColor Cyan
    Write-Host "   http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}
