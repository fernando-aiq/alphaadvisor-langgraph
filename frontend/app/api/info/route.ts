import { NextRequest, NextResponse } from 'next/server'

// Função para obter URL do backend
function getBackendUrl() {
  const url = process.env.API_URL || 
              process.env.NEXT_PUBLIC_API_URL || 
              'http://localhost:8000'
  return url.trim().replace(/\/$/, '') // Remove trailing slash
}

const BACKEND_URL = getBackendUrl()

// Função auxiliar para criar headers CORS
function createCorsHeaders(origin: string | null): Headers {
  const headers = new Headers()
  headers.set('Access-Control-Allow-Origin', origin || '*')
  headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS')
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-LangSmith-API-Key, Accept, x-auth-scheme, x-user-id, x-tenant-id')
  headers.set('Access-Control-Allow-Credentials', 'true')
  return headers
}

// Handler para GET e OPTIONS
export async function GET(request: NextRequest) {
  return handleInfoRequest(request, 'GET')
}

export async function OPTIONS(request: NextRequest) {
  return handleInfoRequest(request, 'OPTIONS')
}

async function handleInfoRequest(request: NextRequest, method: string) {
  const origin = request.headers.get('origin')
  
  // Verificar se BACKEND_URL está configurado
  if (!BACKEND_URL || BACKEND_URL === 'http://localhost:8000') {
    console.error('[Info Proxy] BACKEND_URL não configurado!')
    const errorHeaders = createCorsHeaders(origin)
    errorHeaders.set('Content-Type', 'application/json')
    return NextResponse.json(
      { 
        error: 'Backend URL not configured',
        message: 'API_URL environment variable is not set in Vercel',
        hint: 'Configure API_URL in Vercel project settings'
      },
      { status: 500, headers: errorHeaders }
    )
  }
  
  try {
    const backendUrl = `${BACKEND_URL}/info`
    
    console.log(`[Info Proxy] ${method} /info -> ${backendUrl}`)
    console.log(`[Info Proxy] Origin: ${origin}`)
    
    // Preparar headers
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    // Copiar headers importantes
    if (origin) {
      headers['Origin'] = origin
    }
    
    // Copiar headers customizados
    const customHeaders = ['X-LangSmith-API-Key', 'Authorization', 'Accept']
    for (const headerName of customHeaders) {
      const headerValue = request.headers.get(headerName)
      if (headerValue) {
        headers[headerName] = headerValue
      }
    }
    
    // Para OPTIONS, apenas retornar CORS headers
    if (method === 'OPTIONS') {
      const responseHeaders = createCorsHeaders(origin)
      return new NextResponse(null, { status: 200, headers: responseHeaders })
    }
    
    // Criar AbortController para timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    // Fazer requisição para o backend
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
      signal: controller.signal,
    }).finally(() => clearTimeout(timeoutId))
    
    console.log(`[Info Proxy] Response status: ${response.status}`)
    
    // Obter resposta do backend
    const responseText = await response.text()
    
    // Preparar headers da resposta com CORS
    const responseHeaders = new Headers()
    
    // Copiar headers do backend
    const headersToCopy = ['Content-Type']
    for (const headerName of headersToCopy) {
      const headerValue = response.headers.get(headerName)
      if (headerValue) {
        responseHeaders.set(headerName, headerValue)
      }
    }
    
    // Sempre adicionar CORS headers (sobrescrever qualquer header do backend)
    const corsHeaders = createCorsHeaders(origin)
    corsHeaders.forEach((value, key) => {
      responseHeaders.set(key, value)
    })
    
    // Retornar resposta
    return new NextResponse(responseText, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    })
    
  } catch (error: any) {
    console.error('[Info Proxy] Erro:', error)
    console.error('[Info Proxy] Tipo do erro:', error.name)
    console.error('[Info Proxy] Mensagem:', error.message)
    
    // Sempre retornar CORS headers mesmo em caso de erro
    const errorHeaders = createCorsHeaders(origin)
    errorHeaders.set('Content-Type', 'application/json')
    
    // Se for timeout
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Request timeout', message: 'Backend não respondeu em 30 segundos' },
        { status: 504, headers: errorHeaders }
      )
    }
    
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error', 
        type: error.name
      },
      { status: 500, headers: errorHeaders }
    )
  }
}
