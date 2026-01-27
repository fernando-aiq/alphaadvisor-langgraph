# Conectar LangSmith Studio - Porta 8123

## ✅ Servidor Rodando

O LangGraph Server está rodando na porta **8123** (servidor padrão do `langgraph-app`).

## Configuração no LangSmith Studio

### 1. Base URL
```
http://127.0.0.1:8123
```

### 2. Advanced Settings > Allowed Origins

Adicione EXATAMENTE estas URLs completas:

```
http://127.0.0.1:8123
http://localhost:8123
```

**IMPORTANTE**: 
- ❌ NÃO use apenas `localhost` ou `127.0.0.1` sem porta
- ❌ NÃO use `localhost:8123` sem o protocolo `http://`
- ✅ USE as URLs completas: `http://127.0.0.1:8123`

### 3. Passo a Passo

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. **Base URL**: `http://127.0.0.1:8123`
4. Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione:
   ```
   http://127.0.0.1:8123
   http://localhost:8123
   ```
6. Clique em **Connect**

## Endpoints Disponíveis

O servidor na porta 8123 expõe os seguintes endpoints:

- `GET /` - Informações do servidor
- `POST /assistants/search` - Busca assistentes ✅
- `GET /threads` - Lista threads
- `POST /threads` - Cria thread e executa
- `GET /threads/{id}` - Obtém thread
- `POST /threads/{id}` - Atualiza thread

## Verificação

Para verificar se o servidor está funcionando:

```bash
# Testar endpoint raiz
curl http://127.0.0.1:8123/

# Testar busca de assistentes
curl -X POST http://127.0.0.1:8123/assistants/search \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

## Troubleshooting

### Erro: "Connection failed"

1. **Verifique se o servidor está rodando**:
   ```bash
   curl http://127.0.0.1:8123/
   ```

2. **Verifique Allowed Origins**:
   - Deve ter `http://127.0.0.1:8123` (com protocolo e porta)
   - Não apenas `localhost` ou `127.0.0.1`

3. **Abra o Console do Navegador** (F12):
   - Verifique erros na aba Console
   - Verifique requisições na aba Network

4. **Chrome bloqueando HTTP**:
   - Tente desabilitar: `chrome://flags/#block-insecure-private-network-requests`
   - Ou use `http://127.0.0.1:8123` em vez de `http://localhost:8123`

### Servidor não está rodando

Para iniciar o servidor LangGraph:

```bash
cd langgraph-app
langgraph dev
```

Ou use os scripts:
- Windows: `start-local.bat`
- Linux/Mac: `./start-local.sh`
