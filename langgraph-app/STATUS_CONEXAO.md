# Status da Conexão - LangSmith Studio

## ✅ Servidor Rodando

**URL**: `http://127.0.0.1:8555`

**Status**: Servidor LangGraph iniciado com sucesso na porta 8555

## Testes Realizados

### ✅ Endpoints Funcionando

- **POST /assistants/search** - ✅ Status 200 (CRÍTICO - usado pelo Studio)
- **GET /** - ✅ Status 200 (Endpoint raiz)
- **GET /docs** - ✅ Status 200 (Documentação OpenAPI)
- **OPTIONS /assistants** - ✅ Status 200 (CORS preflight)

### ⚠️ Endpoints Não Disponíveis (Normal)

- **GET /assistants** - Status 405 (não exposto pelo LangGraph Server padrão)
- **GET /threads** - Status 405 (não exposto pelo LangGraph Server padrão)

**Nota**: Estes endpoints não são necessários. O LangSmith Studio usa principalmente `POST /assistants/search`.

## CORS Configurado

- **Access-Control-Allow-Origin**: `*` (permite todas as origens)
- **Access-Control-Allow-Methods**: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
- **CORS Preflight**: Funcionando corretamente

## Conectar no LangSmith Studio

### Passo a Passo

1. **Acesse**: https://smith.langchain.com/
2. **Vá em**: Studio > Connect Studio to local agent
3. **Base URL**: `http://127.0.0.1:8555`
4. **Advanced Settings** > **Allowed Origins**, adicione:
   ```
   http://127.0.0.1:8555
   http://localhost:8555
   ```
5. **Clique em**: Connect

### Se Der Erro no Chrome

Chrome 142+ pode bloquear conexões HTTP de sites HTTPS. Soluções:

1. **Usar 127.0.0.1** (recomendado):
   - Base URL: `http://127.0.0.1:8555`

2. **Usar tunnel HTTPS**:
   ```bash
   cd langgraph-app
   ./start-local-tunnel.bat  # Windows
   # ou
   ./start-local-tunnel.sh   # Linux/Mac
   ```
   - Use a URL HTTPS fornecida pelo tunnel

3. **Desabilitar PNA no Chrome**:
   - Acesse: `chrome://flags/#block-insecure-private-network-requests`
   - Desabilite e reinicie

## Testar Conexão

Execute os scripts de teste:

```bash
# Teste completo
python test_langsmith_connection.py

# Diagnóstico detalhado
python diagnose_connection.py

# Teste específico da porta
python test_port_8555.py
```

## Resultado Esperado

Após conectar no Studio:
- ✅ Studio deve listar o assistente "agent"
- ✅ Deve ser possível criar threads
- ✅ Deve ser possível enviar mensagens
- ✅ Traces devem aparecer no LangSmith

## Troubleshooting

### Erro: "Connection failed"

1. Verifique se o servidor está rodando:
   ```bash
   curl http://127.0.0.1:8555/
   ```

2. Verifique Allowed Origins no Studio:
   - Deve ter `http://127.0.0.1:8555` (URL completa)

3. Abra o Console do navegador (F12):
   - Verifique erros na aba Console
   - Verifique requisições na aba Network

### Erro: "Origin is not allowed"

- Adicione a origem em **Allowed Origins** nas Advanced Settings

## Comandos Úteis

```bash
# Iniciar servidor
cd langgraph-app
langgraph dev --port 8555

# Iniciar com tunnel HTTPS
langgraph dev --port 8555 --tunnel

# Testar endpoints
curl http://127.0.0.1:8555/
curl -X POST http://127.0.0.1:8555/assistants/search -H "Content-Type: application/json" -d '{"limit": 10}'
```
