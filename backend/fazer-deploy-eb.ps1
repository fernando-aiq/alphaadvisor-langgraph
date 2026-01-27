# Script simplificado para deploy no Elastic Beanstalk
Write-Host "🚀 Deploy Backend no Elastic Beanstalk" -ForegroundColor Cyan
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

Write-Host "✅ EB CLI encontrado" -ForegroundColor Green
Write-Host ""

# Verificar ambiente
Write-Host "📋 Ambientes disponíveis:" -ForegroundColor Yellow
eb list

Write-Host ""
$envName = Read-Host "Digite o nome do ambiente (ou Enter para criar 'alphaadvisor-env')"

if ([string]::IsNullOrWhiteSpace($envName)) {
    $envName = "alphaadvisor-env"
}

# Verificar se ambiente existe
Write-Host ""
Write-Host "🔍 Verificando ambiente: $envName" -ForegroundColor Yellow
eb status $envName 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Ambiente '$envName' não encontrado." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Criando novo ambiente..." -ForegroundColor Cyan
    Write-Host "Isso pode levar 10-15 minutos..." -ForegroundColor Yellow
    Write-Host ""
    
    # Configurar variáveis antes de criar
    Write-Host "📝 Configurando variáveis de ambiente..." -ForegroundColor Yellow
    $frontendUrl = "https://alphaadvisor-rpgso0oq2-aiqgen.vercel.app"
    Write-Host "FRONTEND_URL será configurado como: $frontendUrl" -ForegroundColor Cyan
    
    # Criar ambiente
    eb create $envName --envvars FRONTEND_URL=$frontendUrl
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao criar ambiente" -ForegroundColor Red
        Write-Host "Tentando criar sem variáveis..." -ForegroundColor Yellow
        eb create $envName
        if ($LASTEXITCODE -ne 0) {
            exit 1
        }
    }
} else {
    Write-Host "✅ Ambiente encontrado: $envName" -ForegroundColor Green
    
    # Configurar variáveis
    Write-Host ""
    Write-Host "📝 Configurando variáveis de ambiente..." -ForegroundColor Yellow
    $frontendUrl = "https://alphaadvisor-rpgso0oq2-aiqgen.vercel.app"
    eb setenv FRONTEND_URL=$frontendUrl --environment $envName
    
    Write-Host ""
    Write-Host "🚀 Fazendo deploy..." -ForegroundColor Yellow
    eb deploy $envName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro no deploy" -ForegroundColor Red
        Write-Host "Verifique os logs: eb logs" -ForegroundColor Yellow
        exit 1
    }
}

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
    Write-Host ""
    Write-Host "📝 Próximos passos:" -ForegroundColor Yellow
    Write-Host "  1. Teste: curl $url/api/health"
    Write-Host "  2. Configure NEXT_PUBLIC_API_URL no Vercel: $url"
    Write-Host "  3. Faça redeploy do frontend: cd ../frontend && vercel --prod"
} else {
    Write-Host "📋 Para obter a URL, execute: eb status $envName" -ForegroundColor Cyan
    Write-Host "   Ou: eb open" -ForegroundColor Cyan
}

Write-Host ""

