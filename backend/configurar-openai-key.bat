@echo off
REM Script para configurar OPENAI_API_KEY no Elastic Beanstalk
REM Uso: configurar-openai-key.bat SUA_CHAVE_AQUI

setlocal enabledelayedexpansion

if "%1"=="" (
    echo.
    echo ERRO: Chave da OpenAI nao fornecida!
    echo.
    echo Uso: configurar-openai-key.bat SUA_CHAVE_AQUI
    echo.
    echo Exemplo:
    echo   configurar-openai-key.bat sk-proj-xxxxxxxxxxxxx
    echo.
    echo IMPORTANTE: Nao inclua aspas na chave
    echo.
    pause
    exit /b 1
)

set "OPENAI_KEY=%1"
set "ENV_NAME=Alphaadvisor-v6-env"
set "REGION=us-east-2"
set "APP_NAME=alphaadvisor-v6"

echo ========================================
echo   Configurando OPENAI_API_KEY
echo ========================================
echo.
echo Environment: %ENV_NAME%
echo Regiao: %REGION%
echo.

REM Verificar se AWS CLI esta instalado
aws --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: AWS CLI nao encontrado!
    exit /b 1
)

echo Configurando variavel de ambiente...
aws elasticbeanstalk update-environment ^
    --environment-name %ENV_NAME% ^
    --region %REGION% ^
    --option-settings ^
        Namespace=aws:elasticbeanstalk:application:environment,OptionName=OPENAI_API_KEY,Value=%OPENAI_KEY% ^
        Namespace=aws:elasticbeanstalk:application:environment,OptionName=AI_MODEL,Value=gpt-4o

if errorlevel 1 (
    echo.
    echo ERRO ao configurar variavel de ambiente
    pause
    exit /b 1
)

echo.
echo ========================================
echo   OK Configuracao concluida!
echo ========================================
echo.
echo A variavel OPENAI_API_KEY foi configurada.
echo O environment sera atualizado automaticamente.
echo.
echo Aguarde alguns minutos para o deploy completar.
echo.
echo Para verificar o status:
echo   aws elasticbeanstalk describe-environments --environment-names %ENV_NAME% --region %REGION% --query Environments[0].[Status,Health] --output table
echo.
pause

