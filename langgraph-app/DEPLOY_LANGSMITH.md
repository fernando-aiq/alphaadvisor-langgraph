# Deploy via LangSmith - Guia Completo

## Status Atual

✅ Código commitado localmente  
✅ Remote GitHub configurado: `https://github.com/fernando-git-2021/alphaadvisor-langgraph.git`  
✅ Branch: `master`  
✅ langgraph.json configurado corretamente  

## Próximos Passos

### 1. Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. Nome do repositório: `alphaadvisor-langgraph`
3. Visibilidade: **Privado**
4. **NÃO** inicialize com README, .gitignore ou license (já temos tudo)
5. Clique em "Create repository"

### 2. Fazer Push para GitHub

Após criar o repositório, execute:

```bash
git push -u origin master
```

Ou se preferir renomear para `main`:

```bash
git branch -M main
git push -u origin main
```

### 3. Configurar Deployment no LangSmith

1. Acesse: https://smith.langchain.com/
2. Vá em **Deployments** → **New Deployment**
3. Preencha:
   - **Name**: `alphaadvisor-agent` (ou outro nome de sua escolha)
   - **Repository**: Selecione `fernando-git-2021/alphaadvisor-langgraph`
   - **Branch**: `master` (ou `main` se renomeou)
   - **Config File**: `langgraph.json` (deve ser detectado automaticamente)
   - **Deployment Type**: 
     - Development (gratuito) - para testes
     - Production - para produção (requer plano pago)
   - **Shareable**: Marque se quiser compartilhar com outros usuários LangSmith

### 4. Configurar Variáveis de Ambiente

No painel de **Environment Variables** do deployment:

Adicione as seguintes variáveis (todas são secrets):

```
LANGSMITH_API_KEY=lsv2_sua_api_key_aqui
OPENAI_API_KEY=sk-sua_openai_key_aqui
LANGSMITH_PROJECT=alphaadvisor
AI_MODEL=gpt-4o
```

**Como obter as API keys:**

- **LANGSMITH_API_KEY**: 
  - Acesse https://smith.langchain.com/
  - Settings → API Keys
  - Crie ou copie uma API key (começa com `lsv2_...`)

- **OPENAI_API_KEY**:
  - Acesse https://platform.openai.com/api-keys
  - Crie uma nova API key

### 5. Aguardar Deployment

- O deployment inicial pode levar 5-10 minutos
- Monitore os logs no painel do LangSmith
- Você verá o status mudando de "Building" → "Deploying" → "Running"

### 6. Testar o Deployment

Após o deployment estar rodando:

1. **Obter URL do deployment**: Será algo como `https://seu-deployment.langsmith.dev`
2. **Testar endpoint**:
   ```bash
   curl https://seu-deployment.langsmith.dev/health
   ```
3. **Criar thread e enviar mensagem**:
   ```bash
   curl -X POST https://seu-deployment.langsmith.dev/threads \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "messages": [{"role": "user", "content": "Qual é meu perfil de investidor?"}]
       }
     }'
   ```

### 7. Verificar Traces no LangSmith

1. Acesse https://smith.langchain.com/
2. Vá em **Projects** → `alphaadvisor` (ou o nome do seu projeto)
3. Você verá os traces aparecendo em tempo real

## Estrutura do Projeto

- **langgraph.json**: Configuração principal do LangGraph
- **src/agent/graph_chat.py**: Implementação do grafo com ferramentas
- **src/agent/backend_tools.py**: Ferramentas do backend (obter_perfil, obter_carteira, etc)
- **pyproject.toml**: Dependências do projeto
- **requirements.txt**: Dependências alternativas (para compatibilidade)

## Troubleshooting

### Erro: "Git Repository is empty"
- Verifique se o push foi feito corretamente
- Confirme que a branch existe no GitHub
- Verifique se o repositório não está vazio

### Erro: "Config file not found"
- Verifique se `langgraph.json` está na raiz do repositório
- Confirme que o caminho está correto no LangSmith

### Erro: "Failed to build"
- Verifique os logs do deployment
- Confirme que todas as dependências estão em `pyproject.toml` ou `requirements.txt`
- Verifique se as variáveis de ambiente estão configuradas

### Deployment não inicia
- Verifique se todas as variáveis de ambiente obrigatórias estão configuradas
- Confirme que as API keys são válidas
- Verifique os logs para erros específicos

## Atualizações Automáticas

Se você marcou "Automatically update deployment on push to branch":
- Qualquer push para a branch `master` (ou `main`) atualizará automaticamente o deployment
- Isso é útil para desenvolvimento contínuo

## Próximos Passos Após Deployment

1. Integrar com frontend (se necessário)
2. Configurar autoscaling (Production)
3. Monitorar performance e custos
4. Configurar alertas e notificações
