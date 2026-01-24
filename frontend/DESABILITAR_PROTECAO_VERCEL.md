# Desabilitar Proteção de Deployment no Vercel

## Problema

O Vercel está retornando 401 "Authentication Required" para todas as requisições porque o "Deployment Protection" está ativado.

## Solução

### Opção 1: Desabilitar via Dashboard (Recomendado)

1. Acesse: https://vercel.com/aiqgen/alphaadvisor/settings/deployment-protection
2. Desabilite "Vercel Authentication" ou configure exceções
3. Salve as alterações

### Opção 2: Configurar Exceções para Rotas de API

1. Acesse: https://vercel.com/aiqgen/alphaadvisor/settings/deployment-protection
2. Em "Deployment Protection Exceptions", adicione:
   - `/api/*` - Para todas as rotas de API
   - `/info` - Para o endpoint /info
3. Salve as alterações

### Opção 3: Usar Protection Bypass Secret (Para Automação)

Se você precisa manter a proteção mas permitir acesso automático:

1. Acesse: https://vercel.com/aiqgen/alphaadvisor/settings/deployment-protection
2. Em "Protection Bypass for Automation", gere um secret
3. Configure como variável de ambiente `VERCEL_AUTOMATION_BYPASS_SECRET` no projeto
4. Use o secret nas requisições automáticas

## Verificação

Após desabilitar a proteção, teste:

```bash
curl -H "Origin: https://smith.langchain.com" https://alphaadvisor-i8noqf1qr-aiqgen.vercel.app/info
```

Deve retornar 200 com headers CORS.
