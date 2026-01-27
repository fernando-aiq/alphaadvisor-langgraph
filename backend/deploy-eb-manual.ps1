# Script para deploy manual no Elastic Beanstalk (sem Git)
# Cria um ZIP e faz deploy diretamente

Write-Host "🚀 Deploy Manual no Elastic Beanstalk" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório backend
if (-not (Test-Path "application.py")) {
    Write-Host "❌ Execute este script do diretório backend" -ForegroundColor Red
    exit 1
}

# Verificar EB CLI
$ebInstalled = Get-Command eb -ErrorAction SilentlyContinue
if (-not $ebInstalled) {
    Write-Host "❌ EB CLI não encontrado. Instale com: pip install awsebcli" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Criando arquivo ZIP para deploy..." -ForegroundColor Yellow

# Criar ZIP com arquivos necessários
$zipFile = "deploy-eb-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"

# Arquivos e diretórios a incluir
$filesToInclude = @(
    "application.py",
    "Procfile",
    "requirements.txt",
    "app",
    ".ebextensions"
)

# Criar ZIP
$zipPath = Join-Path $PWD $zipFile
Compress-Archive -Path $filesToInclude -DestinationPath $zipPath -Force

if (-not (Test-Path $zipPath)) {
    Write-Host "❌ Erro ao criar ZIP" -ForegroundColor Red
    exit 1
}

Write-Host "✅ ZIP criado: $zipFile" -ForegroundColor Green
Write-Host ""

# Verificar ambiente
Write-Host "🔍 Verificando ambiente..." -ForegroundColor Yellow
$envName = Read-Host "Digite o nome do ambiente (ou Enter para 'alphaadvisor-env')"

if ([string]::IsNullOrWhiteSpace($envName)) {
    $envName = "alphaadvisor-env"
}

# Verificar se ambiente existe
eb status $envName 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Ambiente '$envName' não encontrado." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Criando novo ambiente..." -ForegroundColor Cyan
    Write-Host "Isso pode levar 10-15 minutos..." -ForegroundColor Yellow
    Write-Host ""
    
    # Criar ambiente
    eb create $envName --source $zipPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao criar ambiente" -ForegroundColor Red
        Remove-Item $zipPath -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Host "✅ Ambiente encontrado: $envName" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Fazendo deploy..." -ForegroundColor Yellow
    
    # Fazer deploy
    eb deploy $envName --source $zipPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro no deploy" -ForegroundColor Red
        Remove-Item $zipPath -ErrorAction SilentlyContinue
        exit 1
    }
}

# Limpar ZIP
Remove-Item $zipPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host ""

# Obter URL
Write-Host "📋 Obtendo informações do ambiente..." -ForegroundColor Yellow
$statusOutput = eb status $envName 2>&1 | Out-String

if ($statusOutput -match "CNAME:\s+(\S+)") {
    $cname = $matches[1]
    $url = "http://$cname"
    Write-Host ""
    Write-Host "🌐 URL do Backend: $url" -ForegroundColor Green
    Write-Host "   Health Check: $url/api/health" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Configure variáveis de ambiente: eb setenv FRONTEND_URL=https://alphaadvisor-rpgso0oq2-aiqgen.vercel.app"
Write-Host "  2. Configure NEXT_PUBLIC_API_URL no Vercel"
Write-Host "  3. Faça redeploy do frontend"
Write-Host ""

