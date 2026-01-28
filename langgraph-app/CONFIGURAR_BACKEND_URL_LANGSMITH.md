# Configurar BACKEND_URL para o agente usar as regras do S3

O agente consulta o backend (e as regras salvas na página Autonomia / S3) quando tem uma URL do backend. A URL pode vir de **config**, da variável de ambiente **BACKEND_URL** ou do **fallback em código** (`DEFAULT_BACKEND_URL`). Sem nenhuma delas, ele usaria as 4 regras padrão; com o fallback, o agente usa por padrão o backend AlphaAdvisor (EB).

## Fallback em código (DEFAULT_BACKEND_URL)

No módulo `config_tools.py` existe uma constante **`DEFAULT_BACKEND_URL`** com a URL do backend no Elastic Beanstalk. Ela é usada quando **nem** `config.configurable.backend_url` **nem** a variável de ambiente `BACKEND_URL` estão definidos (por exemplo no LangGraph Cloud, onde a env do deployment pode não chegar ao grafo). Assim, o agente passa a consultar sempre o backend conhecido e a listar as regras atuais (S3/Autonomia) no classificador de handoff.

Para usar **outro** backend em vez do padrão, defina `BACKEND_URL` no deployment ou passe `backend_url` no config ao invocar o grafo. Se o backend mudar de domínio, atualize `DEFAULT_BACKEND_URL` em `config_tools.py` ou configure `BACKEND_URL` no deployment.

## Onde configurar (opcional)

### 1. LangSmith Cloud (Studio / Deployments)

Se o agente roda no **LangSmith** (Studio, Deployments):

1. Acesse [LangSmith](https://smith.langchain.com) → **Deployments** → seu deployment (ex.: **agent**).
2. Abra **Settings** / **Environment variables** (ou **Configuration**).
3. Adicione:
   - **Nome:** `BACKEND_URL`
   - **Valor:** URL base do backend Flask (sem barra no final), ex.:
     - `https://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com`
     - ou `https://seu-backend.onrender.com`
4. Salve e **redeploy** o agente (ou reinicie o deployment) para a variável passar a valer.

Assim, em todo run o agente chama `GET {BACKEND_URL}/api/configuracoes/regras_redirecionamento?user_id=default` e usa as regras que estão no backend (S3 ou memória).

### 2. Servidor próprio (langgraph-app no EB ou local)

Se o agente roda no **langgraph-app** (Elastic Beanstalk ou `application.py` local):

- Defina a variável de ambiente **BACKEND_URL** no ambiente onde o processo roda:
  - **EB:** Environment properties do Elastic Beanstalk (backend Flask, não o langgraph-app).
  - **Local:** no `.env` em `langgraph-app/.env` ou no terminal antes de subir o servidor.

Exemplo em `langgraph-app/.env`:

```
BACKEND_URL=https://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com
```

O `application.py` já injeta `backend_url` no config quando `BACKEND_URL` está definida, e o grafo usa isso em `should_continue` e `handoff_node`.

### 3. Via config ao invocar o grafo

Quem invoca o grafo pode passar a URL no config:

```python
graph.invoke(
    {"messages": [...]},
    config={"configurable": {"backend_url": "https://seu-backend.com", "user_id": "default"}}
)
```

Isso tem prioridade sobre a variável de ambiente dentro daquela invocação.

## Como conferir

- Nos logs do run (LangSmith: Run → logs / stderr), procure por:
  - `[RegrasHandoff] GET https://...` → está tentando consultar o backend.
  - `[RegrasHandoff] Backend OK status=200 regras_count=N` → backend respondeu e retornou N regras.
  - `[RegrasHandoff] Backend error status=...` → backend respondeu com erro (403, 404, 500).
  - `[RegrasHandoff] Exception: ...` → falha de rede (timeout, conexão recusada, etc.).
  - `[RegrasHandoff] BACKEND_URL nao definida` → variável não chegou ao grafo (reconfira no deployment).
- No trace do **should_continue**, o prompt do classificador deve listar as regras que vieram do backend (as da Autonomia/S3), não só as 4 padrão.

## Já tenho BACKEND_URL no deployment e ainda vejo as 4 regras

1. **Confira nos logs** qual mensagem aparece: `Backend error`, `Exception` ou `BACKEND_URL nao definida`.
2. **URL acessível**: O backend precisa ser acessível pela internet (LangSmith roda na nuvem). Use `https://` e uma URL pública (ex.: Elastic Beanstalk, Render). `http://localhost` não funciona no deployment.
3. **CORS**: O endpoint `/api/configuracoes/regras_redirecionamento` é GET e não exige auth; se o backend bloquear por CORS em requisições server-side, pode falhar. Garanta que o backend aceite GET sem Origin restritivo ou que a URL esteja na lista de origens permitidas.
4. **Redeploy**: Depois de alterar variáveis de ambiente no deployment, faça redeploy (ou reinicie) para o processo passar a ver a nova env.
5. **Teste manual**: De outra máquina ou Postman, chame `GET {BACKEND_URL}/api/configuracoes/regras_redirecionamento?user_id=default` e confira se retorna JSON com `regras_redirecionamento` (array).
