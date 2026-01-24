# Guia de Deploy - AlphaAdvisor Frontend (Vercel)

## 🚀 Deploy Rápido no Vercel

### Opção 1: Deploy via Dashboard (Mais Fácil)

1. **Acesse [vercel.com](https://vercel.com)** e faça login

2. **Conecte seu repositório:**
   - Clique em "Add New Project"
   - Conecte GitHub/GitLab/Bitbucket
   - Selecione o repositório do AlphaAdvisor
   - **Importante:** Configure o "Root Directory" como `frontend`

3. **Configure o projeto:**
   - Framework Preset: Next.js (deve detectar automaticamente)
   - Build Command: `npm run build` (padrão)
   - Output Directory: `.next` (padrão)
   - Install Command: `npm install` (padrão)

4. **Configure variáveis de ambiente:**
   - Clique em "Environment Variables"
   - Adicione:
     ```
     API_URL=https://sua-api.elasticbeanstalk.com
     ```
   - Ou se precisar no cliente:
     ```
     NEXT_PUBLIC_API_URL=https://sua-api.elasticbeanstalk.com
     ```

5. **Deploy:**
   - Clique em "Deploy"
   - Aguarde o build completar
   - Seu site estará disponível em `https://seu-projeto.vercel.app`

### Opção 2: Deploy via CLI

1. **Instalar Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Navegar para o diretório frontend:**
   ```bash
   cd frontend
   ```

4. **Deploy:**
   ```bash
   vercel
   ```
   - Responda às perguntas:
     - Set up and deploy? **Y**
     - Which scope? (selecione sua conta)
     - Link to existing project? **N** (primeira vez)
     - Project name? (ou pressione Enter para padrão)
     - Directory? **./** (ou pressione Enter)
     - Override settings? **N**

5. **Deploy de produção:**
   ```bash
   vercel --prod
   ```

## 🔧 Configuração Avançada

### Domínio Customizado

1. No Vercel Dashboard, vá em Settings > Domains
2. Adicione seu domínio
3. Configure DNS conforme instruções
4. Aguarde propagação (pode levar alguns minutos)

### Variáveis de Ambiente por Ambiente

No Vercel Dashboard, você pode configurar variáveis diferentes para:
- Production
- Preview
- Development

### Configuração de Build

O arquivo `vercel.json` já está configurado. Você pode personalizar:

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

### Configurar CORS no Backend

Certifique-se de que o backend permite requisições do domínio Vercel:

```python
# Exemplo para Flask
from flask_cors import CORS

CORS(app, origins=[
    "https://seu-projeto.vercel.app",
    "https://*.vercel.app"  # Para preview deployments
])
```

## 🔄 Deploy Automático

O Vercel faz deploy automático quando você:
- Faz push para a branch `main` (produção)
- Faz push para outras branches (preview)
- Abre um Pull Request (preview)

### Desabilitar Deploy Automático

No Vercel Dashboard:
- Settings > Git
- Desabilite "Automatic deployments"

## 📊 Monitoramento

- **Logs:** Vercel Dashboard > Deployments > [seu deploy] > Logs
- **Analytics:** Vercel Dashboard > Analytics (plano Pro)
- **Real User Monitoring:** Disponível no plano Pro

## 🐛 Troubleshooting

### Build Falha

1. **Verifique os logs:**
   - Vercel Dashboard > Deployments > [deploy falhado] > Logs

2. **Teste localmente:**
   ```bash
   npm run build
   ```

3. **Verifique dependências:**
   - Todas as dependências estão no `package.json`?
   - Versões compatíveis?

### Variáveis de Ambiente Não Funcionam

1. **Verifique se estão configuradas:**
   - Vercel Dashboard > Settings > Environment Variables

2. **Use o prefixo correto:**
   - `NEXT_PUBLIC_` para variáveis acessíveis no cliente
   - Sem prefixo para variáveis apenas no servidor

3. **Faça rebuild:**
   - Variáveis de ambiente requerem novo build

### Erro 404 em Rotas

- Next.js App Router usa a estrutura de pastas
- Certifique-se de que os arquivos estão em `app/[rota]/page.tsx`

### CORS Errors

- Configure CORS no backend
- Adicione o domínio Vercel nas origens permitidas
- Verifique se a API está acessível publicamente

## 📝 Checklist de Deploy

- [ ] Repositório conectado ao Vercel
- [ ] Root Directory configurado como `frontend`
- [ ] Variáveis de ambiente configuradas
- [ ] Build local funciona (`npm run build`)
- [ ] CORS configurado no backend
- [ ] Deploy inicial concluído
- [ ] Site acessível
- [ ] API conectando corretamente
- [ ] Domínio customizado configurado (opcional)

## 🎯 Próximos Passos

Após o deploy:
1. Configure domínio customizado (opcional)
2. Configure analytics (opcional)
3. Configure preview deployments para branches específicas
4. Configure webhooks para notificações




