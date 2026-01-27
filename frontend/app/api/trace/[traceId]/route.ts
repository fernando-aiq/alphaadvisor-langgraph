import { NextRequest, NextResponse } from 'next/server'
import { createLangSmithClient, getLangSmithConfig, collectRuns } from '@/app/lib/langsmith-trace-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/trace/[traceId]
 * Busca dados de um trace específico do LangSmith usando SDK
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  try {
    const { traceId } = await params
    const { projectName } = getLangSmithConfig()
    const client = createLangSmithClient()
    
    console.log('[API Route /api/trace/[traceId]] Buscando trace via SDK:', {
      traceId,
      hasProjectName: !!projectName,
    })
    
    try {
      // Usar SDK para buscar runs do trace (limite máximo é 100)
      const runsIterable = client.listRuns({
        traceId: traceId,
        projectName: projectName || undefined,
        limit: 100,
      })
      
      // Coletar todos os runs do async iterable
      const runs = await collectRuns(runsIterable)
      
      console.log('[API Route /api/trace/[traceId]] Runs encontrados via SDK:', runs.length)
      
      // Processar runs para criar estrutura do trace
      if (runs.length === 0) {
        return NextResponse.json({
          trace_id: traceId,
          name: `Trace ${traceId}`,
          runs: [],
          start_time: null,
          end_time: null,
          status: 'not_found',
          error: 'Trace não encontrado',
          langsmith_url: `https://smith.langchain.com/o/${projectName || 'default'}/traces/${traceId}`,
        })
      }
      
      // Encontrar o run raiz (root run - sem parent_run_id)
      const rootRun = runs.find((run: any) => !run.parent_run_id || run.parent_run_id === null) || runs[0]
      
      // Calcular tempos
      const startTimes = runs
        .map((r: any) => r.start_time ? new Date(r.start_time).getTime() : null)
        .filter((t): t is number => t !== null)
      const endTimes = runs
        .map((r: any) => r.end_time ? new Date(r.end_time).getTime() : null)
        .filter((t): t is number => t !== null)
      
      const startTime = startTimes.length > 0 
        ? new Date(Math.min(...startTimes)).toISOString() 
        : null
      const endTime = endTimes.length > 0 
        ? new Date(Math.max(...endTimes)).toISOString() 
        : null
      
      // Determinar status geral
      const hasErrors = runs.some((r: any) => r.error || r.status === 'error')
      const allCompleted = runs.every((r: any) => 
        r.status === 'success' || r.status === 'error' || r.status === 'cancelled'
      )
      const status = hasErrors ? 'error' : (allCompleted ? 'success' : 'running')
      
      return NextResponse.json({
        trace_id: traceId,
        name: rootRun.name || rootRun.run_type || `Trace ${traceId}`,
        runs: runs,
        start_time: startTime,
        end_time: endTime,
        status: status,
        error: hasErrors ? (runs.find((r: any) => r.error)?.error || 'Unknown error') : null,
        run_count: runs.length,
        langsmith_url: `https://smith.langchain.com/o/${projectName || 'default'}/traces/${traceId}`,
      })
    } catch (sdkError: any) {
      console.error('[API Route /api/trace/[traceId]] Erro ao buscar trace via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
        name: sdkError.name,
      })
      
      // Retornar estrutura básica em caso de erro
      return NextResponse.json({
        trace_id: traceId,
        name: `Trace ${traceId}`,
        runs: [],
        start_time: null,
        end_time: null,
        status: 'unknown',
        error: `Failed to fetch trace: ${sdkError.message || 'Unknown error'}`,
        langsmith_url: `https://smith.langchain.com/o/${projectName || 'default'}/traces/${traceId}`,
      })
    }
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]] Erro:', {
      message: error.message,
      stack: error.stack,
    })
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        trace_id: (await params).traceId,
      },
      { status: 500 }
    )
  }
}
