@echo off
echo ========================================
echo   DEPLOY CHAT AGENT - ALPHAADVISOR
echo ========================================
echo.

REM Verificar se estamos no diretório correto
if not exist "package.json" (
    echo ERRO: Execute este script do diretório frontend
    pause
    exit /b 1
)

echo [1/5] Instalando dependências...
call npm install
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependências
    pause
    exit /b 1
)

echo.
echo [2/5] Configurando variáveis de ambiente no Vercel...
echo.
echo ATENCAO: Configure as seguintes variáveis manualmente no Vercel:
echo   - NEXT_PUBLIC_API_URL=https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app
echo   - NEXT_PUBLIC_ASSISTANT_ID=agent
echo   - NEXT_PUBLIC_LANGSMITH_API_KEY=<SUA_CHAVE_AQUI>
echo.
echo Configurando NEXT_PUBLIC_API_URL...
echo https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app | vercel env add NEXT_PUBLIC_API_URL production
echo https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app | vercel env add NEXT_PUBLIC_API_URL preview
echo https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app | vercel env add NEXT_PUBLIC_API_URL development

echo.
echo Configurando NEXT_PUBLIC_ASSISTANT_ID...
echo agent | vercel env add NEXT_PUBLIC_ASSISTANT_ID production
echo agent | vercel env add NEXT_PUBLIC_ASSISTANT_ID preview
echo agent | vercel env add NEXT_PUBLIC_ASSISTANT_ID development

echo.
echo Configurando NEXT_PUBLIC_LANGSMITH_API_KEY...
echo ATENCAO: Configure manualmente a chave da API no Vercel
echo vercel env add NEXT_PUBLIC_LANGSMITH_API_KEY production
echo vercel env add NEXT_PUBLIC_LANGSMITH_API_KEY preview
echo vercel env add NEXT_PUBLIC_LANGSMITH_API_KEY development

echo.
echo [3/5] Fazendo commit das mudanças...
git add .
git commit -m "feat: Integração completa do Agent Chat UI no frontend AlphaAdvisor" || echo "Nenhuma mudança para commitar"

echo.
echo [4/5] Fazendo push para o repositório...
git push origin master || git push origin main

echo.
echo [5/5] Fazendo deploy no Vercel...
vercel --prod

echo.
echo ========================================
echo   DEPLOY CONCLUÍDO!
echo ========================================
echo.
echo Variáveis de ambiente configuradas:
echo   - NEXT_PUBLIC_API_URL=https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app
echo   - NEXT_PUBLIC_ASSISTANT_ID=agent
echo   - NEXT_PUBLIC_LANGSMITH_API_KEY=<CONFIGURE_MANUALMENTE>
echo.
echo Acesse: https://alphaadvisor.vercel.app/chat-agent
echo.
pause
