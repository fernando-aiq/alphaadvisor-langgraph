import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient } from '@/app/lib/langgraph-client'

/**
 * GET /api/studio/threads/[threadId]/runs
 * Lista runs de uma thread usando SDK
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await params
    const client = createLangGraphClient()
    const searchParams = request.nextUrl.searchParams
    
    const limit = searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : undefined
    const offset = searchParams.get('offset') ? parseInt(searchParams.get('offset')!) : undefined
    
    try {
      // Usar SDK para listar runs
      const runs = await client.runs.list(threadId, {
        limit,
        offset,
      })
      
      // Normalizar resposta para manter compatibilidade
      const runsArray = Array.isArray(runs) ? runs : []
      
      return NextResponse.json({ runs: runsArray })
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao listar runs via SDK:', sdkError)
      
      const statusCode = sdkError.status || sdkError.statusCode || 500
      return NextResponse.json(
        { 
          error: 'Failed to fetch runs', 
          details: sdkError.message || 'Unknown error' 
        },
        { status: statusCode }
      )
    }
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
 * Cria um novo run em uma thread usando SDK
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await params
    const client = createLangGraphClient()
    const body = await request.json()
    
    try {
      // Usar SDK para criar run
      // O SDK pode ter diferentes métodos dependendo da versão
      // Tentar usar create ou stream dependendo do que está disponível
      const run = await client.runs.create(threadId, body)
      
      return NextResponse.json(run)
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao criar run via SDK:', sdkError)
      
      const statusCode = sdkError.status || sdkError.statusCode || 500
      return NextResponse.json(
        { 
          error: 'Failed to create run', 
          details: sdkError.message || 'Unknown error' 
        },
        { status: statusCode }
      )
    }
  } catch (error: any) {
    console.error('[Studio API] Erro ao criar run:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
