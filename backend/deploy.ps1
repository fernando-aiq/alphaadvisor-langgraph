# Script PowerShell de deploy para AWS Elastic Beanstalk

Write-Host "🚀 Iniciando deploy do AlphaAdvisor Backend..." -ForegroundColor Cyan

# Verificar se EB CLI está instalado
$ebExists = Get-Command eb -ErrorAction SilentlyContinue
if (-not $ebExists) {
    Write-Host "❌ EB CLI não encontrado. Instale com: pip install awsebcli" -ForegroundColor Red
    exit 1
}

# Verificar se está no diretório backend
if (-not (Test-Path "application.py")) {
    Write-Host "❌ Execute este script do diretório backend" -ForegroundColor Red
    exit 1
}

# Verificar se ambiente já existe
try {
    $envs = eb list 2>&1
    $envExists = $envs -match "alphaadvisor-env"
} catch {
    $envExists = $false
}

if (-not $envExists) {
    Write-Host "📦 Inicializando ambiente EB..." -ForegroundColor Yellow
    eb init -p python-3.11 alphaadvisor-backend --region us-east-1
    
    Write-Host "🏗️  Criando novo ambiente..." -ForegroundColor Yellow
    eb create alphaadvisor-env
} else {
    Write-Host "🔄 Fazendo deploy no ambiente existente..." -ForegroundColor Yellow
    eb deploy
}

Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Obtenha a URL do ambiente: eb status"
Write-Host "2. Atualize NEXT_PUBLIC_API_URL no Vercel com a URL do backend"
Write-Host "3. Faça redeploy do frontend: cd ../frontend; vercel --prod"




