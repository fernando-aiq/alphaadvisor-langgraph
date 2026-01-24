@echo off
REM ============================================================================
REM Script de Deploy para AWS Elastic Beanstalk - LangGraph Server
REM Environment: Langgraph-v6-env
REM Region: us-east-2 (Ohio)
REM ============================================================================

setlocal enabledelayedexpansion

REM Garantir que o script roda dentro da pasta langgraph-app
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Configuracoes
set "ENV_NAME=Langgraph-v6-env"
set "REGION=us-east-2"
set "APP_NAME=langgraph-v6"
set "PLATFORM=Python 3.11"
set "INSTANCE_TYPE=t3.small"

REM Verificar credenciais AWS via variaveis de ambiente ou AWS CLI
set "AWS_ACCESS_KEY=%AWS_ACCESS_KEY_ID%"
set "AWS_SECRET_KEY=%AWS_SECRET_ACCESS_KEY%"

REM Se nao estiverem nas variaveis de ambiente, tentar obter do AWS CLI
if "%AWS_ACCESS_KEY%"=="" (
    echo Credenciais nao encontradas em variaveis de ambiente. Verificando AWS CLI...
    for /f "tokens=*" %%i in ('aws configure get aws_access_key_id --output text 2^>nul') do set "AWS_ACCESS_KEY=%%i"
    for /f "tokens=*" %%i in ('aws configure get aws_secret_access_key --output text 2^>nul') do set "AWS_SECRET_KEY=%%i"
    
    if "!AWS_ACCESS_KEY!"=="" (
        echo ERRO: Credenciais AWS nao encontradas!
        echo Configure as variaveis de ambiente ou AWS CLI:
        echo   AWS_ACCESS_KEY_ID
        echo   AWS_SECRET_ACCESS_KEY
        echo   Ou: aws configure
        exit /b 1
    )
    echo OK Credenciais encontradas no AWS CLI
)

REM Configurar credenciais AWS
set "AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY%"
set "AWS_SECRET_ACCESS_KEY=%AWS_SECRET_KEY%"
set "AWS_DEFAULT_REGION=%REGION%"

echo ========================================
echo   Deploy para Elastic Beanstalk - LangGraph Server
echo   Environment: %ENV_NAME%
echo   Region: %REGION% (Ohio)
echo ========================================
echo.

REM Verificar se AWS CLI esta instalado
echo [1/8] Verificando AWS CLI...
aws --version >nul 2>&1
if errorlevel 1 (
    echo   ERRO AWS CLI nao encontrado!
    echo   Instale: https://aws.amazon.com/cli/
    exit /b 1
)
for /f "tokens=*" %%i in ('aws --version 2^>^&1') do echo   OK AWS CLI encontrado: %%i

REM Verificar credenciais AWS
echo [2/8] Verificando credenciais AWS...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo   ERRO ao validar credenciais
    exit /b 1
)
for /f "tokens=2" %%i in ('aws sts get-caller-identity --query Account --output text 2^>nul') do set "ACCOUNT_ID=%%i"
echo   OK Credenciais validas (Account: %ACCOUNT_ID%)

REM Verificar se application existe, criar se nao existir
echo [3/8] Verificando application...
for /f "tokens=*" %%i in ('aws elasticbeanstalk describe-applications --application-names %APP_NAME% --region %REGION% --query Applications[0].ApplicationName --output text 2^>nul') do set "APP_EXISTS=%%i"
if "%APP_EXISTS%"=="%APP_NAME%" (
    echo   OK Application encontrada: %APP_NAME%
) else (
    echo   Application nao encontrada. Criando...
    aws elasticbeanstalk create-application --application-name %APP_NAME% --description "LangGraph Server - AlphaAdvisor Agent" --region %REGION% >nul 2>&1
    if errorlevel 1 (
        echo   ERRO ao criar application
        exit /b 1
    )
    echo   OK Application criada: %APP_NAME%
)

REM Verificar se environment existe
echo [4/8] Verificando environment...
for /f "tokens=*" %%i in ('aws elasticbeanstalk describe-environments --environment-names %ENV_NAME% --region %REGION% --query Environments[0].Status --output text 2^>nul') do set "ENV_STATUS=%%i"
if "%ENV_STATUS%"=="" (
    echo   AVISO: Environment %ENV_NAME% nao encontrado na regiao %REGION%!
    echo   Criando environment...
    aws elasticbeanstalk create-environment --application-name %APP_NAME% --environment-name %ENV_NAME% --solution-stack-name "%PLATFORM% 64bit Amazon Linux 2" --region %REGION% --option-settings Namespace=aws:autoscaling:launchconfiguration,OptionName=InstanceType,Value=%INSTANCE_TYPE% >nul 2>&1
    if errorlevel 1 (
        echo   ERRO ao criar environment
        echo   Tente criar manualmente via AWS Console
        exit /b 1
    )
    echo   OK Environment criado: %ENV_NAME%
    echo   Aguardando 60 segundos para environment ficar pronto...
    ping 127.0.0.1 -n 61 >nul 2>&1
) else (
    echo   OK Environment encontrado: %ENV_NAME% (Status: %ENV_STATUS%)
)

REM Criar ZIP
echo [5/8] Criando arquivo ZIP...
for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set "DATETIME=%%i"
set "VERSION_LABEL=app-%DATETIME:~0,8%_%DATETIME:~8,6%"
set "ZIP_FILE=deploy-%VERSION_LABEL%.zip"

REM Remover ZIPs antigos
del /q deploy-*.zip 2>nul

REM Criar script Python temporario para criar ZIP
echo import zipfile > create_zip_temp.py
echo import os >> create_zip_temp.py
echo from pathlib import Path >> create_zip_temp.py
echo. >> create_zip_temp.py
echo exclude_patterns = ['*.zip', 'data', '.git', 'venv', 'env', '.env', '*_DEPLOY*.txt', '*_DEPLOY*.md', 'deploy*.ps1', 'deploy*.bat', '__pycache__', '*.pyc', 'test_*.py', 'start_*.bat', 'start_*.sh', 'RESTART_*.bat', '.elasticbeanstalk', 'gerar-zip*.py', 'criar-zip*.py', 'aguardar*.py', 'verificar*.py', 'create_zip_temp.py', '.github', 'tests', 'uv.lock', 'Makefile'] >> create_zip_temp.py
echo exclude_dirs = {'data', '.git', 'venv', 'env', '__pycache__', '.elasticbeanstalk', '.github', 'tests'} >> create_zip_temp.py
echo. >> create_zip_temp.py
echo zip_path = '%ZIP_FILE%' >> create_zip_temp.py
echo base_path = Path('.') >> create_zip_temp.py
echo. >> create_zip_temp.py
echo with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf: >> create_zip_temp.py
echo     for root, dirs, files in os.walk('.'): >> create_zip_temp.py
echo         dirs[:] = [d for d in dirs if d not in exclude_dirs and not any(Path(root, d).match(p) for p in exclude_patterns)] >> create_zip_temp.py
echo         for file in files: >> create_zip_temp.py
echo             file_path = Path(root, file) >> create_zip_temp.py
echo             if any(file_path.match(p) for p in exclude_patterns): >> create_zip_temp.py
echo                 continue >> create_zip_temp.py
echo             arcname = str(file_path.relative_to(base_path)).replace('\\', '/') >> create_zip_temp.py
echo             zipf.write(str(file_path), arcname) >> create_zip_temp.py
echo. >> create_zip_temp.py
echo print(f'ZIP criado: {zip_path}') >> create_zip_temp.py

python create_zip_temp.py
if errorlevel 1 (
    echo   ERRO ao criar ZIP
    exit /b 1
)
del create_zip_temp.py

if exist "%ZIP_FILE%" (
    echo   OK ZIP criado: %ZIP_FILE%
) else (
    echo   ERRO: ZIP nao foi criado
    exit /b 1
)

REM Obter bucket S3
echo [6/8] Preparando upload para S3...
for /f "tokens=*" %%i in ('aws elasticbeanstalk create-storage-location --region %REGION% --query S3Bucket --output text 2^>nul') do set "S3_BUCKET=%%i"
if "%S3_BUCKET%"=="" set "S3_BUCKET=elasticbeanstalk-%REGION%-%ACCOUNT_ID%"
echo   OK Bucket S3: %S3_BUCKET%

REM Upload para S3
echo   Fazendo upload...
aws s3 cp "%ZIP_FILE%" "s3://%S3_BUCKET%/%VERSION_LABEL%.zip" --region %REGION% >nul 2>&1
if errorlevel 1 (
    echo   ERRO ao fazer upload
    exit /b 1
)
echo   OK Upload concluido

REM Criar versao da aplicacao e atualizar environment
echo [7/8] Criando versao e atualizando environment...
aws elasticbeanstalk create-application-version --application-name %APP_NAME% --version-label %VERSION_LABEL% --source-bundle "S3Bucket=%S3_BUCKET%,S3Key=%VERSION_LABEL%.zip" --region %REGION%
if errorlevel 1 (
    echo   ERRO ao criar versao
    exit /b 1
)
echo   OK Versao criada: %VERSION_LABEL%

REM Aguardar versao ficar processada
echo   Aguardando 30 segundos para versao ser processada...
ping 127.0.0.1 -n 31 >nul 2>&1

REM Atualizar environment
echo   Atualizando environment...
echo   (Isso pode levar alguns minutos para completar...)
aws elasticbeanstalk update-environment --application-name %APP_NAME% --environment-name %ENV_NAME% --version-label %VERSION_LABEL% --region %REGION%
set "UPDATE_RESULT=%ERRORLEVEL%"
if %UPDATE_RESULT% EQU 0 (
    echo   OK Deploy iniciado com sucesso!
) else (
    echo   AVISO: Pode ter havido um erro, mas a versao foi criada.
    echo   Voce pode atualizar manualmente via AWS Console ou aguardar alguns minutos e tentar novamente.
    echo   Versao criada: %VERSION_LABEL%
)

REM Obter URL do environment
echo [8/8] Obtendo URL do environment...
for /f "tokens=*" %%i in ('aws elasticbeanstalk describe-environments --environment-names %ENV_NAME% --region %REGION% --query Environments[0].CNAME --output text 2^>nul') do set "ENV_URL=%%i"
if not "%ENV_URL%"=="" (
    set "FULL_URL=http://%ENV_URL%"
    echo   OK URL: %FULL_URL%
) else (
    set "FULL_URL=N/A (aguardando provisionamento)"
)

REM Limpar ZIP local
del "%ZIP_FILE%" 2>nul
echo ZIP local removido

echo.
echo ========================================
echo   OK Deploy iniciado com sucesso!
echo ========================================
echo.
echo Versao: %VERSION_LABEL%
echo Environment: %ENV_NAME%
echo Region: %REGION% (Ohio)
echo URL: %FULL_URL%
echo Status: Atualizando (pode levar 5-10 minutos)
echo.
echo Para monitorar o status:
echo   aws elasticbeanstalk describe-environments --environment-names %ENV_NAME% --region %REGION% --query Environments[0].[Status,Health,VersionLabel,CNAME] --output table
echo.
echo IMPORTANTE: Configure as variaveis de ambiente no Elastic Beanstalk:
echo   - OPENAI_API_KEY
echo   - LANGSMITH_API_KEY (opcional)
echo   - AI_MODEL (opcional, padrao: gpt-4o)
echo   - LANGSMITH_PROJECT (opcional, padrao: alphaadvisor)
echo.

endlocal
