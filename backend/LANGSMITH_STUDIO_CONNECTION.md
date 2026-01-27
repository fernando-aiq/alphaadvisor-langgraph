# Conectar LangSmith Studio ao Elastic Beanstalk

Este guia explica como conectar o LangSmith Studio ao backend AlphaAdvisor deployado no Elastic Beanstalk.

## Endpoints Criados

Os seguintes endpoints foram adicionados ao backend para compatibilidade com LangGraph Server:

- `GET /langgraph/assistants` - Lista grafos disponíveis
- `POST /langgraph/threads` - Cria thread e executa grafo
- `GET /langgraph/threads` - Lista threads
- `GET /langgraph/threads/{thread_id}` - Obtém estado de uma thread
- `POST /langgraph/threads/{thread_id}` - Atualiza thread existente
- `POST /langgraph/threads/{thread_id}/stream` - Stream de execução (SSE)
- `GET /langgraph/health` - Health check do servidor LangGraph

## Como Conectar no LangSmith Studio

### 1. Acesse o LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** no menu lateral
3. Clique em **Connect Studio to local agent**

### 2. Configure a Conexão

No formulário de conexão:

- **Base URL**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
  - Ou use a URL do seu ambiente Elastic Beanstalk

- **Custom Headers** (opcional):
  - Se necessário, adicione headers customizados
  - Por exemplo: `X-LangSmith-API-Key` se configurado

### 3. Testar a Conexão

Após conectar:

1. O Studio deve listar o assistente "agent" disponível
2. Você pode enviar mensagens e ver o fluxo do grafo em tempo real
3. Os traces serão automaticamente enviados para o LangSmith

## Testando Localmente

Antes de fazer deploy, você pode testar localmente:

```bash
# Iniciar o backend local
cd backend
python application.py
# Ou
gunicorn application:app

# Em outro terminal, testar os endpoints
python test_langgraph_server.py
```

## Formato de Requisição

### Criar Thread e Executar

```bash
curl -X POST http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/langgraph/threads \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"role": "user", "content": "qual é minha carteira?"}
      ]
    }
  }'
```

### Resposta Esperada

```json
{
  "thread_id": "uuid-da-thread",
  "values": {
    "messages": [
      {"role": "user", "content": "qual é minha carteira?"},
      {"role": "assistant", "content": "Resposta do agente..."}
    ]
  },
  "config": {
    "configurable": {
      "thread_id": "uuid-da-thread"
    }
  }
}
```

## Troubleshooting

### Erro: "LangGraph não está disponível"

- Verifique se `OPENAI_API_KEY` está configurada no Elastic Beanstalk
- Verifique os logs do backend para erros de inicialização

### Erro: CORS

- Verifique se as origens do LangSmith estão na lista de CORS permitidas
- As origens `https://smith.langchain.com` e `https://studio.langchain.com` já estão configuradas

### Erro: "Thread não encontrada"

- O endpoint `GET /langgraph/threads/{thread_id}` ainda não implementa persistência completa
- Use `POST /langgraph/threads` para criar novas threads

### Traces não aparecem no LangSmith

- Verifique se `LANGSMITH_API_KEY` está configurada no Elastic Beanstalk
- Verifique se `LANGSMITH_PROJECT` está configurado (padrão: `alphaadvisor`)
- Verifique os logs do backend para erros de conexão com LangSmith

## Configuração no Elastic Beanstalk

Certifique-se de que as seguintes variáveis de ambiente estão configuradas:

```bash
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=alphaadvisor
LANGSMITH_TRACING=true
FRONTEND_URL=https://...
```

Para configurar via AWS CLI:

```bash
eb setenv OPENAI_API_KEY=sk-... LANGSMITH_API_KEY=lsv2_... LANGSMITH_PROJECT=alphaadvisor
```

Ou via AWS Console:
1. Elastic Beanstalk > Seu Ambiente
2. Configuration > Software > Environment properties
3. Adicione as variáveis acima

## Próximos Passos

1. Fazer deploy do backend atualizado no Elastic Beanstalk
2. Testar conexão do Studio com a URL do Elastic Beanstalk
3. Verificar traces no LangSmith
4. Explorar o grafo no Studio para debugging e otimização
