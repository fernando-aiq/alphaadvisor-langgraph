# Como Conectar LangSmith Studio ao Servidor Local

Este guia explica como conectar o LangSmith Studio (https://smith.langchain.com/) ao LangGraph Server rodando localmente na porta 8555.

## Pré-requisitos

1. LangGraph Server rodando localmente na porta 8555
2. Navegador moderno (Chrome, Firefox, Edge)
3. Conta no LangSmith (https://smith.langchain.com/)

## Passo a Passo

### 1. Iniciar o Servidor Local

Execute um dos seguintes comandos:

**Windows:**
```bash
cd langgraph-app
start-local.bat
```

**Linux/Mac:**
```bash
cd langgraph-app
./start-local.sh
```

**Ou manualmente:**
```bash
cd langgraph-app
langgraph dev --port 8555
```

O servidor estará disponível em: `http://localhost:8555`

### 2. Verificar se o Servidor Está Funcionando

Teste os endpoints:

```bash
# Testar endpoint raiz
curl http://127.0.0.1:8555/

# Testar busca de assistentes
curl -X POST http://127.0.0.1:8555/assistants/search \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

### 3. Conectar no LangSmith Studio

1. **Acesse o LangSmith Studio**
   - URL: https://smith.langchain.com/
   - Vá em **Studio** no menu lateral

2. **Conectar ao Servidor Local**
   - Clique em **Connect Studio to local agent**
   - **Base URL**: `http://127.0.0.1:8555`

3. **Configurar Advanced Settings** (CRÍTICO!)
   - Clique em **Advanced Settings**
   - Em **Allowed Origins**, adicione EXATAMENTE:
     ```
     http://127.0.0.1:8555
     http://localhost:8555
     ```
   - **IMPORTANTE**: Use URLs completas com protocolo e porta!
   - ❌ NÃO use apenas `localhost` ou `127.0.0.1`
   - ✅ USE `http://127.0.0.1:8555`

4. **Conectar**
   - Clique em **Connect**
   - O Studio deve listar o assistente "agent"

## Troubleshooting

### Erro: "Connection failed"

**Causa 1: Chrome 142+ bloqueando HTTP**

Chrome 142+ bloqueia conexões HTTP de sites HTTPS por padrão (Private Network Access).

**Soluções:**

1. **Usar 127.0.0.1 em vez de localhost** (recomendado)
   - Base URL: `http://127.0.0.1:8555`
   - Allowed Origins: `http://127.0.0.1:8555`

2. **Desabilitar PNA no Chrome**
   - Acesse: `chrome://flags/#block-insecure-private-network-requests`
   - Desabilite "Block insecure private network requests"
   - Reinicie o Chrome

3. **Usar túnel HTTPS** (melhor solução)
   ```bash
   langgraph dev --port 8555 --tunnel
   ```
   - Use a URL HTTPS fornecida pelo tunnel no Studio

**Causa 2: Allowed Origins incorreto**

Verifique se você adicionou as URLs completas:
- ✅ Correto: `http://127.0.0.1:8555`
- ❌ Incorreto: `localhost` ou `127.0.0.1`

**Causa 3: Servidor não está rodando**

Verifique se o servidor está rodando:
```bash
curl http://127.0.0.1:8555/
```

### Erro: "Origin is not allowed"

**Solução**: Adicione a origem em **Allowed Origins** nas Advanced Settings do Studio

### Erro: "404 Not Found" ou "405 Method Not Allowed"

**Solução**: Verifique se o servidor está rodando na porta correta (8555) e se os endpoints estão acessíveis:

```bash
# Testar endpoints
curl http://127.0.0.1:8555/assistants
curl -X POST http://127.0.0.1:8555/assistants/search -H "Content-Type: application/json" -d '{"limit": 10}'
```

### Verificar Logs do Servidor

Se ainda não funcionar, verifique os logs do servidor para erros:
- Procure por mensagens de erro no terminal onde o servidor está rodando
- Verifique se há problemas de CORS ou inicialização

## Endpoints Requeridos

O LangSmith Studio precisa dos seguintes endpoints funcionando:

- ✅ `GET /` - Endpoint raiz (descoberta)
- ✅ `POST /assistants/search` - Busca assistentes
- ✅ `GET /assistants` - Lista assistentes
- ✅ `GET /threads` - Lista threads
- ✅ `POST /threads` - Cria thread
- ✅ `OPTIONS /*` - Preflight CORS

## Solução com Tunnel HTTPS (Recomendado)

Para evitar problemas com Chrome 142+ e Mixed Content:

```bash
cd langgraph-app
langgraph dev --port 8555 --tunnel
```

Isso criará um túnel HTTPS automático. Use a URL HTTPS fornecida no Studio.

## Testando a Conexão

Execute o script de teste:

```bash
cd langgraph-app
python test_langsmith_connection.py
```

Ou teste manualmente:

```bash
# Testar CORS preflight
curl -X OPTIONS http://127.0.0.1:8555/assistants \
  -H "Origin: https://smith.langchain.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Testar busca de assistentes
curl -X POST http://127.0.0.1:8555/assistants/search \
  -H "Content-Type: application/json" \
  -H "Origin: https://smith.langchain.com" \
  -d '{"limit": 10}' \
  -v
```

## Referências

- [LangGraph Server Docs](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)
- [LangSmith Studio Docs](https://docs.langchain.com/oss/python/langgraph/studio)
- [Troubleshooting Studio](https://docs.langchain.com/langsmith/troubleshooting-studio)
