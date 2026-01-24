import { NextRequest, NextResponse } from 'next/server'

function getBackendUrl() {
  const url = process.env.API_URL || 
              process.env.NEXT_PUBLIC_API_URL || 
              'http://localhost:8000'
  return url
}

const BACKEND_URL = getBackendUrl()

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/cliente/carteira`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Backend request failed', details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[API Route] Erro ao buscar carteira:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error', type: error.name },
      { status: 500 }
    )
  }
}

