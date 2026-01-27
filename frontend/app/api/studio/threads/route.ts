import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient } from '@/app/lib/langgraph-client'

/**
 * GET /api/studio/threads
 * Lista todas as threads do LangGraph Deployment usando SDK
 */
export async function GET(request: NextRequest) {
  try {
    const client = createLangGraphClient()
    const searchParams = request.nextUrl.searchParams
    const limit = parseInt(searchParams.get('limit') || '100')
    const offset = parseInt(searchParams.get('offset') || '0')
    
    try {
      // Usar SDK para buscar threads - remover metadata: null (SDK não aceita null)
      const threads = await client.threads.search({
        limit,
        offset,
      })
      
      // Normalizar resposta para manter compatibilidade - SDK pode retornar array ou objeto
      let threadsArray: any[] = []
      if (Array.isArray(threads)) {
        threadsArray = threads
      } else if (threads && typeof threads === 'object') {
        threadsArray = threads.threads || threads.data || []
      }
      
      return NextResponse.json({ threads: threadsArray })
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao buscar threads via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
        status: sdkError.status || sdkError.statusCode,
      })
      // Retornar array vazio em caso de erro
      return NextResponse.json({ threads: [] })
    }
  } catch (error: any) {
    console.error('[Studio API] Erro ao listar threads:', error)
    return NextResponse.json({ threads: [] })
  }
}

/**
 * POST /api/studio/threads
 * Cria uma nova thread usando SDK
 */
export async function POST(request: NextRequest) {
  try {
    const client = createLangGraphClient()
    const body = await request.json()
    
    try {
      // Usar SDK para criar thread
      const thread = await client.threads.create(body)
      
      return NextResponse.json(thread)
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao criar thread via SDK:', sdkError)
      
      // Retornar erro apropriado
      const statusCode = sdkError.status || sdkError.statusCode || 500
      return NextResponse.json(
        { 
          error: 'Failed to create thread', 
          details: sdkError.message || 'Unknown error' 
        },
        { status: statusCode }
      )
    }
  } catch (error: any) {
    console.error('[Studio API] Erro ao criar thread:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
