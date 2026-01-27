import { NextRequest, NextResponse } from 'next/server'
import { createLangSmithClient, getLangSmithConfig, collectRuns } from '@/app/lib/langsmith-trace-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/trace/[traceId]/steps
 * Busca steps (runs) de um trace do LangSmith usando SDK
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
      
      // Ordenar runs por start_time
      const sortedRuns = runs.sort((a: any, b: any) => {
        const timeA = a.start_time ? new Date(a.start_time).getTime() : 0
        const timeB = b.start_time ? new Date(b.start_time).getTime() : 0
        return timeA - timeB
      })
      
      // Converter runs para steps
      const steps = sortedRuns.map((run: any, index: number) => {
        const runId = run.id || run.run_id || String(run.run_id)
        const runName = run.name || run.run_type || 'Unknown'
        const runType = run.run_type || 'unknown'
        
        // Calcular duração
        let durationMs: number | null = null
        if (run.start_time && run.end_time) {
          durationMs = new Date(run.end_time).getTime() - new Date(run.start_time).getTime()
        }
        
        return {
          id: runId,
          step: index + 1,
          name: runName,
          type: runType,
          status: run.status || 'unknown',
          start_time: run.start_time,
          end_time: run.end_time,
          duration_ms: durationMs,
          input: run.inputs || {},
          output: run.outputs || {},
          error: run.error,
          parent_run_id: run.parent_run_id,
          metadata: run.extra?.metadata || run.metadata || {},
        }
      })
      
      return NextResponse.json({
        steps,
        total: steps.length,
      })
    } catch (sdkError: any) {
      console.error('[API Route /api/trace/[traceId]/steps] Erro ao buscar trace via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
      })
      
      return NextResponse.json({
        steps: [],
        error: `Failed to fetch trace: ${sdkError.message || 'Unknown error'}`,
      })
    }
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]/steps] Erro:', {
      message: error.message,
      stack: error.stack,
    })
    return NextResponse.json({
      steps: [],
      error: error.message || 'Internal server error',
    }, { status: 500 })
  }
}
