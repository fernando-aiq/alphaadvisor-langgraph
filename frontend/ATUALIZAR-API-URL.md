# Atualizar URL da API no Frontend

## ✅ O que foi feito

1. **Arquivo `.env.local` atualizado** com a URL do backend:
   - `API_URL=http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
   - `NEXT_PUBLIC_API_URL=http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`

2. **Script criado**: `atualizar-api-url-vercel.bat` para atualizar automaticamente no Vercel

## 🚀 Como atualizar no Vercel

### Opção 1: Via Script (Recomendado)

Execute o script no diretório `frontend`:

```bash
cd frontend
atualizar-api-url-vercel.bat
```

O script irá:
- Verificar se você está logado no Vercel
- Remover variáveis antigas
- Adicionar as novas variáveis para production, preview e development

### Opção 2: Via Dashboard Vercel (Manual)

1. Acesse [vercel.com](https://vercel.com)
2. Vá para o projeto `alphaadvisor`
3. Acesse **Settings** > **Environment Variables**
4. Adicione ou atualize as seguintes variáveis:

   **Para Production:**
   - `API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
   - `NEXT_PUBLIC_API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`

   **Para Preview:**
   - `API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
   - `NEXT_PUBLIC_API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`

   **Para Development:**
   - `API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
   - `NEXT_PUBLIC_API_URL` = `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`

5. Clique em **Save**
6. Faça um redeploy:
   - Via Dashboard: Vá em **Deployments** > Clique nos três pontos do último deploy > **Redeploy**
   - Via CLI: `vercel --prod`

### Opção 3: Via Vercel CLI (Manual)

```bash
# Remover variáveis antigas (se existirem)
vercel env rm API_URL production --yes
vercel env rm NEXT_PUBLIC_API_URL production --yes

# Adicionar novas variáveis
echo "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com" | vercel env add API_URL production
echo "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com" | vercel env add NEXT_PUBLIC_API_URL production

# Repetir para preview e development se necessário
echo "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com" | vercel env add API_URL preview
echo "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com" | vercel env add NEXT_PUBLIC_API_URL preview

# Fazer redeploy
vercel --prod
```

## 📋 Verificação

Após atualizar, verifique se está funcionando:

1. Acesse o frontend no Vercel
2. Abra o console do navegador (F12)
3. Tente fazer login ou usar o chat
4. Verifique se as requisições estão indo para a URL correta do backend

## 🔍 URLs Configuradas

- **Backend (Elastic Beanstalk)**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
- **Região**: `us-east-2` (Ohio)
- **Environment**: `Alphaadvisor-v6-env`

## ⚠️ Nota Importante

Se o backend estiver usando HTTPS, você precisará atualizar a URL para usar `https://` em vez de `http://`. Verifique o status do deploy do backend no AWS Console para confirmar se HTTPS está habilitado.


