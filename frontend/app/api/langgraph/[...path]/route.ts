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
  headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-LangSmith-API-Key, Accept, x-auth-scheme, x-user-id, x-tenant-id')
  headers.set('Access-Control-Allow-Credentials', 'true')
  return headers
}

// Handler para todos os métodos HTTP
// Suporta tanto Next.js 14 (params direto) quanto Next.js 15+ (params como Promise)
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'GET')
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'POST')
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'PUT')
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'DELETE')
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'PATCH')
}

export async function OPTIONS(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  return handleRequest(request, params, 'OPTIONS')
}

// Handler genérico para fazer proxy
async function handleRequest(
  request: NextRequest,
  params: Promise<{ path: string[] }> | { path: string[] },
  method: string
) {
  try {
    // Resolver params se for Promise (Next.js 15+)
    const resolvedParams = params instanceof Promise ? await params : params
    
    // Construir path do backend
    // params.path é um array: ['assistants', 'search'] vira '/assistants/search'
    const backendPath = '/' + resolvedParams.path.join('/')
    
    // Construir URL completa do backend
    const backendUrl = `${BACKEND_URL}${backendPath}`
    
    // Preservar query string se houver
    const searchParams = request.nextUrl.searchParams.toString()
    const fullBackendUrl = searchParams 
      ? `${backendUrl}?${searchParams}`
      : backendUrl
    
    console.log(`[LangGraph Proxy] ${method} ${backendPath} -> ${fullBackendUrl}`)
    
    // Obter origin do request
    const origin = request.headers.get('origin')
    
    // Preparar headers para o backend
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    // Copiar headers importantes do request original
    if (origin) {
      headers['Origin'] = origin
    }
    
    const referer = request.headers.get('referer')
    if (referer) {
      headers['Referer'] = referer
    }
    
    // Copiar headers customizados (como X-LangSmith-API-Key)
    const customHeaders = ['X-LangSmith-API-Key', 'Authorization', 'Accept']
    for (const headerName of customHeaders) {
      const headerValue = request.headers.get(headerName)
      if (headerValue) {
        headers[headerName] = headerValue
      }
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
    
    console.log(`[LangGraph Proxy] Response status: ${response.status}`)
    
    // Obter resposta do backend
    const responseText = await response.text()
    
    // Preparar headers da resposta
    const responseHeaders = new Headers()
    
    // Copiar headers importantes do backend
    const headersToCopy = [
      'Content-Type',
      'Access-Control-Allow-Origin',
      'Access-Control-Allow-Methods',
      'Access-Control-Allow-Headers',
      'Access-Control-Allow-Credentials',
    ]
    
    for (const headerName of headersToCopy) {
      const headerValue = response.headers.get(headerName)
      if (headerValue) {
        responseHeaders.set(headerName, headerValue)
      }
    }
    
    // Sempre garantir CORS headers (sobrescrever qualquer header do backend)
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
    console.error('[LangGraph Proxy] Erro:', error)
    console.error('[LangGraph Proxy] Tipo do erro:', error.name)
    console.error('[LangGraph Proxy] Mensagem:', error.message)
    
    // Sempre criar headers CORS mesmo em caso de erro
    const errorHeaders = createCorsHeaders(origin)
    errorHeaders.set('Content-Type', 'application/json')
    
    // Se for timeout
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Request timeout', message: 'Backend não respondeu em 60 segundos' },
        { status: 504, headers: errorHeaders }
      )
    }
    
    // Tentar obter path para erro (pode falhar se params for Promise não resolvida)
    let errorPath = 'unknown'
    try {
      const resolvedParams = params instanceof Promise ? await params : params
      errorPath = resolvedParams.path.join('/')
    } catch (e) {
      // Ignorar erro ao obter path
    }
    
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error', 
        type: error.name,
        path: errorPath
      },
      { status: 500, headers: errorHeaders }
    )
  }
}
