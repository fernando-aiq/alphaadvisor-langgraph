# Configuração para Deploy Vercel - Agent Chat UI AlphaAdvisor

## Informações do Deployment

- **Deployment URL**: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
- **Graph ID**: `agent`
- **API Key**: Obtenha em https://smith.langchain.com/ → Settings → API Keys

## Variáveis de Ambiente no Vercel

Configure as seguintes variáveis de ambiente no painel do Vercel:

### Variáveis Obrigatórias:

1. **NEXT_PUBLIC_API_URL**
   - Valor: `https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app`
   - Descrição: URL do deployment LangSmith

2. **NEXT_PUBLIC_ASSISTANT_ID**
   - Valor: `agent`
   - Descrição: ID do grafo (definido no langgraph.json)

### Variáveis Opcionais (mas recomendadas):

3. **NEXT_PUBLIC_LANGSMITH_API_KEY**
   - Valor: `[Sua API Key do LangSmith - obtenha em https://smith.langchain.com/]`
   - Descrição: API key para autenticação no LangSmith Deployment
   - **IMPORTANTE**: Não commite esta chave no código. Configure apenas no Vercel.

## Como Configurar no Vercel

1. Acesse: https://vercel.com/
2. Vá em seu projeto → **Settings** → **Environment Variables**
3. Adicione cada variável acima
4. Marque como **Production**, **Preview** e **Development**
5. Salve e faça redeploy

## Build Settings

- **Framework Preset**: Next.js
- **Root Directory**: `apps/web`
- **Build Command**: `cd apps/web && npm run build`
- **Output Directory**: `apps/web/.next`
- **Install Command**: `npm install`

## Arquivos de Configuração

- `vercel.json` - Configuração do Vercel (já criado)
- `.env.local` - Variáveis locais (não commitado, criar manualmente)
- `.env.example` - Exemplo de variáveis (não commitado)

## Notas

- O arquivo `vercel.json` já está configurado
- As variáveis `NEXT_PUBLIC_*` são expostas ao cliente (browser)
- A API key será usada para autenticação nas requisições
- O SDK do LangGraph (`@langchain/langgraph-sdk`) lida com a autenticação automaticamente

## Teste Local (Opcional)

Para testar localmente antes do deploy:

1. Crie `apps/web/.env.local` com as variáveis acima
2. Execute: `npm run dev` (na raiz do projeto)
3. Acesse: http://localhost:3000
