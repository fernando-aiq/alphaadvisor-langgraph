@echo off
REM ============================================================================
REM Script para aguardar processamento da versao e fazer deploy automaticamente
REM ============================================================================

setlocal enabledelayedexpansion

set "ENV_NAME=Alphaadvisor-v4-env"
set "REGION=us-east-1"
set "APP_NAME=alphaadvisor-backend"
set "VERSION_LABEL=app-20260109_152054"

echo ========================================
echo   Aguardando Processamento e Deploy
echo ========================================
echo.
echo Versao: %VERSION_LABEL%
echo.

REM Aguardar versao ser processada
echo Aguardando versao ser processada...
set /a WAIT_COUNT=0
set /a MAX_WAIT=120
set /a INTERVAL=5

:wait_loop
timeout /t %INTERVAL% /nobreak >nul
set /a WAIT_COUNT+=%INTERVAL%

REM Verificar status usando PowerShell para evitar problemas
for /f "tokens=*" %%i in ('powershell -Command "aws elasticbeanstalk describe-application-versions --application-name %APP_NAME% --version-labels %VERSION_LABEL% --region %REGION% --query ApplicationVersions[0].Status --output text 2>$null"') do set "VERSION_STATUS=%%i"

if "%VERSION_STATUS%"=="PROCESSED" (
    echo.
    echo OK Versao processada!
    goto deploy_now
)

if %WAIT_COUNT% lss %MAX_WAIT% (
    echo Aguardando... (%WAIT_COUNT%/%MAX_WAIT% segundos) - Status: %VERSION_STATUS%
    goto wait_loop
)

echo.
echo AVISO: Timeout aguardando processamento
echo Status atual: %VERSION_STATUS%
echo Tentando fazer deploy mesmo assim...
goto deploy_now

:deploy_now
echo.
echo Fazendo deploy da versao %VERSION_LABEL%...
aws elasticbeanstalk update-environment --application-name %APP_NAME% --environment-name %ENV_NAME% --version-label %VERSION_LABEL% --region %REGION%

if errorlevel 1 (
    echo.
    echo ERRO ao fazer deploy
    echo.
    echo Tente novamente em alguns minutos ou via AWS Console
) else (
    echo.
    echo OK Deploy iniciado!
    echo.
    echo O deploy pode levar 5-10 minutos para completar.
    echo.
    echo Para monitorar:
    echo   aws elasticbeanstalk describe-environments --environment-names %ENV_NAME% --region %REGION% --query Environments[0].[Status,Health,VersionLabel] --output table
)

echo.
pause

