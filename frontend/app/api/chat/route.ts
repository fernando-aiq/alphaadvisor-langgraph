import { NextRequest, NextResponse } from 'next/server'

// Usar runtime config para garantir que a variável seja lida corretamente
function getBackendUrl() {
  // Tentar diferentes formas de obter a URL
  const url = process.env.API_URL || 
              process.env.NEXT_PUBLIC_API_URL || 
              'http://localhost:8000'
  return url
}

const BACKEND_URL = getBackendUrl()

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    console.log('[API Route] Backend URL:', BACKEND_URL)
    console.log('[API Route] Request body:', body)
    
    const backendUrl = `${BACKEND_URL}/api/chat`
    console.log('[API Route] Calling:', backendUrl)
    
    // Criar AbortController para timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    }).finally(() => clearTimeout(timeoutId))

    console.log('[API Route] Response status:', response.status)
    console.log('[API Route] Response headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      console.error('[API Route] Backend error:', errorText)
      return NextResponse.json(
        { error: 'Backend request failed', details: errorText },
        { status: response.status }
      )
    }

    const responseText = await response.text()
    console.log('[API Route] Response text length:', responseText.length)
    console.log('[API Route] Response text preview:', responseText.substring(0, 200))
    
    if (!responseText) {
      console.error('[API Route] Empty response from backend')
      return NextResponse.json(
        { error: 'Empty response from backend' },
        { status: 500 }
      )
    }

    try {
      const data = JSON.parse(responseText)
      console.log('[API Route] Parsed data:', data)
      return NextResponse.json(data)
    } catch (parseError) {
      console.error('[API Route] JSON parse error:', parseError)
      return NextResponse.json(
        { error: 'Invalid JSON response from backend', raw: responseText.substring(0, 500) },
        { status: 500 }
      )
    }
  } catch (error: any) {
    console.error('[API Route] Erro ao fazer proxy para backend:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error', type: error.name },
      { status: 500 }
    )
  }
}


