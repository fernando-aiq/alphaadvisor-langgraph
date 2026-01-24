# Guia de Deploy Agent Chat UI no Vercel

## Status Atual

- Código commitado e enviado para GitHub
- Repositório: `fernando-aiq/alphaadvisor-langgraph`
- Branch: `main`
- Arquivos configurados: `vercel.json`, `Stream.tsx` atualizado

## Próximos Passos no Vercel

### 1. Conectar Repositório ao Vercel

1. Acesse: https://vercel.com/
2. Faça login
3. Clique em **"Add New Project"**
4. Selecione o repositório: `fernando-aiq/alphaadvisor-langgraph`
5. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `apps/web`
   - **Build Command**: `cd apps/web && npm run build`
   - **Output Directory**: `apps/web/.next`
   - **Install Command**: `npm install`

### 2. Configurar Variáveis de Ambiente

No painel do projeto Vercel, vá em **Settings** → **Environment Variables** e adicione:

#### Variável 1:
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
- **Environments**: Production, Preview, Development

#### Variável 2:
- **Name**: `NEXT_PUBLIC_ASSISTANT_ID`
- **Value**: `agent`
- **Environments**: Production, Preview, Development

#### Variável 3:
- **Name**: `NEXT_PUBLIC_LANGSMITH_API_KEY`
- **Value**: `[Sua API Key do LangSmith - obtenha em https://smith.langchain.com/]`
- **Environments**: Production, Preview, Development
- **IMPORTANTE**: Não commite esta chave. Configure apenas no Vercel.

### 3. Fazer Deploy

1. Clique em **"Deploy"**
2. Aguarde o build completar (pode levar alguns minutos)
3. Obtenha a URL do deployment

### 4. Testar

Após o deploy:
1. Acesse a URL fornecida pelo Vercel
2. A interface deve carregar automaticamente com as configurações
3. Teste enviando uma mensagem

## Informações do Deployment LangSmith

- **API URL**: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
- **Graph ID**: `agent`
- **Autenticação**: Header `x-api-key`

## Arquivos de Configuração

- `vercel.json` - Configuração do Vercel (já commitado)
- `apps/web/src/providers/Stream.tsx` - Atualizado para usar `x-api-key`
- `DEPLOY_VERCEL.md` - Este guia

## Troubleshooting

### Build Fails
- Verifique se todas as variáveis de ambiente estão configuradas
- Confirme que o Root Directory está correto (`apps/web`)
- Verifique os logs do build no Vercel

### Erro de Conexão
- Verifique se a API URL está correta
- Confirme que a API key está configurada
- Teste a API diretamente: `curl https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app/info`

### Erro de Autenticação
- Verifique se `NEXT_PUBLIC_LANGSMITH_API_KEY` está configurada
- Confirme que o header está sendo enviado corretamente
