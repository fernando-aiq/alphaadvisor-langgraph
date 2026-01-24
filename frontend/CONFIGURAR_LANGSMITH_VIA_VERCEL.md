# Configurar LangSmith Studio via Proxy Vercel

## Solução Implementada

Foi criado um proxy HTTPS no Vercel que faz forward para o backend HTTP do Elastic Beanstalk. Isso resolve o problema de Mixed Content porque:

- LangSmith Studio (HTTPS) → Vercel Proxy (HTTPS) → Backend HTTP (interno)
- O navegador só vê HTTPS, então não há bloqueio de Mixed Content

## Como Usar

### 1. Fazer Deploy do Frontend

Certifique-se de que o frontend está deployado no Vercel com a nova rota de proxy:

```bash
cd frontend
vercel --prod
```

### 2. Obter URL do Vercel

A URL do seu projeto Vercel será algo como:
- `https://alphaadvisor.vercel.app`
- Ou `https://alphaadvisor-xxxxx.vercel.app`

### 3. Configurar no LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. **Base URL**: `https://seu-projeto.vercel.app/api/langgraph`
   - Exemplo: `https://alphaadvisor.vercel.app/api/langgraph`
4. Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione:
   ```
   https://seu-projeto.vercel.app
   ```
   - Exemplo: `https://alphaadvisor.vercel.app`
6. Clique em **Connect**

## Endpoints Disponíveis via Proxy

Todos os endpoints do LangGraph Server estão disponíveis via proxy:

- `GET /api/langgraph/info` → Informações do servidor (descoberta)
- `GET /api/info` → Proxy alternativo para /info
- `GET /info` → Redirecionado para /api/info (via rewrite)
- `GET /api/langgraph/health` → Health check
- `GET /api/langgraph/assistants` → Lista assistentes
- `POST /api/langgraph/assistants/search` → Busca assistentes
- `GET /api/langgraph/threads` → Lista threads
- `POST /api/langgraph/threads` → Cria thread
- `GET /api/langgraph/threads/{id}` → Obtém thread
- `POST /api/langgraph/threads/{id}` → Atualiza thread
- etc.

**IMPORTANTE**: Use `https://seu-projeto.vercel.app/api/langgraph` como Base URL no LangSmith Studio.

## Testar Proxy

Para testar se o proxy está funcionando:

```bash
# Testar health check
curl https://seu-projeto.vercel.app/api/langgraph/health

# Testar busca de assistentes
curl -X POST https://seu-projeto.vercel.app/api/langgraph/assistants/search \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Ou use o script de teste:

```bash
cd frontend
npx tsx test_langgraph_proxy.ts
```

## Vantagens

- ✅ Não requer configuração de SSL no Elastic Beanstalk
- ✅ Vercel já tem HTTPS por padrão
- ✅ Solução rápida e sem custos adicionais
- ✅ Funciona imediatamente após deploy
- ✅ Todos os endpoints do LangGraph Server disponíveis

## Troubleshooting

### Erro: "Connection failed"

1. Verifique se o frontend está deployado no Vercel
2. Verifique se a URL do Vercel está correta
3. Teste o endpoint diretamente: `curl https://seu-projeto.vercel.app/api/langgraph/health`

### Erro: "Origin is not allowed"

1. Adicione a origem completa do Vercel em Allowed Origins
2. Certifique-se de usar `https://` (não `http://`)

### Erro: 500 Internal Server Error

1. Verifique os logs do Vercel: `vercel logs`
2. Verifique se a variável `API_URL` está configurada no Vercel
3. Verifique se o backend está acessível

### Erro: CORS ou 401 em /info

Se o LangSmith Studio tentar acessar `/info` na raiz e receber erro:
1. Certifique-se de que a **Base URL** está configurada como `/api/langgraph` (não apenas a raiz)
2. O endpoint `/info` está disponível em `/api/langgraph/info`
3. Há também um proxy em `/api/info` e um rewrite de `/info` para `/api/info`
