# Instruções Finais - Conectar LangSmith Studio

## ⚠️ IMPORTANTE: Configuração Necessária

O LangSmith Studio **REQUER** que você adicione a origem nas **Advanced Settings** antes de conectar.

## Passo a Passo Completo

### 1. Aguardar Deploy Finalizar

O deploy está em andamento. Aguarde até o status ser "Ready":
```bash
aws elasticbeanstalk describe-environments --environment-names Alphaadvisor-v6-env --region us-east-2 --query Environments[0].[Status,Health,VersionLabel] --output table
```

### 2. No LangSmith Studio

1. Acesse: https://smith.langchain.com/
2. Vá em **Studio** > **Connect Studio to local agent**
3. Preencha:
   - **Base URL**: `http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
4. **CRÍTICO**: Clique em **Advanced Settings**
5. Em **Allowed Origins**, adicione EXATAMENTE:
   ```
   http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com
   ```
   **OU** use regex para permitir todos os Elastic Beanstalk:
   ```
   .*\.elasticbeanstalk\.com
   ```
6. Clique em **Connect**

### 3. O Que Foi Implementado

✅ Endpoints na raiz (`/assistants`, `/threads`)
✅ Endpoint `/assistants/search` (POST) - formato LangGraph Server
✅ Suporte a OPTIONS (preflight CORS)
✅ Endpoint `/docs` para OpenAPI
✅ Formato completo de resposta com timestamps, version, etc.
✅ CORS configurado para LangSmith Studio

### 4. Endpoints Disponíveis

- `GET /` - Informações do servidor
- `GET /assistants` - Lista assistentes
- `POST /assistants/search` - Busca assistentes (formato LangGraph Server)
- `GET /threads` - Lista threads
- `POST /threads` - Cria thread e executa
- `GET /threads/{id}` - Obtém thread
- `POST /threads/{id}` - Atualiza thread
- `GET /docs` - Documentação OpenAPI
- `GET /health` - Health check

### 5. Se Ainda Não Funcionar

#### Verificar se o servidor está acessível:
```bash
curl http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/assistants
```

#### Verificar CORS:
```bash
curl -H "Origin: https://smith.langchain.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com/assistants \
     -v
```

Deve retornar:
```
Access-Control-Allow-Origin: https://smith.langchain.com
```

#### Verificar logs:
```bash
eb logs Alphaadvisor-v6-env --region us-east-2
```

## Problema Comum: HTTP vs HTTPS

O Studio funciona melhor com HTTPS. Se continuar falhando, considere:
- Configurar SSL no Elastic Beanstalk (Load Balancer)
- Ou usar um túnel HTTPS (ngrok, Cloudflare Tunnel)

## Formato de Resposta Esperado

O Studio espera que `/assistants` retorne:
```json
{
  "assistants": [
    {
      "assistant_id": "agent",
      "graph_id": "agent",
      "name": "AlphaAdvisor Agent",
      "version": 1,
      "created_at": "2026-01-21T19:30:00.000Z",
      "updated_at": "2026-01-21T19:30:00.000Z",
      "metadata": {},
      "config": {
        "configurable": {}
      }
    }
  ]
}
```

E `/assistants/search` (POST) retorna array direto:
```json
[
  {
    "assistant_id": "agent",
    ...
  }
]
```

## Status do Deploy

Versão atual: `app-20260121_143027`
Status: Aguardando finalizar (Updating → Ready)
