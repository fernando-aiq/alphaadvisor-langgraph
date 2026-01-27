# Como Conectar LangSmith Studio - Passo a Passo

## Problema: "Connection failed"

O LangSmith Studio precisa de configuração adicional nas **Advanced Settings**.

## Solução Passo a Passo

### 1. No LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. Preencha:
   - **Base URL**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
4. **IMPORTANTE**: Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione:
   ```
   http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com
   ```
   Ou use regex:
   ```
   .*\.elasticbeanstalk\.com
   ```
6. Clique em **Connect**

### 2. Se ainda não funcionar

#### Opção A: Usar HTTPS (Recomendado)

O Studio funciona melhor com HTTPS. Considere:
- Usar um Load Balancer com SSL no Elastic Beanstalk
- Ou usar um túnel HTTPS (ngrok, Cloudflare Tunnel, etc.)

#### Opção B: Verificar CORS

Teste se o CORS está funcionando:

```bash
curl -H "Origin: https://smith.langchain.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/assistants \
     -v
```

Deve retornar headers CORS:
```
Access-Control-Allow-Origin: https://smith.langchain.com
Access-Control-Allow-Methods: GET, POST, ...
```

### 3. Testar Endpoints Manualmente

```bash
# Testar endpoint raiz
curl http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/

# Testar assistants
curl http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/assistants

# Testar threads
curl http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/threads
```

### 4. Verificar Logs do Backend

Se ainda não funcionar, verifique os logs do Elastic Beanstalk:

```bash
eb logs Alphaadvisor-v6-env --region us-east-2
```

Procure por:
- Erros de CORS
- Erros de inicialização do adapter
- Erros de conexão

## Endpoints Disponíveis

- `GET /` - Informações do servidor
- `GET /assistants` - Lista assistentes
- `GET /threads` - Lista threads
- `POST /threads` - Cria thread e executa
- `GET /threads/{id}` - Obtém thread
- `POST /threads/{id}` - Atualiza thread
- `GET /health` - Health check

## Troubleshooting

### Erro: "Origin is not allowed"
→ Adicione a origem em **Allowed Origins** nas Advanced Settings

### Erro: "Connection failed"
→ Verifique se o servidor está rodando e acessível
→ Teste os endpoints manualmente com curl

### Erro: CORS
→ Verifique se `https://smith.langchain.com` está nas origens permitidas
→ Verifique os headers CORS nas respostas
