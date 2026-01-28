import { NextRequest, NextResponse } from 'next/server'

/**
 * Proxy para /api/configuracoes do backend Flask.
 * Usa API_URL (ou BACKEND_URL) no servidor — não NEXT_PUBLIC_API_URL (LangGraph).
 * Assim a página Autonomia chama esta rota (mesma origem) e evita 403 do LangGraph.
 */
function getFlaskBackendUrl() {
  return (
    process.env.API_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  ).trim().replace(/\r\n/g, '').replace(/\n/g, '')
}

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const backendUrl = getFlaskBackendUrl()
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('user_id') || 'default'
    const authHeader = request.headers.get('authorization')

    const url = `${backendUrl}/api/configuracoes?user_id=${userId}`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      signal: AbortSignal.timeout(15000),
    })

    if (!response.ok) {
      const text = await response.text()
      return NextResponse.json(
        { error: `Backend: ${response.status}`, details: text },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[API configuracoes] GET error:', error?.message)
    return NextResponse.json(
      { error: error?.message || 'Erro ao buscar configurações' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const backendUrl = getFlaskBackendUrl()
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('user_id') || 'default'
    const authHeader = request.headers.get('authorization')
    const body = await request.json().catch(() => ({}))

    const url = `${backendUrl}/api/configuracoes?user_id=${userId}`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000),
    })

    if (!response.ok) {
      const text = await response.text()
      return NextResponse.json(
        { error: `Backend: ${response.status}`, details: text },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[API configuracoes] POST error:', error?.message)
    return NextResponse.json(
      { error: error?.message || 'Erro ao salvar configurações' },
      { status: 500 }
    )
  }
}
