# Guia de Deploy - AlphaAdvisor Backend (AWS Elastic Beanstalk)

## Pré-requisitos

1. AWS CLI instalado e configurado
2. EB CLI instalado (`pip install awsebcli`)
3. Credenciais AWS configuradas

## Deploy no Elastic Beanstalk

### 1. Inicializar Ambiente EB (Primeira vez)

```bash
cd backend
eb init -p python-3.11 alphaadvisor-backend --region us-east-1
```

### 2. Criar Ambiente (Primeira vez)

```bash
eb create alphaadvisor-env
```

### 3. Fazer Deploy

```bash
eb deploy
```

### 4. Verificar Status

```bash
eb status
```

### 5. Obter URL do Ambiente

```bash
eb status
# Ou
eb open
```

## Atualizar Variável de Ambiente no Vercel

Após obter a URL do backend (ex: `https://alphaadvisor-env.elasticbeanstalk.com`):

```bash
cd frontend
vercel env rm NEXT_PUBLIC_API_URL production
echo "https://sua-url.elasticbeanstalk.com" | vercel env add NEXT_PUBLIC_API_URL production
vercel --prod
```

## Configuração de CORS

O backend já está configurado para aceitar requisições do frontend Vercel. Se necessário, atualize a variável `FRONTEND_URL` no Elastic Beanstalk:

```bash
eb setenv FRONTEND_URL=https://alphaadvisor-1g0eb8d6g-aiqgen.vercel.app
```

## Comandos Úteis

- `eb logs` - Ver logs do ambiente
- `eb health` - Verificar saúde do ambiente
- `eb open` - Abrir URL do ambiente no navegador
- `eb terminate` - Deletar ambiente (cuidado!)




