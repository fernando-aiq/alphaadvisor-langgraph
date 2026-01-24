# Solução para Erro 404: "Thread or assistant not found"

## Problema

Ao usar o LangGraph Server na porta 8222, você pode receber o erro:
```
HTTP 404: {"detail":"Thread or assistant not found."}
```

## Causas Comuns

### 1. Assistant ID Incorreto

O LangGraph CLI (`langgraph dev`) gera automaticamente um **UUID** para cada assistant. Você **não pode usar** o nome do grafo (ex: "agent") como `assistant_id`.

**Solução:** Sempre busque o `assistant_id` correto antes de usar:

```python
import requests

# 1. Buscar o assistant_id correto
response = requests.post("http://localhost:8222/assistants/search", json={})
assistants = response.json()
assistant_id = assistants[0]["assistant_id"]  # UUID gerado automaticamente

# 2. Usar o UUID correto ao criar threads
payload = {
    "assistant_id": assistant_id,  # Use o UUID, não "agent"
    "input": {
        "messages": [{"role": "user", "content": "Olá"}]
    }
}
response = requests.post("http://localhost:8222/threads", json=payload)
```

### 2. Thread ID Não Existe

Se você tentar atualizar ou acessar uma thread que não existe, receberá 404.

**Solução:** Sempre crie a thread primeiro ou verifique se ela existe:

```python
# Criar thread primeiro
response = requests.post("http://localhost:8222/threads", json={
    "assistant_id": assistant_id,
    "input": {"messages": [{"role": "user", "content": "Olá"}]}
})
thread_id = response.json()["thread_id"]

# Agora você pode usar o thread_id
```

### 3. Endpoint Incorreto para Atualizar Thread

O LangGraph CLI usa endpoints diferentes do servidor customizado.

**Para atualizar uma thread (adicionar nova mensagem):**

```python
# ❌ ERRADO - Não funciona no LangGraph CLI
requests.post(f"http://localhost:8222/threads/{thread_id}", json={...})

# ✅ CORRETO - Criar um novo "run" na thread
requests.post(f"http://localhost:8222/threads/{thread_id}/runs", json={
    "assistant_id": assistant_id,
    "input": {
        "messages": [{"role": "user", "content": "Nova mensagem"}]
    }
})
```

## Exemplo Completo

```python
import requests

BASE_URL = "http://localhost:8222"

# 1. Buscar assistant_id
response = requests.post(f"{BASE_URL}/assistants/search", json={})
assistant_id = response.json()[0]["assistant_id"]
print(f"Assistant ID: {assistant_id}")

# 2. Criar thread
response = requests.post(f"{BASE_URL}/threads", json={
    "assistant_id": assistant_id,
    "input": {
        "messages": [{"role": "user", "content": "Olá"}]
    }
})
thread_id = response.json()["thread_id"]
print(f"Thread ID: {thread_id}")

# 3. Adicionar nova mensagem (criar novo run)
response = requests.post(f"{BASE_URL}/threads/{thread_id}/runs", json={
    "assistant_id": assistant_id,
    "input": {
        "messages": [{"role": "user", "content": "Recomende investimentos"}]
    }
})
run_id = response.json()["run_id"]
print(f"Run ID: {run_id}")

# 4. Aguardar resultado (opcional)
response = requests.post(f"{BASE_URL}/threads/{thread_id}/runs/{run_id}/join")
result = response.json()
print(f"Resultado: {result}")
```

## Endpoints Disponíveis

### Assistants
- `POST /assistants/search` - Buscar assistants
- `GET /assistants/{assistant_id}` - Obter assistant específico

### Threads
- `POST /threads` - Criar nova thread
- `GET /threads/{thread_id}` - Obter thread específica
- `PATCH /threads/{thread_id}` - Atualizar thread (metadados)
- `DELETE /threads/{thread_id}` - Deletar thread

### Thread Runs (Execuções)
- `POST /threads/{thread_id}/runs` - Criar nova execução na thread
- `GET /threads/{thread_id}/runs` - Listar execuções
- `POST /threads/{thread_id}/runs/{run_id}/join` - Aguardar resultado da execução
- `GET /threads/{thread_id}/runs/{run_id}` - Obter execução específica

## Verificação Rápida

Para verificar se o servidor está funcionando:

```bash
# Verificar se o servidor está rodando
curl http://localhost:8222/ok

# Listar assistants
curl -X POST http://localhost:8222/assistants/search -H "Content-Type: application/json" -d "{}"
```

## Notas Importantes

1. **Sempre use UUIDs**: O LangGraph CLI gera UUIDs automaticamente. Não use strings como "agent".

2. **Criar thread antes de usar**: Sempre crie a thread primeiro com `POST /threads` antes de tentar atualizá-la.

3. **Usar `/runs` para novas mensagens**: Para adicionar uma nova mensagem a uma thread existente, use `POST /threads/{thread_id}/runs`, não `POST /threads/{thread_id}`.

4. **Aguardar execução**: Se você criar um run em background, pode precisar usar `/join` ou `/wait` para obter o resultado.

## Troubleshooting

### Erro 422: "Invalid assistant ID: must be a UUID"
- **Causa**: Você está usando uma string em vez de UUID
- **Solução**: Busque o `assistant_id` correto com `/assistants/search`

### Erro 404: "Thread or assistant not found"
- **Causa**: Thread ou assistant não existe
- **Solução**: 
  1. Verifique se o `assistant_id` está correto
  2. Verifique se a `thread_id` existe
  3. Crie a thread primeiro se necessário

### Erro 405: "Method Not Allowed"
- **Causa**: Endpoint ou método HTTP incorreto
- **Solução**: Verifique a documentação OpenAPI em `http://localhost:8222/docs`
