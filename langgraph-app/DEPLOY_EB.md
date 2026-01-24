# Deploy LangGraph Server para Elastic Beanstalk

## Pré-requisitos

1. AWS CLI instalado e configurado
2. Credenciais AWS configuradas (via `aws configure` ou variáveis de ambiente)
3. Python 3.11+ instalado

## Passo 1: Configurar Variáveis de Ambiente no EB

Após o primeiro deploy, configure as variáveis de ambiente no Elastic Beanstalk:

1. Acesse AWS Console → Elastic Beanstalk
2. Selecione o environment `Langgraph-v6-env`
3. Vá em **Configuration** → **Software** → **Environment properties**
4. Adicione:
   - `OPENAI_API_KEY` = sua chave OpenAI
   - `LANGSMITH_API_KEY` = sua chave LangSmith (opcional)
   - `AI_MODEL` = `gpt-4o` (opcional, padrão)
   - `LANGSMITH_PROJECT` = `alphaadvisor` (opcional)

## Passo 2: Executar Deploy

```bash
cd langgraph-app
deploy-v6-ohio.bat
```

O script vai:
1. Verificar credenciais AWS
2. Criar/verificar application e environment
3. Criar ZIP com o código
4. Fazer upload para S3
5. Criar versão e atualizar environment

## Passo 3: Monitorar Deploy

O deploy pode levar 5-10 minutos. Para monitorar:

```bash
aws elasticbeanstalk describe-environments --environment-names Langgraph-v6-env --region us-east-2 --query Environments[0].[Status,Health,VersionLabel,CNAME] --output table
```

## Passo 4: Obter URL

Após o deploy, a URL será algo como:
```
http://langgraph-v6-env.xxxxx.us-east-2.elasticbeanstalk.com
```

## Testar Endpoints

```bash
# Health check
curl http://sua-url.elasticbeanstalk.com/health

# Buscar assistentes
curl -X POST http://sua-url.elasticbeanstalk.com/assistants/search

# Criar thread e enviar mensagem
curl -X POST http://sua-url.elasticbeanstalk.com/threads \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "Qual é meu perfil de investidor?"}]
    }
  }'
```

## Conectar LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Studio > Connect Studio to local agent
3. Base URL: `http://sua-url.elasticbeanstalk.com`
4. Advanced Settings > Allowed Origins:
   - `http://sua-url.elasticbeanstalk.com`
   - `https://smith.langchain.com`
5. Connect

## Troubleshooting

### Erro: "Graph not loaded"
- Verifique se todas as dependências estão no `requirements.txt`
- Verifique logs: `aws elasticbeanstalk describe-events --environment-name Langgraph-v6-env --region us-east-2`

### Erro: "Module not found"
- Verifique se `src/agent/` está incluído no ZIP
- Verifique `PYTHONPATH` no `.ebextensions/langgraph.config`

### Health check falhando
- Verifique se `/health` retorna 200
- Verifique timeout no health check (aumentar se necessário)
