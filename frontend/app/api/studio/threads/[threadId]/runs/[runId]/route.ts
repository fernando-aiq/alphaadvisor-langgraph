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
 * GET /api/studio/threads/[threadId]/runs/[runId]
 * Obtém detalhes de um run específico
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string; runId: string }> }
) {
  try {
    const { threadId, runId } = await params
    const { apiUrl, apiKey } = getLangSmithConfig()
    
    const response = await fetch(`${apiUrl}/threads/${threadId}/runs/${runId}`, {
      method: 'GET',
      headers: createHeaders(apiKey),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Failed to fetch run details', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[Studio API] Erro ao obter detalhes do run:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
