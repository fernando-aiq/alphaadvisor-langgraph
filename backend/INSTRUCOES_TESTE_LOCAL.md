# Instruções: Testar LangGraph Server Localmente

## Status Atual

✅ Servidor está rodando em `http://127.0.0.1:8000`
✅ Endpoints principais funcionando:
- GET /assistants - OK
- POST /assistants/search - OK
- GET /threads - OK
- GET /health - OK
- GET /docs - OK
- CORS configurado corretamente

## Como Testar

### 1. Servidor Local (Já Rodando)

O servidor está rodando em background. Para verificar:
```bash
curl http://127.0.0.1:8000/api/health
```

### 2. Testar Endpoints

Execute o script de teste completo:
```bash
cd backend
python test_local_studio.py
```

### 3. Conectar LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. Use a Base URL: `http://127.0.0.1:8000`
4. **IMPORTANTE**: Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione:
   ```
   http://127.0.0.1:8000
   http://localhost:8000
   ```
6. Clique em **Connect**

### 4. Se Der Erro no Chrome

Chrome 142+ pode bloquear conexões HTTP de sites HTTPS. Soluções:

**Opção A: Usar http://127.0.0.1:8000** (recomendado)
- Funciona melhor que localhost

**Opção B: Desabilitar PNA no Chrome**
1. Acesse: `chrome://flags/#block-insecure-private-network-requests`
2. Desabilite "Block insecure private network requests"
3. Reinicie o Chrome

**Opção C: Usar túnel HTTPS**
```bash
# Instalar ngrok: https://ngrok.com/download
ngrok http 8000

# Usar a URL HTTPS do ngrok no Studio
```

## Endpoints Disponíveis Localmente

- `GET http://127.0.0.1:8000/assistants` - Lista assistentes
- `POST http://127.0.0.1:8000/assistants/search` - Busca assistentes
- `GET http://127.0.0.1:8000/threads` - Lista threads
- `POST http://127.0.0.1:8000/threads` - Cria thread
- `GET http://127.0.0.1:8000/health` - Health check
- `GET http://127.0.0.1:8000/docs` - Documentação OpenAPI

## Verificar Logs

Se houver problemas, verifique os logs do servidor. O servidor está rodando em background e os logs devem aparecer no terminal onde foi iniciado.

## Próximos Passos

Após validar localmente:
1. Se tudo funcionar, fazer deploy no Elastic Beanstalk
2. Configurar HTTPS no Elastic Beanstalk (recomendado)
3. Conectar Studio ao endpoint HTTPS do Elastic Beanstalk
