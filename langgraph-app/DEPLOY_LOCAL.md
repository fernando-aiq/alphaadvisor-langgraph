# Deploy Local - LangGraph Server com LangSmith

Este guia mostra como rodar o LangGraph Server localmente e conectar ao LangSmith para tracing.

## Pré-requisitos

- Python 3.10+
- Conta no LangSmith (https://smith.langchain.com/)
- API Key do LangSmith
- API Key do OpenAI

## Passo 1: Instalar Dependências

```bash
cd langgraph-app
pip install -e . "langgraph-cli[inmem]"
```

Isso instala:
- O projeto local (`-e .`)
- LangGraph CLI com suporte a memória (`langgraph-cli[inmem]`)

## Passo 2: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do `langgraph-app`:

```bash
# .env
LANGSMITH_API_KEY=lsv2_sua_api_key_aqui
LANGSMITH_PROJECT=alphaadvisor
OPENAI_API_KEY=sk-sua_openai_key_aqui
```

**Como obter as API keys:**

1. **LangSmith API Key:**
   - Acesse https://smith.langchain.com/
   - Vá em **Settings** → **API Keys**
   - Crie ou copie uma API key (começa com `lsv2_...`)

2. **OpenAI API Key:**
   - Acesse https://platform.openai.com/api-keys
   - Crie uma nova API key

## Passo 3: Iniciar o LangGraph Server

```bash
langgraph dev
```

Isso vai:
- Iniciar o servidor local na porta **8555**
- Abrir o LangGraph Studio automaticamente no navegador
- Conectar automaticamente ao LangSmith se `LANGSMITH_API_KEY` estiver configurada

**Ou use os scripts:**
- Windows: `start-local.bat`
- Linux/Mac: `./start-local.sh`

## Passo 4: Acessar o LangGraph Studio

O comando `langgraph dev --port 8555` abre automaticamente:
- **Studio UI**: http://localhost:8555 (interface visual para testar o agente)
- **API Endpoint**: http://localhost:8555/threads (API REST)

## Passo 5: Verificar Traces no LangSmith

1. Acesse https://smith.langchain.com/
2. Vá em **Projects** → **alphaadvisor** (ou o nome do seu projeto)
3. Você verá os traces aparecendo em tempo real quando:
   - Enviar mensagens pelo Studio UI
   - Fazer chamadas à API REST
   - Testar o agente

## Endpoints Disponíveis

Quando o servidor está rodando, você tem acesso a:

### 1. LangGraph Studio (Interface Visual)
```
http://localhost:8555
```
- Interface gráfica para testar o agente
- Visualização do grafo em tempo real
- Edição de estado e replay

### 2. API REST

**Criar thread e enviar mensagem:**
```bash
curl -X POST http://localhost:8555/threads \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [{"role": "user", "content": "Multiplique 5 por 3"}]
    }
  }'
```

**Listar threads:**
```bash
curl http://localhost:8555/threads
```

**Obter estado de uma thread:**
```bash
curl http://localhost:8555/threads/{thread_id}
```

## Configuração Avançada

### Porta Customizada

O servidor está configurado para usar a porta **8555** por padrão. Para usar outra porta:

```bash
langgraph dev --port 8080
```

### Host Customizado

```bash
langgraph dev --host 0.0.0.0
```

### Modo Headless (sem abrir navegador)

```bash
langgraph dev --no-browser
```

## Verificando Conexão com LangSmith

Ao iniciar o servidor, você deve ver logs como:

```
[INFO] LangGraph Server iniciado em http://localhost:8555
[INFO] LangSmith tracing habilitado
[INFO] Projeto: alphaadvisor
```

Se não aparecer, verifique:
1. Se `LANGSMITH_API_KEY` está no `.env`
2. Se a API key é válida
3. Se o arquivo `.env` está na raiz do `langgraph-app`

## Troubleshooting

### Erro: "langgraph-cli não encontrado"

```bash
pip install --upgrade "langgraph-cli[inmem]"
```

### Erro: "Module not found"

```bash
pip install -e .
```

### Traces não aparecem no LangSmith

1. Verifique se `LANGSMITH_API_KEY` está correta no `.env`
2. Teste a API key manualmente:
   ```python
   from langsmith import Client
   client = Client(api_key="sua_key")
   print(client.list_projects())
   ```
3. Verifique os logs do servidor para erros

### Porta já em uso

Use uma porta diferente:
```bash
langgraph dev --port 8556
```

### Conectar LangSmith Studio (https://smith.langchain.com/)

Para conectar o LangSmith Studio ao servidor local:

1. Acesse https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. **Base URL**: `http://127.0.0.1:8555`
4. **IMPORTANTE**: Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione:
   ```
   http://127.0.0.1:8555
   http://localhost:8555
   ```
6. Clique em **Connect**

**Nota**: Chrome 142+ pode bloquear conexões HTTP de sites HTTPS. Se isso acontecer:
- Use `http://127.0.0.1:8555` em vez de `http://localhost:8555`
- Ou use `langgraph dev --port 8555 --tunnel` para criar um túnel HTTPS

## Próximos Passos

1. **Testar o agente no Studio**: Envie mensagens e veja o fluxo em tempo real
2. **Explorar traces no LangSmith**: Analise cada execução detalhadamente
3. **Customizar o grafo**: Modifique `src/agent/graph_chat.py` para suas necessidades
4. **Adicionar tools**: Crie novas ferramentas em `src/agent/tools.py`

## Referências

- [LangGraph Server Docs](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)
- [LangGraph Studio Docs](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/)
- [LangSmith Tracing](https://docs.smith.langchain.com/tracing)
