import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient } from '@/app/lib/langgraph-client'

/**
 * GET /api/studio/threads/[threadId]/state
 * Obtém o estado completo de uma thread usando SDK
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await params
    const client = createLangGraphClient()
    
    try {
      // Usar SDK para obter estado da thread
      const state = await client.threads.getState(threadId)
      
      return NextResponse.json(state)
    } catch (sdkError: any) {
      console.error('[Studio API] Erro ao obter estado da thread via SDK:', sdkError)
      
      const statusCode = sdkError.status || sdkError.statusCode || 500
      return NextResponse.json(
        { 
          error: 'Failed to fetch thread state', 
          details: sdkError.message || 'Unknown error' 
        },
        { status: statusCode }
      )
    }
  } catch (error: any) {
    console.error('[Studio API] Erro ao obter estado da thread:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
