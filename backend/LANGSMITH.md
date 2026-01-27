# Configuração LangSmith - AlphaAdvisor

## Visão Geral

O AlphaAdvisor está configurado para enviar traces automaticamente para o LangSmith quando a API key estiver configurada. Isso permite observabilidade completa de todas as execuções do agente, incluindo:

- Execuções do LangGraph (grafo de estados)
- Chamadas de tools (obter_perfil, analisar_adequacao, etc.)
- Chamadas LLM (OpenAI)
- Execuções do AgentExecutor (ReAct pattern)

## Configuração

### 1. Obter API Key do LangSmith

1. Acesse [https://smith.langchain.com/](https://smith.langchain.com/)
2. Crie uma conta ou faça login
3. Vá em **Settings** → **API Keys**
4. Crie uma nova API key ou copie uma existente
5. A API key começa com `lsv2_...`

### 2. Configurar Variáveis de Ambiente

Adicione as seguintes variáveis ao arquivo `.env` do backend:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=lsv2_sua_api_key_aqui
LANGSMITH_PROJECT=alphaadvisor
LANGSMITH_TRACING=true
```

**Variáveis:**
- `LANGSMITH_API_KEY` (obrigatório): Sua API key do LangSmith
- `LANGSMITH_PROJECT` (opcional): Nome do projeto no LangSmith (padrão: `alphaadvisor`)
- `LANGSMITH_TRACING` (opcional): Habilitar/desabilitar tracing (padrão: `true` se API key estiver configurada)

### 3. Verificar Configuração

Ao iniciar o backend, você verá logs informativos:

```
[Startup] LangSmith configurado - Projeto: alphaadvisor
[Startup] Tracing automático habilitado para LangGraph e AgentExecutor
```

Se não estiver configurado:

```
[Startup] LangSmith não configurado (LANGSMITH_API_KEY não encontrada)
[Startup] Para habilitar tracing, configure LANGSMITH_API_KEY no .env
```

## Como Funciona

### LangGraph Tracing

O `LangGraphAgent` usa automaticamente `LangSmithCheckpointer` quando `LANGSMITH_API_KEY` está configurado:

- **Checkpointer**: Persiste estado do grafo no LangSmith
- **Tracing automático**: Cada execução do grafo gera um trace completo
- **Replay**: Permite re-executar traces para debugging

### AgentExecutor Tracing

O `AgentService` usa o decorator `@traceable` do LangSmith:

- Todas as chamadas de `process_message` são rastreadas
- Tool calls individuais aparecem como spans no trace
- Chamadas LLM são automaticamente capturadas

### Tools Tracing

Todas as tools em `agent_tools.py` usam `@traceable_tool`:

- `obter_perfil`
- `obter_carteira`
- `analisar_adequacao`
- `calcular_projecao`
- `buscar_oportunidades`
- `analisar_alinhamento_objetivos`
- `analisar_diversificacao`
- `recomendar_rebalanceamento`
- `gerar_explicacao`

## Visualizando Traces

### 1. Acessar Dashboard

1. Acesse [https://smith.langchain.com/](https://smith.langchain.com/)
2. Vá em **Projects** → **alphaadvisor** (ou o nome do seu projeto)
3. Veja todos os traces em tempo real

### 2. Explorar um Trace

Cada trace contém:

- **Input**: Mensagem do usuário e contexto
- **Graph Execution**: Nós visitados (detect_intent, route_decision, etc.)
- **Tool Calls**: Todas as tools executadas com inputs/outputs
- **LLM Calls**: Prompts e respostas completas
- **Output**: Resposta final do agente
- **Metadata**: Trace ID, timestamps, duração

### 3. Filtrar Traces

Use os filtros do dashboard para:

- Buscar por trace_id específico
- Filtrar por data/hora
- Filtrar por erro/sucesso
- Filtrar por tool específica
- Filtrar por intent detectado

## Queries Úteis

### Buscar Traces com Erros

```
status:error
```

### Buscar Traces de uma Tool Específica

```
tool_name:analisar_adequacao
```

### Buscar Traces por Intent

```
metadata.intent:analisar_alinhamento_objetivos
```

### Buscar Traces de Hoje

```
start_time:today
```

## Debugging

### Replay de Traces

1. Abra um trace no dashboard
2. Clique em **Replay** para re-executar
3. Útil para debugar problemas específicos

### Comparar Traces

1. Selecione múltiplos traces
2. Compare execuções para identificar diferenças
3. Analise performance e custos

## Performance e Custos

### Monitoramento

- **Latência**: Tempo de execução de cada nó
- **Custos**: Tokens usados em cada chamada LLM
- **Erros**: Taxa de erro por tool/node

### Otimização

Use os dados do LangSmith para:

- Identificar nós lentos
- Otimizar prompts
- Reduzir chamadas desnecessárias de tools
- Melhorar routing decisions

## Troubleshooting

### Traces não aparecem

1. Verifique se `LANGSMITH_API_KEY` está configurada
2. Verifique logs do backend para erros
3. Teste a API key manualmente:
   ```python
   from langsmith import Client
   client = Client(api_key=os.getenv('LANGSMITH_API_KEY'))
   print(client.list_projects())
   ```

### Erro "LangSmithCheckpointer não disponível"

- Instale/atualize langsmith: `pip install --upgrade langsmith langgraph`
- Verifique versão: `pip show langsmith langgraph`

### Traces incompletos

- Verifique se todas as tools têm `@traceable_tool`
- Verifique se `@traceable` está no `process_message`
- Verifique logs para erros de tracing

## Referências

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/checkpointing/)
- [LangSmith Tracing](https://docs.smith.langchain.com/tracing)
