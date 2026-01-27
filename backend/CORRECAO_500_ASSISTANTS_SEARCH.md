# Correção do Erro 500 em POST /assistants/search

## Problema

O endpoint `POST /assistants/search` estava retornando 500 Internal Server Error no Elastic Beanstalk, impedindo o LangSmith Studio de conectar.

## Correções Implementadas

### 1. Lazy Loading do Grafo

**Arquivo**: `backend/app/routes/langgraph_server.py`

- Removido import direto do grafo no topo do arquivo
- Implementado lazy loading: grafo só é carregado quando necessário
- Adicionado tratamento de erro para capturar erros de importação

**Antes**:
```python
from app.services.langgraph_graph import graph
```

**Depois**:
```python
def get_graph():
    """Lazy loading do grafo"""
    global _graph, _graph_error
    if _graph is None:
        try:
            from app.services.langgraph_graph import graph
            _graph = graph
        except Exception as e:
            _graph_error = e
            raise
    return _graph
```

### 2. Simplificação do Endpoint search_assistants

**Arquivo**: `backend/app/routes/langgraph_server.py`

- Endpoint `search_assistants` não depende mais do grafo
- Removida qualquer tentativa de carregar o grafo neste endpoint
- Endpoint agora é totalmente independente e retorna lista estática

### 3. Tratamento de Erro Robusto

**Arquivos**: 
- `backend/app/routes/langgraph_server.py`
- `backend/app/services/langgraph_graph.py`
- `backend/app/services/langgraph_tools.py`

- Adicionados try/except em todos os imports críticos
- Logs detalhados em cada etapa
- Erros são logados com traceback completo

### 4. Health Check Melhorado

**Arquivo**: `backend/app/routes/langgraph_server.py`

- Health check não falha se o grafo não estiver disponível
- Retorna status "partial" se grafo não disponível, mas servidor está rodando
- Permite que o servidor funcione mesmo se o grafo falhar ao carregar

## Resultado Esperado

Após essas correções:

1. **POST /assistants/search** retorna 200 mesmo se o grafo não estiver carregado
2. **Logs detalhados** mostram exatamente onde erros ocorrem
3. **Lazy loading** evita erros no startup se houver problema com imports
4. **LangSmith Studio** consegue conectar e listar assistentes

## Próximo Passo

Fazer novo deploy para aplicar as correções:

```bash
cd backend
deploy-v6-ohio.bat
```

Após deploy, o endpoint `/assistants/search` deve funcionar corretamente.
