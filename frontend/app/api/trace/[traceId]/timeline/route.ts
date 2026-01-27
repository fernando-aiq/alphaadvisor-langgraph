import { NextRequest, NextResponse } from 'next/server'
import { createLangSmithClient, getLangSmithConfig, collectRuns } from '@/app/lib/langsmith-trace-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/trace/[traceId]/timeline
 * Busca timeline de um trace do LangSmith usando SDK
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
      
      // Ordenar por start_time
      const sortedRuns = runs.sort((a: any, b: any) => {
        const timeA = a.start_time ? new Date(a.start_time).getTime() : 0
        const timeB = b.start_time ? new Date(b.start_time).getTime() : 0
        return timeA - timeB
      })
      
      // Encontrar tempo inicial do trace
      const startTimes = sortedRuns
        .map((r: any) => r.start_time ? new Date(r.start_time).getTime() : null)
        .filter((t): t is number => t !== null)
      const traceStartTime = startTimes.length > 0 ? Math.min(...startTimes) : null
      
      // Converter runs para timeline events
      const timeline = sortedRuns.map((run: any) => {
        const startTime = run.start_time ? new Date(run.start_time).getTime() : null
        const endTime = run.end_time ? new Date(run.end_time).getTime() : null
        const duration = startTime && endTime ? endTime - startTime : null
        
        // Calcular tempo relativo ao início do trace
        const relativeTimeMs = traceStartTime && startTime 
          ? startTime - traceStartTime 
          : 0
        
        // Determinar tipo de evento baseado no run_type
        let eventType = 'node_execution'
        let label = run.name || run.run_type || 'Unknown'
        
        if (run.run_type === 'tool') {
          eventType = 'tool_call'
          label = `Tool: ${run.name || 'Unknown'}`
        } else if (run.run_type === 'llm' || run.run_type === 'chat') {
          eventType = 'llm_call'
          label = `LLM: ${run.name || run.run_type}`
        } else if (run.run_type === 'chain') {
          eventType = 'node_execution'
          label = `Node: ${run.name || 'Unknown'}`
        }
        
        return {
          type: eventType,
          node: run.name,
          tool: run.run_type === 'tool' ? run.name : undefined,
          timestamp: run.start_time || run.created_at,
          relative_time_ms: relativeTimeMs,
          duration_ms: duration,
          label: label,
        }
      })
      
      // Calcular start_time e end_time do trace
      const endTimes = sortedRuns
        .map((r: any) => r.end_time ? new Date(r.end_time).getTime() : null)
        .filter((t): t is number => t !== null)
      const traceEndTime = endTimes.length > 0 ? Math.max(...endTimes) : null
      
      return NextResponse.json({
        trace_id: traceId,
        start_time: traceStartTime ? new Date(traceStartTime).toISOString() : null,
        end_time: traceEndTime ? new Date(traceEndTime).toISOString() : null,
        timeline,
        total_events: timeline.length,
      })
    } catch (sdkError: any) {
      console.error('[API Route /api/trace/[traceId]/timeline] Erro ao buscar trace via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
      })
      
      return NextResponse.json({
        trace_id: traceId,
        start_time: null,
        end_time: null,
        timeline: [],
        total_events: 0,
        error: `Failed to fetch trace: ${sdkError.message || 'Unknown error'}`,
      })
    }
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]/timeline] Erro:', {
      message: error.message,
      stack: error.stack,
    })
    return NextResponse.json({
      trace_id: (await params).traceId,
      start_time: null,
      end_time: null,
      timeline: [],
      total_events: 0,
      error: error.message || 'Internal server error',
    }, { status: 500 })
  }
}
