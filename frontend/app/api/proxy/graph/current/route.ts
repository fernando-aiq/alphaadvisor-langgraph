import { NextRequest, NextResponse } from 'next/server'

function getBackendUrl() {
  return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}
const BACKEND_URL = getBackendUrl()

export const dynamic = 'force-dynamic' // Forçar rota dinâmica

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const userId = searchParams.get('user_id') || 'default'
    const authHeader = request.headers.get('authorization')
    
    const backendUrl = `${BACKEND_URL}/api/configuracoes/graph/current?user_id=${userId}`
    
    console.log('[API Proxy] Fazendo requisição para backend:', backendUrl)
    
    // Criar AbortController para timeout manual
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 segundos
    
    try {
      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeader ? { 'Authorization': authHeader } : {})
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        console.error('[API Proxy] Erro do backend:', response.status, response.statusText)
        const errorText = await response.text()
        return NextResponse.json(
          { error: `Backend error: ${response.status}`, details: errorText },
          { status: response.status }
        )
      }
      
      const data = await response.json()
      console.log('[API Proxy] Resposta recebida do backend com sucesso')
      
      return NextResponse.json(data)
    } catch (fetchError: any) {
      clearTimeout(timeoutId)
      if (fetchError.name === 'AbortError') {
        console.error('[API Proxy] Timeout ao conectar com backend')
        return NextResponse.json(
          { error: 'Timeout ao conectar com o backend' },
          { status: 504 }
        )
      }
      throw fetchError
    }
  } catch (error: any) {
    console.error('[API Proxy] Erro geral:', error.message, error.stack)
    return NextResponse.json(
      { error: error.message || 'Erro ao fazer proxy para o backend', details: error.stack },
      { status: 500 }
    )
  }
}

