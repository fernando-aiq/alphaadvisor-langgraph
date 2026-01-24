@echo off
REM Script para atualizar a URL da API no Vercel
REM Pré-requisito: Vercel CLI instalado (npm i -g vercel)

echo 🔄 Atualizando URL da API no Vercel
echo.

REM Verificar se Vercel CLI está instalado
where vercel >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Vercel CLI não encontrado.
    echo 📦 Instale com: npm i -g vercel
    pause
    exit /b 1
)

REM URL do backend
set "BACKEND_URL=http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"

echo 📋 URL do Backend: %BACKEND_URL%
echo.

REM Verificar se está logado
echo 🔐 Verificando login no Vercel...
vercel whoami >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Não está logado. Fazendo login...
    vercel login
)

echo.
echo 🔄 Removendo variável antiga (se existir)...
vercel env rm API_URL production --yes 2>nul
vercel env rm API_URL preview --yes 2>nul
vercel env rm API_URL development --yes 2>nul
vercel env rm NEXT_PUBLIC_API_URL production --yes 2>nul
vercel env rm NEXT_PUBLIC_API_URL preview --yes 2>nul
vercel env rm NEXT_PUBLIC_API_URL development --yes 2>nul

echo.
echo ➕ Adicionando nova variável API_URL...
echo %BACKEND_URL% | vercel env add API_URL production
echo %BACKEND_URL% | vercel env add API_URL preview
echo %BACKEND_URL% | vercel env add API_URL development

echo.
echo ➕ Adicionando nova variável NEXT_PUBLIC_API_URL...
echo %BACKEND_URL% | vercel env add NEXT_PUBLIC_API_URL production
echo %BACKEND_URL% | vercel env add NEXT_PUBLIC_API_URL preview
echo %BACKEND_URL% | vercel env add NEXT_PUBLIC_API_URL development

echo.
echo ✅ Variáveis de ambiente atualizadas!
echo.
echo 📋 Próximos passos:
echo 1. Faça redeploy: vercel --prod
echo 2. Ou aguarde o próximo deploy automático
echo.
pause


