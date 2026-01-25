import { NextRequest, NextResponse } from 'next/server'

function getLangSmithConfig() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() || ''
  const apiKey = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY?.trim() || ''
  
  if (!apiUrl) {
    throw new Error('NEXT_PUBLIC_API_URL não configurada')
  }
  
  if (!apiKey) {
    throw new Error('NEXT_PUBLIC_LANGSMITH_API_KEY não configurada')
  }
  
  return { apiUrl, apiKey }
}

function createHeaders(apiKey: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'x-api-key': apiKey,
  }
}

/**
 * GET /api/studio/threads
 * Lista todas as threads do LangSmith Deployment
 * NOTA: Este endpoint pode não estar disponível na API do LangGraph Deployment.
 * Se retornar 404 ou 405, significa que o endpoint não existe.
 */
export async function GET(request: NextRequest) {
  try {
    const { apiUrl, apiKey } = getLangSmithConfig()
    const searchParams = request.nextUrl.searchParams
    
    // Construir query params
    const queryParams = new URLSearchParams()
    if (searchParams.get('limit')) queryParams.append('limit', searchParams.get('limit')!)
    if (searchParams.get('offset')) queryParams.append('offset', searchParams.get('offset')!)
    
    const url = `${apiUrl}/threads${queryParams.toString() ? `?${queryParams}` : ''}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: createHeaders(apiKey),
    })
    
    // Se endpoint não existir, retornar array vazio
    if (response.status === 404 || response.status === 405) {
      return NextResponse.json({ threads: [] })
    }
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Failed to fetch threads', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    
    // Normalizar resposta para array de threads
    // A API pode retornar diretamente um array ou um objeto com threads
    const threads = Array.isArray(data) ? data : (data.threads || [])
    
    return NextResponse.json({ threads })
  } catch (error: any) {
    console.error('[Studio API] Erro ao listar threads:', error)
    // Retornar array vazio em caso de erro (endpoint pode não existir)
    return NextResponse.json({ threads: [] })
  }
}

/**
 * POST /api/studio/threads
 * Cria uma nova thread
 */
export async function POST(request: NextRequest) {
  try {
    const { apiUrl, apiKey } = getLangSmithConfig()
    const body = await request.json()
    
    const response = await fetch(`${apiUrl}/threads`, {
      method: 'POST',
      headers: createHeaders(apiKey),
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Failed to create thread', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[Studio API] Erro ao criar thread:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
