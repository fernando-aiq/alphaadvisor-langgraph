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
 * GET /api/studio/threads/[threadId]/runs
 * Lista runs de uma thread
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await params
    const { apiUrl, apiKey } = getLangSmithConfig()
    const searchParams = request.nextUrl.searchParams
    
    // Construir query params
    const queryParams = new URLSearchParams()
    if (searchParams.get('limit')) queryParams.append('limit', searchParams.get('limit')!)
    if (searchParams.get('offset')) queryParams.append('offset', searchParams.get('offset')!)
    
    const url = `${apiUrl}/threads/${threadId}/runs${queryParams.toString() ? `?${queryParams}` : ''}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: createHeaders(apiKey),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Failed to fetch runs', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    
    // Normalizar resposta
    const runs = Array.isArray(data) ? data : (data.runs || [])
    
    return NextResponse.json({ runs })
  } catch (error: any) {
    console.error('[Studio API] Erro ao listar runs:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/studio/threads/[threadId]/runs
 * Cria um novo run em uma thread
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await params
    const { apiUrl, apiKey } = getLangSmithConfig()
    const body = await request.json()
    
    const response = await fetch(`${apiUrl}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: createHeaders(apiKey),
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Failed to create run', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[Studio API] Erro ao criar run:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
