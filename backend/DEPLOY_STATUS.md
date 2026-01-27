# Status do Deploy - LangGraph-App Integrado

## Deploy Iniciado

**Versão**: `app-20260121_161136`  
**Environment**: `Alphaadvisor-v6-env`  
**Status**: Atualizando (pode levar 5-10 minutos)  
**URL**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`

## O Que Foi Deployado

- ✅ Grafo MessagesState (`langgraph_graph.py`)
- ✅ Tools wrapper (`langgraph_tools.py`)
- ✅ LangGraph Server routes atualizadas
- ✅ Requirements atualizados (langgraph>=1.0.0, langchain-core>=0.3.0)
- ✅ Todas as 8 tools do backend integradas

## Monitorar Deploy

```bash
aws elasticbeanstalk describe-environments --environment-names Alphaadvisor-v6-env --region us-east-2 --query Environments[0].[Status,Health,VersionLabel,CNAME] --output table
```

## Após Deploy Completar

### 1. Verificar Health Check

```bash
curl http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/health
```

### 2. Testar Endpoint LangGraph

```bash
curl -X POST http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/assistants/search
```

### 3. Conectar LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Studio > Connect Studio to local agent
3. **Base URL**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
4. **Advanced Settings** > **Allowed Origins**:
   - `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
   - `https://smith.langchain.com`
5. Connect

### 4. Testar Tools

Envie mensagens que acionem as tools:
- "Qual é meu perfil de investidor?" → `obter_perfil`
- "Qual é o total da minha carteira?" → `obter_carteira`
- "Minha carteira está adequada?" → `analisar_adequacao`

## Variáveis de Ambiente Necessárias

Certifique-se de que estão configuradas no Elastic Beanstalk:
- `OPENAI_API_KEY` - Chave OpenAI
- `LANGSMITH_API_KEY` - Chave LangSmith (opcional, mas recomendado)
- `AI_MODEL` - Modelo a usar (padrão: gpt-4o)
- `LANGSMITH_PROJECT` - Projeto LangSmith (padrão: alphaadvisor)

## Troubleshooting

### Deploy falhando
- Verifique logs: `aws elasticbeanstalk describe-events --environment-name Alphaadvisor-v6-env --region us-east-2`
- Verifique se todas as dependências estão no `requirements.txt`

### Health check falhando
- Verifique se `/health` retorna 200
- Verifique timeout no health check

### Tools não funcionando
- Verifique se `OPENAI_API_KEY` está configurada
- Verifique logs do servidor para erros
