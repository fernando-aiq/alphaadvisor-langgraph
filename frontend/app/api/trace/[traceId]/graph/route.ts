import { NextRequest, NextResponse } from 'next/server'
import { createLangSmithClient, getLangSmithConfig, collectRuns } from '@/app/lib/langsmith-trace-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/trace/[traceId]/graph
 * Busca dados do grafo de um trace do LangSmith usando SDK
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  try {
    const { traceId } = await params
    const { projectName } = getLangSmithConfig()
    const client = createLangSmithClient()
    
    try {
      // Usar SDK para buscar runs do trace (limite máximo é 100)
      const runsIterable = client.listRuns({
        traceId: traceId,
        projectName: projectName || undefined,
        limit: 100,
      })
      
      const runs = await collectRuns(runsIterable)
      
      // Construir grafo a partir dos runs
      const nodes: any[] = []
      const edges: any[] = []
      const nodeMap = new Map<string, any>()
      
      runs.forEach((run: any) => {
        const runId = run.id || run.run_id || String(run.run_id)
        const runName = run.name || run.run_type || 'Unknown'
        const runType = run.run_type || 'unknown'
        
        // Calcular duração se tiver start_time e end_time
        let durationMs: number | undefined = undefined
        if (run.start_time && run.end_time) {
          durationMs = new Date(run.end_time).getTime() - new Date(run.start_time).getTime()
        }
        
        // Criar nó para cada run
        const node = {
          id: runId,
          label: runName,
          type: runType,
          status: run.status || 'unknown',
          timestamp: run.start_time,
          duration_ms: durationMs,
          data: {
            input: run.inputs || {},
            output: run.outputs || {},
            error: run.error,
            metadata: run.extra?.metadata || run.metadata || {},
          },
        }
        
        nodes.push(node)
        nodeMap.set(runId, node)
        
        // Criar aresta se tiver parent
        if (run.parent_run_id) {
          const parentId = String(run.parent_run_id)
          edges.push({
            id: `${parentId}-${runId}`,
            source: parentId,
            target: runId,
            timestamp: run.start_time,
          })
        }
      })
      
      return NextResponse.json({
        nodes,
        edges,
        run_count: runs.length,
      })
    } catch (sdkError: any) {
      console.error('[API Route /api/trace/[traceId]/graph] Erro ao buscar trace via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
      })
      
      return NextResponse.json({
        nodes: [],
        edges: [],
        error: `Failed to fetch trace: ${sdkError.message || 'Unknown error'}`,
      })
    }
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]/graph] Erro:', {
      message: error.message,
      stack: error.stack,
    })
    return NextResponse.json({
      nodes: [],
      edges: [],
      error: error.message || 'Internal server error',
    }, { status: 500 })
  }
}
