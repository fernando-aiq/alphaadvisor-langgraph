import { NextRequest, NextResponse } from 'next/server'
import { createLangSmithClient, getLangSmithConfig, collectRuns } from '@/app/lib/langsmith-trace-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/trace/[traceId]/tools
 * Busca tool calls de um trace do LangSmith usando SDK
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
      // Usar SDK para buscar runs do trace, filtrando apenas tool calls (limite máximo é 100)
      const runsIterable = client.listRuns({
        traceId: traceId,
        projectName: projectName || undefined,
        runType: 'tool', // Filtrar apenas tool runs
        limit: 100,
      })
      
      let toolRuns = await collectRuns(runsIterable)
      
      // Se não encontrou com filtro, buscar todos e filtrar depois
      if (toolRuns.length === 0) {
        const allRunsIterable = client.listRuns({
          traceId: traceId,
          projectName: projectName || undefined,
          limit: 100,
        })
        
        const allRuns = await collectRuns(allRunsIterable)
        toolRuns = allRuns.filter((run: any) => run.run_type === 'tool')
      }
      
      // Converter tool runs para formato esperado
      const toolCalls = toolRuns.map((run: any) => {
        const runId = run.id || run.run_id || String(run.run_id)
        const toolName = run.name || 'Unknown Tool'
        
        // Calcular duração
        let durationMs: number | null = null
        if (run.start_time && run.end_time) {
          durationMs = new Date(run.end_time).getTime() - new Date(run.start_time).getTime()
        }
        
        return {
          tool_name: toolName,
          timestamp: run.start_time || run.created_at,
          input: run.inputs || {},
          output: run.outputs || {},
          duration_ms: durationMs,
          error: run.error,
        }
      })
      
      // Calcular estatísticas
      const uniqueTools = new Set(toolCalls.map((tc: any) => tc.tool_name))
      const totalDuration = toolCalls
        .map((tc: any) => tc.duration_ms || 0)
        .reduce((sum: number, dur: number) => sum + dur, 0)
      const averageDuration = toolCalls.length > 0 ? totalDuration / toolCalls.length : 0
      
      // Agrupar por tool name para estatísticas
      const toolsStats: Record<string, any> = {}
      toolCalls.forEach((tc: any) => {
        if (!toolsStats[tc.tool_name]) {
          toolsStats[tc.tool_name] = {
            count: 0,
            total_duration_ms: 0,
            calls: [],
          }
        }
        toolsStats[tc.tool_name].count++
        toolsStats[tc.tool_name].total_duration_ms += tc.duration_ms || 0
        toolsStats[tc.tool_name].calls.push(tc)
      })
      
      return NextResponse.json({
        trace_id: traceId,
        tools_used: Array.from(uniqueTools),
        tool_calls: toolCalls,
        statistics: {
          total_tools: toolCalls.length,
          unique_tools: uniqueTools.size,
          total_duration_ms: totalDuration,
          average_duration_ms: averageDuration,
          tools_stats: toolsStats,
        },
      })
    } catch (sdkError: any) {
      console.error('[API Route /api/trace/[traceId]/tools] Erro ao buscar tools via SDK:', {
        message: sdkError.message,
        stack: sdkError.stack,
      })
      
      return NextResponse.json({
        trace_id: traceId,
        tools_used: [],
        tool_calls: [],
        statistics: {
          total_tools: 0,
          unique_tools: 0,
          total_duration_ms: 0,
          average_duration_ms: 0,
          tools_stats: {},
        },
        error: `Failed to fetch tools: ${sdkError.message || 'Unknown error'}`,
      })
    }
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]/tools] Erro:', {
      message: error.message,
      stack: error.stack,
    })
    return NextResponse.json({
      trace_id: (await params).traceId,
      tools_used: [],
      tool_calls: [],
      statistics: {
        total_tools: 0,
        unique_tools: 0,
        total_duration_ms: 0,
        average_duration_ms: 0,
        tools_stats: {},
      },
      error: error.message || 'Internal server error',
    }, { status: 500 })
  }
}
