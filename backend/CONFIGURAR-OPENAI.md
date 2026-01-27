# Configurar Chave da OpenAI no Elastic Beanstalk

## 🔑 Como Configurar

### Opção 1: Via Script (Recomendado)

Execute o script com sua chave da OpenAI:

```bash
cd backend
configurar-openai-key.bat sk-proj-SUA_CHAVE_AQUI
```

**Importante:** Não inclua aspas na chave!

### Opção 2: Via AWS Console

1. Acesse o [AWS Console](https://console.aws.amazon.com/elasticbeanstalk)
2. Vá para **Elastic Beanstalk** > **Environments** > **Alphaadvisor-v6-env**
3. Clique em **Configuration**
4. Role até **Software** e clique em **Edit**
5. Em **Environment properties**, adicione:
   - **OPENAI_API_KEY** = `sua-chave-aqui`
   - **AI_MODEL** = `gpt-4o`
6. Clique em **Apply**
7. Aguarde o environment atualizar (pode levar alguns minutos)

### Opção 3: Via AWS CLI

```bash
aws elasticbeanstalk update-environment \
    --environment-name Alphaadvisor-v6-env \
    --region us-east-2 \
    --option-settings \
        Namespace=aws:elasticbeanstalk:application:environment,OptionName=OPENAI_API_KEY,Value=sk-proj-SUA_CHAVE_AQUI \
        Namespace=aws:elasticbeanstalk:application:environment,OptionName=AI_MODEL,Value=gpt-4o
```

## ✅ Verificação

Após configurar, verifique se a variável foi aplicada:

```bash
aws elasticbeanstalk describe-configuration-settings \
    --application-name alphaadvisor-v6 \
    --environment-name Alphaadvisor-v6-env \
    --region us-east-2 \
    --query 'ConfigurationSettings[0].OptionSettings[?OptionName==`OPENAI_API_KEY`]' \
    --output table
```

## 🔍 Como Obter sua Chave da OpenAI

1. Acesse [platform.openai.com](https://platform.openai.com)
2. Faça login na sua conta
3. Vá em **API keys**
4. Clique em **Create new secret key**
5. Copie a chave (ela só será mostrada uma vez!)

## ⚠️ Segurança

- **NUNCA** commite a chave da OpenAI no Git
- A chave será armazenada de forma segura no Elastic Beanstalk
- Apenas o environment terá acesso à chave

## 📋 Após Configurar

Após configurar a chave:

1. O environment será atualizado automaticamente
2. Aguarde 2-5 minutos para o deploy completar
3. Teste o chat novamente - agora deve usar a API da OpenAI real!

## 🧪 Teste

Após configurar, teste com:

```bash
python testar-backend-v6.py
```

Ou teste diretamente no frontend - as respostas devem ser dinâmicas e não mais pré-determinadas!

