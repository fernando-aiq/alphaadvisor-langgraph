import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

/**
 * Rota de teste para diagnosticar problemas com a API do LangSmith
 * GET /api/test-langsmith
 */
export async function GET(request: NextRequest) {
  const apiKey = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY?.trim() || ''
  const projectName = process.env.NEXT_PUBLIC_LANGSMITH_PROJECT_NAME?.trim() || ''
  
  const results: any[] = []
  
  // Teste 1: Verificar se a API key existe
  results.push({
    test: 'API Key Check',
    apiKeyExists: !!apiKey,
    apiKeyLength: apiKey.length,
    apiKeyPrefix: apiKey.substring(0, 10) + '...',
    projectName,
  })
  
  if (!apiKey) {
    return NextResponse.json({ error: 'API Key não configurada', results })
  }
  
  // Teste 2: Tentar diferentes métodos de autenticação
  const authMethods = [
    {
      name: 'Authorization Bearer',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
    },
    {
      name: 'X-API-Key',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
      },
    },
    {
      name: 'X-API-Key with X-Auth-Scheme',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'x-auth-scheme': 'langsmith-api-key',
      },
    },
  ]
  
  // Teste 3: Tentar diferentes endpoints
  const endpoints = [
    {
      name: 'GET /v1/runs',
      url: 'https://api.smith.langchain.com/v1/runs?limit=10',
      method: 'GET',
    },
    {
      name: 'POST /v1/runs/query',
      url: 'https://api.smith.langchain.com/v1/runs/query',
      method: 'POST',
      body: JSON.stringify({ limit: 10, offset: 0 }),
    },
    {
      name: 'GET /v1/traces',
      url: 'https://api.smith.langchain.com/v1/traces?limit=10',
      method: 'GET',
    },
    {
      name: 'GET /v1/projects',
      url: 'https://api.smith.langchain.com/v1/projects',
      method: 'GET',
    },
    {
      name: 'GET /v1/datasets',
      url: 'https://api.smith.langchain.com/v1/datasets',
      method: 'GET',
    },
  ]
  
  // Executar testes
  for (const authMethod of authMethods) {
    for (const endpoint of endpoints) {
      try {
        const startTime = Date.now()
        const response = await fetch(endpoint.url, {
          method: endpoint.method as any,
          headers: authMethod.headers,
          ...(endpoint.body ? { body: endpoint.body } : {}),
        })
        
        const duration = Date.now() - startTime
        const responseText = await response.text().catch(() => 'Failed to read response')
        let responseData: any = null
        
        try {
          responseData = JSON.parse(responseText)
        } catch {
          responseData = responseText.substring(0, 500)
        }
        
        results.push({
          test: `${authMethod.name} - ${endpoint.name}`,
          url: endpoint.url,
          method: endpoint.method,
          status: response.status,
          statusText: response.statusText,
          ok: response.ok,
          duration: `${duration}ms`,
          responseHeaders: Object.fromEntries(response.headers.entries()),
          responseData: typeof responseData === 'string' ? responseData : JSON.stringify(responseData).substring(0, 500),
          success: response.ok,
        })
        
        // Se funcionou, parar aqui
        if (response.ok) {
          results.push({
            note: `SUCESSO encontrado! Método: ${authMethod.name}, Endpoint: ${endpoint.name}`,
          })
        }
      } catch (error: any) {
        results.push({
          test: `${authMethod.name} - ${endpoint.name}`,
          error: error.message,
          stack: error.stack,
        })
      }
    }
  }
  
  return NextResponse.json({
    summary: {
      totalTests: results.length,
      successful: results.filter((r) => r.success).length,
      failed: results.filter((r) => r.status && !r.ok).length,
    },
    results,
  })
}
