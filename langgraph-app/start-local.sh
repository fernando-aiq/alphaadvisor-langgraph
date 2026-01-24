#!/bin/bash
# Script para iniciar LangGraph Server localmente com LangSmith

echo "========================================"
echo "  LangGraph Server - Deploy Local"
echo "========================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "langgraph.json" ]; then
    echo "ERRO: Execute este script do diretório langgraph-app"
    exit 1
fi

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "AVISO: Arquivo .env não encontrado"
    if [ -f ".env.example" ]; then
        echo "Criando .env a partir do .env.example..."
        cp ".env.example" ".env"
        echo ""
        echo "IMPORTANTE: Configure as seguintes variáveis no .env:"
        echo "  - LANGSMITH_API_KEY=lsv2_..."
        echo "  - OPENAI_API_KEY=sk-..."
        echo "  - LANGSMITH_PROJECT=alphaadvisor"
        echo ""
        read -p "Pressione Enter para continuar..."
    else
        echo "ERRO: .env.example não encontrado"
        echo "Crie um arquivo .env com:"
        echo "  LANGSMITH_API_KEY=lsv2_..."
        echo "  OPENAI_API_KEY=sk-..."
        echo "  LANGSMITH_PROJECT=alphaadvisor"
        exit 1
    fi
fi

# Verificar se langgraph-cli está instalado
if ! command -v langgraph &> /dev/null; then
    echo "LangGraph CLI não encontrado. Instalando..."
    pip install -e . "langgraph-cli[inmem]"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao instalar LangGraph CLI"
        exit 1
    fi
fi

echo ""
echo "Iniciando LangGraph Server..."
echo ""
echo "O servidor será iniciado em: http://localhost:8555"
echo "O LangGraph Studio abrirá automaticamente no navegador"
echo ""
echo "Para parar o servidor, pressione Ctrl+C"
echo ""

langgraph dev --port 8555
