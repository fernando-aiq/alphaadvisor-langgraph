import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

function getBackendUrl() {
  const url = process.env.API_URL ||
              process.env.NEXT_PUBLIC_API_URL ||
              'http://localhost:8000'
  return url
}

const BACKEND_URL = getBackendUrl()

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/regulacoes`

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
  } catch (error: unknown) {
    const err = error as Error
    console.error('[API Route /api/regulacoes GET] Erro:', err)
    return NextResponse.json(
      {
        error: err.message || 'Internal server error',
        type: err.name,
        details: process.env.NODE_ENV === 'development' ? err.stack : undefined
      },
      { status: 500 }
    )
  }
}
