@echo off
REM ============================================================================
REM Script para finalizar o deploy atualizando o environment com a versao mais recente
REM ============================================================================

setlocal enabledelayedexpansion

set "ENV_NAME=Alphaadvisor-v4-env"
set "REGION=us-east-1"
set "APP_NAME=alphaadvisor-backend"

echo ========================================
echo   Finalizando Deploy
echo ========================================
echo.

echo Listando versoes disponiveis...
aws elasticbeanstalk describe-application-versions --application-name %APP_NAME% --region %REGION% --max-items 5 --query ApplicationVersions[*].[VersionLabel,DateCreated] --output table
echo.
echo Digite o nome da versao que deseja deployar (ex: app-20260109_152054):
set /p LATEST_VERSION="Versao: "

if "%LATEST_VERSION%"=="" (
    echo ERRO: Versao nao informada
    pause
    exit /b 1
)

echo Versao mais recente: %LATEST_VERSION%
echo.
echo Atualizando environment...
aws elasticbeanstalk update-environment --application-name %APP_NAME% --environment-name %ENV_NAME% --version-label %LATEST_VERSION% --region %REGION%

if errorlevel 1 (
    echo.
    echo ERRO ao atualizar environment
    echo.
    echo Tente novamente em alguns minutos ou atualize manualmente via AWS Console
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

