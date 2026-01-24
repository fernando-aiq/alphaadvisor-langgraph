@echo off
REM Script para iniciar LangGraph Server localmente com LangSmith

echo ========================================
echo   LangGraph Server - Deploy Local
echo ========================================
echo.

REM Verificar se está no diretório correto
if not exist "langgraph.json" (
    echo ERRO: Execute este script do diretório langgraph-app
    pause
    exit /b 1
)

REM Verificar se .env existe
if not exist ".env" (
    echo AVISO: Arquivo .env não encontrado
    echo Criando .env a partir do .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo.
        echo IMPORTANTE: Configure as seguintes variáveis no .env:
        echo   - LANGSMITH_API_KEY=lsv2_...
        echo   - OPENAI_API_KEY=sk-...
        echo   - LANGSMITH_PROJECT=alphaadvisor
        echo.
        pause
    ) else (
        echo ERRO: .env.example não encontrado
        echo Crie um arquivo .env com:
        echo   LANGSMITH_API_KEY=lsv2_...
        echo   OPENAI_API_KEY=sk-...
        echo   LANGSMITH_PROJECT=alphaadvisor
        pause
        exit /b 1
    )
)

REM Verificar se langgraph-cli está instalado
where langgraph >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo LangGraph CLI não encontrado. Instalando...
    pip install -e . "langgraph-cli[inmem]"
    if %ERRORLEVEL% NEQ 0 (
        echo ERRO: Falha ao instalar LangGraph CLI
        pause
        exit /b 1
    )
)

echo.
echo Iniciando LangGraph Server...
echo.
echo O servidor será iniciado em: http://localhost:8555
echo O LangGraph Studio abrirá automaticamente no navegador
echo.
echo Para parar o servidor, pressione Ctrl+C
echo.

langgraph dev --port 8555

pause
