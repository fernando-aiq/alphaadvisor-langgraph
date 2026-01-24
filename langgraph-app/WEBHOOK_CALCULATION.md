# Webhook para Cálculos Determinísticos

## Visão Geral

Quando um cálculo determinístico é executado (ex: "8 por 7"), o sistema pode disparar um webhook para notificar sistemas externos. Isso permite:

- Registrar cálculos em banco de dados
- Enviar notificações
- Integrar com sistemas de analytics
- Auditoria de operações
- Etc.

## Configuração

### 1. Variáveis de Ambiente

No arquivo `.env` do `langgraph-app`, adicione:

```env
# URL do webhook para cálculos
CALCULATION_WEBHOOK_URL=http://localhost:8888/webhook/calculation

# Opcional: habilitar debug (mostra logs do webhook)
DEBUG_CALCULATION_WEBHOOK=true
```

### 2. Formato do Payload

O webhook recebe um POST com o seguinte JSON:

```json
{
  "event": "calculation_executed",
  "timestamp": "2026-01-22T19:30:45.123456Z",
  "data": {
    "num1": 8.0,
    "operator": "*",
    "num2": 7.0,
    "result": 56.0,
    "user_message": "8 por 7",
    "expression": "8.0 * 7.0 = 56.0"
  }
}
```

### 3. Campos do Payload

- **event**: Sempre `"calculation_executed"`
- **timestamp**: Timestamp UTC em formato ISO
- **data.num1**: Primeiro número do cálculo
- **data.operator**: Operador (`*`, `+`, `-`, `/`)
- **data.num2**: Segundo número do cálculo
- **data.result**: Resultado do cálculo
- **data.user_message**: Mensagem original do usuário
- **data.expression**: Expressão formatada

## Servidor Webhook Sample

Um servidor de exemplo está disponível em `webhook_sample_server.py`.

### Executar o Servidor Sample

```bash
cd langgraph-app
python webhook_sample_server.py
```

O servidor ficará escutando em `http://localhost:8888`

### Endpoints do Servidor Sample

- **POST** `/webhook/calculation` - Recebe webhooks de cálculos
- **GET** `/webhook/calculation/history` - Visualiza histórico de cálculos recebidos
- **POST** `/webhook/calculation/clear` - Limpa histórico (útil para testes)
- **GET** `/health` - Health check

### Testar o Webhook

1. **Iniciar servidor sample:**
   ```bash
   python webhook_sample_server.py
   ```

2. **Configurar .env:**
   ```env
   CALCULATION_WEBHOOK_URL=http://localhost:8888/webhook/calculation
   DEBUG_CALCULATION_WEBHOOK=true
   ```

3. **Iniciar LangGraph Server:**
   ```bash
   langgraph dev --port 8222
   ```

4. **Enviar cálculo:**
   - Via LangGraph Studio ou API
   - Mensagem: "8 por 7"
   - O webhook será disparado automaticamente

5. **Verificar histórico:**
   ```bash
   curl http://localhost:8888/webhook/calculation/history
   ```

## Implementação Customizada

### Exemplo: Salvar em Banco de Dados

```python
def _save_calculation_to_db(num1, operator, num2, result, user_message):
    """Salva cálculo em banco de dados"""
    # Sua implementação aqui
    pass
```

### Exemplo: Enviar Email

```python
def _send_calculation_notification(num1, operator, num2, result):
    """Envia notificação por email"""
    # Sua implementação aqui
    pass
```

### Modificar `_trigger_calculation_webhook`

Você pode estender a função `_trigger_calculation_webhook` em `graph_chat.py` para adicionar outras ações:

```python
def _trigger_calculation_webhook(...):
    # Webhook existente
    _send_webhook_request(...)
    
    # Adicionar outras ações
    _save_calculation_to_db(...)
    _send_calculation_notification(...)
    # etc.
```

## Características

- **Não bloqueante**: Webhook executa em thread separada
- **Não quebra o fluxo**: Erros no webhook não afetam a resposta ao usuário
- **Configurável**: Ativado apenas se `CALCULATION_WEBHOOK_URL` estiver configurado
- **Timeout**: Requisições têm timeout de 5 segundos
- **Debug**: Logs opcionais via `DEBUG_CALCULATION_WEBHOOK`

## Troubleshooting

### Webhook não está sendo disparado

1. Verifique se `CALCULATION_WEBHOOK_URL` está configurado no `.env`
2. Verifique se o servidor webhook está rodando e acessível
3. Habilite debug: `DEBUG_CALCULATION_WEBHOOK=true`

### Erro: "requests não instalado"

Instale a biblioteca:
```bash
pip install requests
```

### Webhook está lento

O webhook executa em background e não bloqueia a resposta. Se o servidor webhook estiver lento, isso não afeta o usuário.

## Segurança

- Em produção, use HTTPS para o webhook
- Considere adicionar autenticação (API key, JWT, etc.)
- Valide e sanitize dados recebidos no webhook
- Implemente rate limiting se necessário

## Exemplo de Webhook com Autenticação

```python
def _send_webhook():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('WEBHOOK_API_KEY')}"
    }
    response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
```
