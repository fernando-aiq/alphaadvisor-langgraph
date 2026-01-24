# Deploy Agent Chat UI no Vercel - Instruções Finais

## Status Atual

- Código commitado e enviado para GitHub
- Repositório: `fernando-aiq/alphaadvisor-langgraph`
- Branch: `main`
- Arquivos configurados:
  - `vercel.json` - Configuração do Vercel
  - `apps/web/src/providers/Stream.tsx` - Atualizado para usar `x-api-key`
  - `DEPLOY_VERCEL.md` - Documentação

## Passo a Passo no Vercel

### 1. Conectar Repositório

1. Acesse: **https://vercel.com/**
2. Faça login na sua conta
3. Clique em **"Add New Project"** ou **"Import Project"**
4. Selecione o repositório: **`fernando-aiq/alphaadvisor-langgraph`**
5. Clique em **"Import"**

### 2. Configurar Build Settings

No painel de configuração do projeto:

- **Framework Preset**: `Next.js` (deve ser detectado automaticamente)
- **Root Directory**: `apps/web` ⚠️ **IMPORTANTE**
- **Build Command**: `cd apps/web && npm run build` (ou deixe padrão)
- **Output Directory**: `apps/web/.next` (ou deixe padrão)
- **Install Command**: `npm install` (ou deixe padrão)

**OU** use o arquivo `vercel.json` que já está configurado (o Vercel deve detectar automaticamente).

### 3. Configurar Variáveis de Ambiente

**ANTES de fazer o deploy**, configure as variáveis de ambiente:

1. No painel do projeto, vá em **Settings** → **Environment Variables**
2. Clique em **"Add New"** para cada variável:

#### Variável 1: NEXT_PUBLIC_API_URL
- **Key**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
- **Environments**: Marque todas (Production, Preview, Development)

#### Variável 2: NEXT_PUBLIC_ASSISTANT_ID
- **Key**: `NEXT_PUBLIC_ASSISTANT_ID`
- **Value**: `agent`
- **Environments**: Marque todas (Production, Preview, Development)

#### Variável 3: NEXT_PUBLIC_LANGSMITH_API_KEY
- **Key**: `NEXT_PUBLIC_LANGSMITH_API_KEY`
- **Value**: `[Sua API Key do LangSmith - obtenha em https://smith.langchain.com/ → Settings → API Keys]`
- **Environments**: Marque todas (Production, Preview, Development)
- **IMPORTANTE**: Não commite esta chave no código. Configure apenas no Vercel.

3. Clique em **"Save"** para cada variável

### 4. Fazer Deploy

1. Após configurar as variáveis, volte para a aba **"Deployments"**
2. Clique em **"Deploy"** (ou aguarde o deploy automático se configurou auto-deploy)
3. Aguarde o build completar (pode levar 2-5 minutos)
4. Quando concluir, você verá a URL do deployment (ex: `https://seu-projeto.vercel.app`)

### 5. Testar

1. Acesse a URL fornecida pelo Vercel
2. A interface do Agent Chat UI deve carregar
3. Como as variáveis estão configuradas, a interface deve conectar automaticamente
4. Teste enviando uma mensagem como: "Qual é meu perfil de investidor?"

## Informações Importantes

### Deployment LangSmith
- **URL**: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
- **Graph ID**: `agent`
- **Autenticação**: Header `x-api-key`

### Estrutura do Projeto
- O Agent Chat UI está em `alphaadvisor-chat-ui/apps/web/`
- O `vercel.json` na raiz aponta para `apps/web` como root directory

## Troubleshooting

### Build Fails
- Verifique se o **Root Directory** está configurado como `apps/web`
- Confirme que todas as variáveis de ambiente estão configuradas
- Verifique os logs do build no Vercel para erros específicos

### Erro de Conexão na Interface
- Verifique se `NEXT_PUBLIC_API_URL` está correta
- Confirme que `NEXT_PUBLIC_ASSISTANT_ID` é `agent`
- Teste a API diretamente: `curl https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app/info`

### Interface não Conecta
- Verifique se `NEXT_PUBLIC_LANGSMITH_API_KEY` está configurada
- Confirme que a API key é válida
- Verifique o console do navegador para erros

## Próximos Passos Após Deploy

1. Obter URL pública do Vercel
2. Testar interface completa
3. Compartilhar URL com usuários
4. Configurar domínio customizado (opcional)
5. Monitorar uso e performance

## Arquivos de Referência

- `alphaadvisor-chat-ui/DEPLOY_VERCEL.md` - Documentação detalhada
- `alphaadvisor-chat-ui/vercel.json` - Configuração do Vercel
- `alphaadvisor-chat-ui/apps/web/src/providers/Stream.tsx` - Código de conexão

Tudo pronto para deploy! 🚀
