# Integração Backend Flask - LangGraph Server

## Status: INTEGRAÇÃO COMPLETA

O servidor LangGraph na porta 8555 agora usa todas as tools do backend Flask.

## O Que Foi Implementado

### 1. Tools do Backend Integradas

Todas as 8 tools do backend foram adaptadas e integradas:

- ✅ `obter_perfil` - Busca perfil do cliente
- ✅ `obter_carteira` - Busca carteira do cliente
- ✅ `analisar_adequacao` - Analisa adequação ao perfil
- ✅ `analisar_alinhamento_objetivos` - Analisa alinhamento com objetivos
- ✅ `analisar_diversificacao` - Analisa diversificação
- ✅ `recomendar_rebalanceamento` - Recomenda rebalanceamento
- ✅ `calcular_projecao` - Calcula projeções
- ✅ `buscar_oportunidades` - Busca oportunidades de investimento

### 2. Arquivos Criados/Modificados

**Criados:**
- `langgraph-app/src/agent/backend_tools.py` - Tools adaptadas do backend
- `langgraph-app/src/agent/mock_data.py` - Dados mockados (CARTEIRA, PERFIL_JOAO)

**Modificados:**
- `langgraph-app/src/agent/graph_chat.py` - Grafo atualizado para usar tools do backend

### 3. Grafo Atualizado

O grafo agora:
- Usa `MessagesState` (compatível com LangSmith Studio)
- Tem 8 tools do backend disponíveis
- Usa modelo configurável via `AI_MODEL` (padrão: gpt-4o)
- Sistema prompt atualizado para contexto de investimentos

## Como Usar

### 1. Iniciar Servidor

```bash
cd langgraph-app
langgraph dev --port 8555
```

### 2. Conectar no LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. **Base URL**: `http://127.0.0.1:8555`
4. **Advanced Settings** > **Allowed Origins**:
   ```
   http://127.0.0.1:8555
   http://localhost:8555
   ```
5. Clique em **Connect**

### 3. Testar Tools

Perguntas que acionam diferentes tools:

- **"Qual é meu perfil de investidor?"** → `obter_perfil`
- **"Qual é o total da minha carteira?"** → `obter_carteira`
- **"Minha carteira está adequada ao meu perfil?"** → `analisar_adequacao`
- **"Minha carteira está alinhada com meus objetivos?"** → `analisar_alinhamento_objetivos`
- **"Como está a diversificação da minha carteira?"** → `analisar_diversificacao`
- **"Preciso rebalancear minha carteira?"** → `recomendar_rebalanceamento`
- **"Quanto terei em 5 anos?"** → `calcular_projecao`
- **"Quais oportunidades de investimento você recomenda?"** → `buscar_oportunidades`

## Verificar Traces no LangSmith

Após conectar no Studio e enviar mensagens:
1. Vá em **Projects** > **alphaadvisor** (ou seu projeto)
2. Veja os traces com todas as tool calls
3. Visualize o fluxo completo do grafo

## Testes

Execute os scripts de teste:

```bash
# Testar grafo localmente
python test_backend_tools.py

# Testar integração completa
python test_integration_completa.py

# Testar conexão Studio
python test_langsmith_connection.py
```

## Diferenças do Backend Flask

- **Estado**: Usa `MessagesState` (simples) em vez de `AgentState` (complexo)
- **Grafo**: ReAct pattern simples (agent → tools → agent → end)
- **Sem conditional edges**: Não há routing bypass/react, apenas ReAct dinâmico
- **Tools**: Mesmas tools, mas adaptadas para formato LangChain `@tool`

## Próximos Passos

1. ✅ Integração completa
2. ⏭️ Testar no LangSmith Studio
3. ⏭️ Verificar traces e tool calls
4. ⏭️ Ajustar prompts se necessário
