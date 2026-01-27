import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient } from '@/app/lib/langgraph-client'

/**
 * GET /api/studio/threads/[threadId]/runs/[runId]
 * Obtém detalhes de um run específico usando SDK
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string; runId: string }> }
) {
  try {
    const { threadId, runId } = await params
    const client = createLangGraphClient()
    
    try {
      // Usar SDK para obter detalhes do run
      const run = await client.runs.get(threadId, runId)
      
      return NextResponse.json(run)
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao obter detalhes do run via SDK:', sdkError)
      
      const statusCode = sdkError.status || sdkError.statusCode || 500
      return NextResponse.json(
        { 
          error: 'Failed to fetch run details', 
          details: sdkError.message || 'Unknown error' 
        },
        { status: statusCode }
      )
    }
  } catch (error: any) {
    console.error('[Studio API] Erro ao obter detalhes do run:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
