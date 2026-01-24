# AlphaAdvisor Frontend

Frontend Next.js para o AlphaAdvisor, deployado no Vercel.

## 🚀 Início Rápido

### Instalação

```bash
npm install
```

### Desenvolvimento

```bash
npm run dev
```

O aplicativo estará disponível em `http://localhost:3000`

### Build

```bash
npm run build
```

### Produção Local

```bash
npm run build
npm start
```

## 📦 Deploy no Vercel

### Pré-requisitos

1. Conta no [Vercel](https://vercel.com)
2. Vercel CLI instalado (opcional, para deploy via CLI)

### Deploy via Dashboard Vercel (Recomendado)

1. **Conecte seu repositório Git:**
   - Acesse [vercel.com](https://vercel.com)
   - Clique em "Add New Project"
   - Conecte seu repositório GitHub/GitLab/Bitbucket
   - Selecione o diretório `frontend`

2. **Configure as variáveis de ambiente:**
   - No dashboard do projeto, vá em Settings > Environment Variables
   - Adicione:
     ```
     API_URL=https://sua-api-url.elasticbeanstalk.com
     ```
   - Ou use `NEXT_PUBLIC_API_URL` se precisar acessar no cliente

3. **Deploy:**
   - O Vercel fará deploy automaticamente após cada push
   - Ou clique em "Deploy" manualmente

### Deploy via CLI

1. **Instalar Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

4. **Deploy de produção:**
   ```bash
   vercel --prod
   ```

### Configuração de Variáveis de Ambiente

No Vercel Dashboard:
- Settings > Environment Variables
- Adicione:
  - `API_URL`: URL da sua API backend
  - `NEXT_PUBLIC_API_URL`: (opcional) Se precisar acessar no cliente

**Importante:** Variáveis que começam com `NEXT_PUBLIC_` são expostas ao cliente. Use apenas para dados não sensíveis.

## 🔧 Configuração

### Variáveis de Ambiente

- `API_URL`: URL da API backend (usado no servidor)
- `NEXT_PUBLIC_API_URL`: URL da API backend (acessível no cliente)

### Estrutura do Projeto

```
frontend/
├── app/
│   ├── layout.tsx      # Layout principal
│   ├── page.tsx         # Página home
│   ├── login/
│   │   └── page.tsx     # Página de login
│   ├── chat/
│   │   └── page.tsx     # Página de chat
│   └── globals.css      # Estilos globais
├── next.config.js       # Configuração Next.js
├── vercel.json          # Configuração Vercel
└── package.json
```

## 📝 Notas

- O frontend usa Next.js 14 com App Router
- TypeScript está configurado
- O projeto está otimizado para Vercel
- CORS deve estar configurado no backend para permitir requisições do domínio Vercel

## 🔄 Atualizações

Após fazer push para o repositório conectado, o Vercel fará deploy automaticamente. Você também pode:

- Fazer deploy manual no dashboard
- Usar `vercel --prod` via CLI
- Configurar preview deployments para branches específicos

## 🐛 Troubleshooting

### Erro de CORS
- Configure CORS no backend para permitir o domínio Vercel
- Exemplo: `https://seu-projeto.vercel.app`

### Variáveis de ambiente não funcionam
- Variáveis devem ser configuradas no Vercel Dashboard
- Use `NEXT_PUBLIC_` prefix para variáveis acessíveis no cliente
- Faça rebuild após alterar variáveis

### Build falha
- Verifique os logs no Vercel Dashboard
- Teste build local: `npm run build`
- Verifique se todas as dependências estão no `package.json`
