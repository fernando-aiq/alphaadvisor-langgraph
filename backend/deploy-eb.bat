@echo off
REM ============================================================================
REM Script para fazer deploy do backend no Elastic Beanstalk
REM ============================================================================

setlocal enabledelayedexpansion

echo ========================================
echo   Deploy Backend - AlphaAdvisor (EB)
echo ========================================
echo.

REM Verificar se EB CLI está instalado
where eb >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] EB CLI nao encontrado
    echo Instale com: pip install awsebcli
    pause
    exit /b 1
)

echo [OK] EB CLI encontrado
echo.

REM Verificar se está no diretório backend
if not exist "application.py" (
    echo [ERRO] Execute este script do diretorio backend
    pause
    exit /b 1
)

REM Listar ambientes disponíveis
echo [1/5] Verificando ambientes disponiveis...
eb list
echo.

REM Perguntar qual ambiente usar
set /p ENV_NAME="Digite o nome do ambiente (ou Enter para 'alphaadvisor-env'): "
if "!ENV_NAME!"=="" set ENV_NAME=alphaadvisor-env

echo.
echo [2/5] Verificando ambiente: !ENV_NAME!
eb status !ENV_NAME! >nul 2>&1
set STATUS_ERROR=%ERRORLEVEL%

if %STATUS_ERROR% NEQ 0 (
    echo [AVISO] Ambiente !ENV_NAME! nao encontrado.
    echo.
    set /p CREATE="Deseja criar um novo ambiente? (s/n): "
    if /i not "!CREATE!"=="s" (
        echo Deploy cancelado.
        pause
        exit /b 1
    )
    
    echo.
    echo [3/5] Criando novo ambiente: !ENV_NAME!
    echo Isso pode levar 10-15 minutos...
    echo.
    
    REM Configurar variáveis de ambiente
    set FRONTEND_URL=https://alphaadvisor-rpgso0oq2-aiqgen.vercel.app
    echo Configurando FRONTEND_URL: !FRONTEND_URL!
    
    REM Criar ambiente com variáveis
    eb create !ENV_NAME! --envvars FRONTEND_URL=!FRONTEND_URL!
    
    if %ERRORLEVEL% NEQ 0 (
        echo [AVISO] Erro ao criar com variaveis. Tentando sem variaveis...
        eb create !ENV_NAME!
        if %ERRORLEVEL% NEQ 0 (
            echo [ERRO] Falha ao criar ambiente
            pause
            exit /b 1
        )
    )
    
    echo.
    echo [OK] Ambiente criado com sucesso!
    echo.
    echo Aguarde alguns minutos para o ambiente ficar pronto...
    echo Depois execute este script novamente para fazer o deploy.
    pause
    exit /b 0
) else (
    echo [OK] Ambiente encontrado: !ENV_NAME!
    echo.
    
    REM Configurar variáveis de ambiente
    echo [3/5] Configurando variaveis de ambiente...
    set FRONTEND_URL=https://alphaadvisor-rpgso0oq2-aiqgen.vercel.app
    echo Configurando FRONTEND_URL: !FRONTEND_URL!
    
    eb setenv FRONTEND_URL=!FRONTEND_URL! --environment !ENV_NAME!
    
    if %ERRORLEVEL% NEQ 0 (
        echo [AVISO] Erro ao configurar variaveis. Continuando...
    ) else (
        echo [OK] Variaveis configuradas!
    )
    
    echo.
    echo [4/5] Fazendo deploy no ambiente !ENV_NAME!...
    echo Isso pode levar alguns minutos...
    echo.
    eb deploy !ENV_NAME!
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Deploy falhou
        echo.
        echo Verifique os logs: eb logs
        pause
        exit /b 1
    )
)

echo.
echo [5/5] Verificando status do ambiente...
eb status !ENV_NAME!

echo.
echo ========================================
echo   Deploy concluido!
echo ========================================
echo.

REM Tentar obter URL do ambiente
echo Obtendo URL do ambiente...
eb status !ENV_NAME! > status_temp.txt 2>&1
findstr /C:"CNAME:" status_temp.txt >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2" %%i in ('findstr /C:"CNAME:" status_temp.txt') do (
        set CNAME=%%i
        echo.
        echo [OK] URL do Backend: http://!CNAME!
        echo      Health Check: http://!CNAME!/api/health
        echo.
    )
)
del status_temp.txt 2>nul

echo Proximos passos:
echo   1. Teste o health check: curl http://[URL]/api/health
echo   2. Configure NEXT_PUBLIC_API_URL no Vercel com a URL do backend
echo   3. Faca redeploy do frontend: cd ..\frontend ^&^& vercel --prod
echo.

pause
