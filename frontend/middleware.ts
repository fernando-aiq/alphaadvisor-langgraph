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
function createCorsHeaders(origin: string | null, methods: string = 'GET, OPTIONS'): Headers {
  const headers = new Headers()
  headers.set('Access-Control-Allow-Origin', origin || '*')
  headers.set('Access-Control-Allow-Methods', methods)
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-LangSmith-API-Key, Accept, x-auth-scheme, x-user-id, x-tenant-id')
  headers.set('Access-Control-Allow-Credentials', 'true')
  return headers
}

// Lista de rotas LangGraph Server que devem ser capturadas pelo middleware
const LANGGRAPH_ROUTES = [
  '/info',
  '/health',
  '/assistants',
  '/threads',
  '/docs'
]

// Verificar se o pathname corresponde a uma rota LangGraph Server
function isLangGraphRoute(pathname: string): boolean {
  // Rotas exatas
  if (LANGGRAPH_ROUTES.includes(pathname)) {
    return true
  }
  
  // Rotas que começam com /assistants/ ou /threads/
  if (pathname.startsWith('/assistants/') || pathname.startsWith('/threads/')) {
    return true
  }
  
  return false
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Interceptar rotas LangGraph Server na raiz
  if (isLangGraphRoute(pathname)) {
    const origin = request.headers.get('origin')
    const method = request.method
    console.log(`[Middleware] Interceptando requisição para ${pathname}`)
    console.log(`[Middleware] Método: ${method}`)
    console.log(`[Middleware] Origin: ${origin}`)
    console.log(`[Middleware] BACKEND_URL: ${BACKEND_URL}`)
    
    // Verificar se BACKEND_URL está configurado
    if (!BACKEND_URL || BACKEND_URL === 'http://localhost:8000') {
      console.error('[Middleware] BACKEND_URL não configurado!')
      const errorHeaders = createCorsHeaders(origin, 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
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
      // Construir URL do backend (preservar pathname completo)
      const backendUrl = `${BACKEND_URL}${pathname}`
      
      // Preservar query string se houver
      const searchParams = request.nextUrl.searchParams.toString()
      const fullBackendUrl = searchParams 
        ? `${backendUrl}?${searchParams}`
        : backendUrl
      
      console.log(`[Middleware] Fazendo proxy para: ${fullBackendUrl}`)
      
      // Preparar headers para o backend
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      // Copiar headers importantes
      if (origin) {
        headers['Origin'] = origin
      }
      
      const referer = request.headers.get('referer')
      if (referer) {
        headers['Referer'] = referer
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
        console.log(`[Middleware] Retornando resposta OPTIONS com CORS`)
        const responseHeaders = createCorsHeaders(origin, 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        responseHeaders.set('Access-Control-Max-Age', '86400')
        return new NextResponse(null, { status: 200, headers: responseHeaders })
      }
      
      // Preparar body se houver (para POST, PUT, PATCH)
      let body: string | undefined = undefined
      if (['POST', 'PUT', 'PATCH'].includes(method)) {
        try {
          const requestBody = await request.json()
          body = JSON.stringify(requestBody)
        } catch (e) {
          // Se não conseguir parsear JSON, tentar como texto
          try {
            body = await request.text()
          } catch (e2) {
            // Se não houver body, deixar undefined
          }
        }
      }
      
      // Criar AbortController para timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 segundos para LangGraph
      
      // Fazer requisição para o backend
      const response = await fetch(fullBackendUrl, {
        method,
        headers,
        body,
        signal: controller.signal,
      }).finally(() => clearTimeout(timeoutId))
      
      console.log(`[Middleware] Resposta do backend: ${response.status} ${response.statusText}`)
      
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
      const corsHeaders = createCorsHeaders(origin, 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
      corsHeaders.forEach((value, key) => {
        responseHeaders.set(key, value)
      })
      
      console.log(`[Middleware] Retornando resposta com CORS headers (status: ${response.status})`)
      
      // Retornar resposta
      return new NextResponse(responseText, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      })
      
    } catch (error: any) {
      console.error('[Middleware] Erro ao fazer proxy:', error)
      console.error('[Middleware] Tipo do erro:', error.name)
      console.error('[Middleware] Mensagem:', error.message)
      
      // Sempre retornar CORS headers mesmo em caso de erro
      const errorHeaders = createCorsHeaders(origin, 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
      errorHeaders.set('Content-Type', 'application/json')
      
      // Se for timeout
      if (error.name === 'AbortError') {
        console.error('[Middleware] Timeout ao conectar com backend')
        return NextResponse.json(
          { error: 'Request timeout', message: 'Backend não respondeu em 60 segundos' },
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
  
  // Para outras rotas, continuar normalmente
  return NextResponse.next()
}

// Configurar matcher para executar em rotas LangGraph Server
export const config = {
  matcher: [
    '/info',
    '/health',
    '/assistants/:path*',
    '/threads/:path*',
    '/docs'
  ],
}
