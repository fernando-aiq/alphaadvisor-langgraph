# Correção: API Routes para Proxy do Backend

## 🔍 Problema Identificado

O frontend estava recebendo respostas vazias do Vercel ao tentar fazer requisições para `/api/chat`. O problema era que:

1. **Rewrite do Next.js não funciona no cliente**: O `rewrites()` no `next.config.js` só funciona para requisições server-side (SSR/SSG), não para requisições do cliente (browser).

2. **Requisições do cliente precisam de API Routes**: Quando o código cliente faz uma requisição para `/api/chat`, o navegador faz a requisição diretamente, e o Vercel não consegue fazer o proxy porque o rewrite não se aplica.

## ✅ Solução Implementada

Criadas **API Routes** no Next.js que fazem o proxy para o backend:

1. **`/app/api/chat/route.ts`**: Proxy para `/api/chat` do backend
2. **`/app/api/auth/login/route.ts`**: Proxy para `/api/auth/login` do backend

Essas rotas:
- Executam no servidor (Vercel)
- Têm acesso à variável de ambiente `API_URL`
- Fazem o proxy das requisições para o backend real
- Retornam a resposta ao cliente

## 📋 Configuração Necessária

### 1. Variável de Ambiente no Vercel

Certifique-se de que a variável `API_URL` está configurada no Vercel:

```bash
API_URL=http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com
```

**Como configurar:**
1. Acesse [vercel.com](https://vercel.com) > Seu projeto
2. Settings > Environment Variables
3. Adicione `API_URL` com a URL do backend
4. Faça um redeploy

### 2. Redeploy do Frontend

Após configurar a variável de ambiente, faça um redeploy:

```bash
cd frontend
vercel --prod
```

Ou via Dashboard: Deployments > Redeploy

## 🧪 Teste

Após o redeploy, teste o chat:

1. Acesse o frontend no Vercel
2. Vá para a página de Chat
3. Envie uma mensagem
4. Verifique no console do navegador se a resposta está chegando corretamente

## 📝 Como Funciona Agora

```
Cliente (Browser)
    ↓ POST /api/chat
Next.js API Route (/app/api/chat/route.ts)
    ↓ Proxy para backend
Backend (Elastic Beanstalk)
    ↓ Resposta
Next.js API Route
    ↓ Retorna resposta
Cliente (Browser)
```

## 🔧 Manutenção

Se precisar adicionar novos endpoints:

1. Crie uma nova rota em `frontend/app/api/[endpoint]/route.ts`
2. Use o mesmo padrão de proxy
3. A variável `API_URL` será usada automaticamente

## ⚠️ Nota Importante

- As API Routes executam no servidor, então têm acesso a variáveis de ambiente não públicas
- Não use `NEXT_PUBLIC_*` para `API_URL` - use apenas `API_URL`
- O código cliente continua usando URLs relativas (`/api/chat`), que agora são interceptadas pelas API Routes


