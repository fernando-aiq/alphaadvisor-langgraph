# Testes Exaustivos do Studio - Guia de Execução

Este documento descreve como executar todos os testes criados para validar o funcionamento completo do Studio integrado.

## 📋 Testes Disponíveis

### 1. Testes de API Routes
**Arquivo:** `test-studio-api-routes.js`

Testa todas as rotas da API `/api/studio/*`:
- `GET /api/studio/threads` - Listar threads
- `POST /api/studio/threads` - Criar thread
- `GET /api/studio/threads/[threadId]/state` - Obter estado
- `GET /api/studio/threads/[threadId]/runs` - Listar runs
- `GET /api/studio/threads/[threadId]/runs/[runId]` - Detalhes do run
- Tratamento de erros
- CORS headers

**Como executar:**
```bash
cd frontend
node test-studio-api-routes.js
```

**Requisitos:**
- Servidor Next.js rodando (`npm run dev`)
- Variáveis de ambiente configuradas

---

### 2. Testes do Cliente LangSmith
**Arquivo:** `test-studio-client.js`

Testa o cliente LangSmith (`langsmith-client.ts`):
- Inicialização do cliente
- Método `listThreads()`
- Método `createThread()`
- Método `getThreadState()`
- Método `listRuns()`
- Método `getRunDetails()`
- Tratamento de erros
- Normalização de respostas

**Como executar:**
```bash
cd frontend
node test-studio-client.js
```

**Requisitos:**
- Servidor Next.js rodando (`npm run dev`)
- Variáveis de ambiente configuradas

---

### 3. Testes de Componentes React
**Arquivo:** `test-studio-components.js`

Valida estrutura e funcionalidades dos componentes:
- Componente `RunsList`
- Componente `RunDetails`
- Cliente LangSmith
- Páginas do Studio
- Integração no Sidebar

**Como executar:**
```bash
cd frontend
node test-studio-components.js
```

**Requisitos:**
- Nenhum (testa apenas estrutura de arquivos)

---

### 4. Teste de Integração Completo
**Arquivo:** `test-studio-integration.js`

Testa o fluxo completo end-to-end:
1. Criar thread via API route
2. Obter estado da thread
3. Criar run
4. Listar runs
5. Obter detalhes do run
6. Verificar comunicação com API de produção

**Como executar:**
```bash
cd frontend
node test-studio-integration.js
```

**Requisitos:**
- Servidor Next.js rodando (`npm run dev`)
- Variáveis de ambiente configuradas
- Conexão com API de produção do LangGraph Deployment

---

### 5. Testes de Navegação e Rotas
**Arquivo:** `test-studio-navigation.js`

Valida todas as rotas e navegação:
- Rotas do frontend (`/studio/*`)
- Rotas da API (`/api/studio/*`)
- Integração no Sidebar
- Biblioteca do cliente
- Estrutura dos componentes

**Como executar:**
```bash
cd frontend
node test-studio-navigation.js
```

**Requisitos:**
- Nenhum (testa apenas estrutura de arquivos)

---

### 6. Teste de Verificação da API de Produção
**Arquivo:** `test-studio-production-api.js`

Testa conexão direta com a API do LangGraph Deployment:
- Conexão com API
- Criar thread
- Obter estado
- Criar run
- Listar runs
- Detalhes do run
- Tratamento de erros
- Endpoints disponíveis

**Como executar:**
```bash
cd frontend
node test-studio-production-api.js
```

**Requisitos:**
- Variáveis de ambiente configuradas
- Conexão com API de produção do LangGraph Deployment

---

### 7. Script Master - Todos os Testes
**Arquivo:** `test-studio-all.js`

Executa todos os testes acima em sequência.

**Como executar:**
```bash
cd frontend
node test-studio-all.js
```

**Requisitos:**
- Servidor Next.js rodando (`npm run dev`)
- Variáveis de ambiente configuradas
- Conexão com API de produção (para alguns testes)

---

## 🔧 Configuração

### Variáveis de Ambiente Necessárias

Certifique-se de ter as seguintes variáveis configuradas em `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app
NEXT_PUBLIC_ASSISTANT_ID=agent
NEXT_PUBLIC_LANGSMITH_API_KEY=sua_chave_aqui
```

### Instalar Dependências

Os testes usam módulos ES6. Certifique-se de que o Node.js suporta ES modules ou use `--experimental-modules`:

```bash
node --experimental-modules test-studio-api-routes.js
```

Ou configure `package.json` para usar ES modules:

```json
{
  "type": "module"
}
```

---

## 📊 Interpretando os Resultados

### ✅ Sucesso Completo
Todos os testes passaram. O Studio está funcionando corretamente.

### ⚠️ Sucesso Parcial
Alguns testes falharam, mas a maioria passou. Verifique os logs para identificar problemas específicos.

### ❌ Falha
Muitos testes falharam. Verifique:
1. Servidor Next.js está rodando?
2. Variáveis de ambiente estão configuradas?
3. API de produção está acessível?
4. Arquivos do Studio existem?

---

## 🐛 Troubleshooting

### Erro: "Cannot find module"
- Certifique-se de estar no diretório `frontend`
- Verifique se os arquivos de teste existem

### Erro: "API_KEY não configurada"
- Configure `NEXT_PUBLIC_LANGSMITH_API_KEY` no `.env.local`
- Reinicie o servidor Next.js após configurar

### Erro: "Connection refused"
- Certifique-se de que o servidor Next.js está rodando (`npm run dev`)
- Verifique se está rodando na porta correta (geralmente 3000)

### Erro: "404 Not Found"
- Verifique se as rotas da API estão criadas corretamente
- Confirme que o servidor Next.js está rodando

---

## 📝 Notas

- Os testes de API routes e cliente requerem o servidor Next.js rodando
- Os testes de componentes e navegação não requerem servidor (testam apenas estrutura)
- O teste de produção cria threads e runs reais na API
- Alguns testes podem falhar se a API não suportar certos endpoints (isso é esperado)

---

## ✅ Checklist de Validação

Após executar todos os testes, verifique:

- [ ] Todas as rotas da API respondem corretamente
- [ ] Cliente LangSmith funciona com todos os métodos
- [ ] Componentes React têm estrutura correta
- [ ] Fluxo de integração completo funciona
- [ ] Rotas e navegação estão configuradas
- [ ] Conexão com API de produção funciona
- [ ] Tratamento de erros está implementado
- [ ] Sidebar tem link para Studio

---

**Última atualização:** Janeiro 2026
