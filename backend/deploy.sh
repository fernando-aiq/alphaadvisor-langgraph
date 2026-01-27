#!/bin/bash

# Script de deploy para AWS Elastic Beanstalk

echo "🚀 Iniciando deploy do AlphaAdvisor Backend..."

# Verificar se EB CLI está instalado
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI não encontrado. Instale com: pip install awsebcli"
    exit 1
fi

# Verificar se está no diretório backend
if [ ! -f "application.py" ]; then
    echo "❌ Execute este script do diretório backend"
    exit 1
fi

# Verificar se ambiente já existe
if ! eb list &> /dev/null; then
    echo "📦 Inicializando ambiente EB..."
    eb init -p python-3.11 alphaadvisor-backend --region us-east-1
fi

# Verificar se ambiente foi criado
ENV_EXISTS=$(eb list 2>/dev/null | grep -c "alphaadvisor-env" || echo "0")

if [ "$ENV_EXISTS" -eq "0" ]; then
    echo "🏗️  Criando novo ambiente..."
    eb create alphaadvisor-env
else
    echo "🔄 Fazendo deploy no ambiente existente..."
    eb deploy
fi

echo "✅ Deploy concluído!"
echo ""
echo "📋 Próximos passos:"
echo "1. Obtenha a URL do ambiente: eb status"
echo "2. Atualize NEXT_PUBLIC_API_URL no Vercel com a URL do backend"
echo "3. Faça redeploy do frontend: cd ../frontend && vercel --prod"




