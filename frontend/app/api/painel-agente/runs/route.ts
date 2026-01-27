import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient } from '@/app/lib/langgraph-client'

export const dynamic = 'force-dynamic'

/**
 * GET /api/painel-agente/runs
 * Busca runs do LangGraph Deployment usando SDK
 * 
 * Estratégia:
 * 1. Buscar todas as threads do deployment usando SDK
 * 2. Para cada thread, buscar seus runs usando SDK
 * 3. Agregar todos os runs em uma lista única
 * 
 * VERSÃO: 3.0 - Usa LangGraph SDK
 */
export async function GET(request: NextRequest) {
  try {
    const client = createLangGraphClient()
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 1000
    
    console.log('[Painel Agente API] ✅ VERSÃO 3.0 - Usando LangGraph SDK:', {
      limit,
      timestamp: new Date().toISOString(),
    })
    
    // Passo 1: Buscar todas as threads usando SDK
    let threads: any[] = []
    
    try {
      // Remover metadata: null - SDK não aceita null, usar objeto vazio ou omitir
      threads = await client.threads.search({
        limit: limit,
        offset: 0,
      })
      
      // Normalizar para array - SDK pode retornar array direto ou objeto com threads
      if (Array.isArray(threads)) {
        threads = threads
      } else if (threads && typeof threads === 'object') {
        threads = threads.threads || threads.data || []
      } else {
        threads = []
      }
      
      console.log('[Painel Agente API] Threads encontradas via SDK:', threads.length)
    } catch (threadsError: any) {
      console.error('[Painel Agente API] Erro ao buscar threads via SDK:', {
        message: threadsError.message,
        stack: threadsError.stack,
        status: threadsError.status || threadsError.statusCode,
        name: threadsError.name,
      })
      // Retornar array vazio em caso de erro
      return NextResponse.json({ runs: [] })
    }
    
    // Se não temos threads, retornar array vazio
    if (threads.length === 0) {
      console.log('[Painel Agente API] Nenhuma thread encontrada, retornando array vazio')
      return NextResponse.json({ runs: [] })
    }
    
    // Passo 2: Buscar runs de cada thread usando SDK
    const allRuns: any[] = []
    
    // Processar threads em paralelo (limitado a 10 por vez para não sobrecarregar)
    const batchSize = 10
    for (let i = 0; i < threads.length; i += batchSize) {
      const batch = threads.slice(i, i + batchSize)
      
      const batchPromises = batch.map(async (thread: any) => {
        // Validar thread_id antes de usar
        const threadId = thread.thread_id || thread.id
        if (!threadId || typeof threadId !== 'string') {
          console.warn('[Painel Agente API] Thread sem thread_id válido:', thread)
          return []
        }
        
        try {
          // Buscar runs e thread state em paralelo
          const [runs, threadState] = await Promise.all([
            client.runs.list(threadId, {
              limit: 100,
            }).catch(() => null),
            client.threads.getState(threadId).catch(() => null)
          ])
          
          // Normalizar para array - SDK pode retornar array direto ou objeto
          let runsArray: any[] = []
          if (runs) {
            if (Array.isArray(runs)) {
              runsArray = runs
            } else if (runs && typeof runs === 'object') {
              runsArray = runs.runs || runs.data || []
            }
          }
          
          // Extrair user_input do thread state
          let userInput = ''
          if (threadState?.values?.messages && Array.isArray(threadState.values.messages)) {
            const firstHumanMessage = threadState.values.messages.find((m: any) => 
              m.type === 'human' || m.role === 'user'
            )
            if (firstHumanMessage) {
              // Extrair conteúdo da mensagem
              if (typeof firstHumanMessage.content === 'string') {
                userInput = firstHumanMessage.content
              } else if (Array.isArray(firstHumanMessage.content)) {
                // Se content é array, pegar o primeiro item de texto
                const textContent = firstHumanMessage.content.find((c: any) => 
                  c.type === 'text' || typeof c === 'string'
                )
                userInput = typeof textContent === 'string' ? textContent : (textContent?.text || '')
              }
            }
          }
          
          // Adicionar thread_id e user_input a cada run
          return runsArray.map((run: any) => ({
            ...run,
            thread_id: threadId,
            user_input: userInput, // Adicionar user_input extraído do thread state
          }))
        } catch (error: any) {
          console.error(`[Painel Agente API] Erro ao buscar runs da thread ${threadId} via SDK:`, {
            message: error.message,
            stack: error.stack,
            status: error.status || error.statusCode,
            threadId,
          })
          return []
        }
      })
      
      const batchResults = await Promise.all(batchPromises)
      allRuns.push(...batchResults.flat())
      
      // Limitar total de runs
      if (allRuns.length >= limit) {
        break
      }
    }
    
    // Limitar resultados
    const runs = allRuns.slice(0, limit)
    
    console.log('[Painel Agente API] Total de runs encontrados via SDK:', runs.length)
    
    return NextResponse.json({ runs })
  } catch (error: any) {
    console.error('[Painel Agente API] Erro ao buscar runs:', {
      message: error.message,
      stack: error.stack,
      name: error.name,
      status: error.status || error.statusCode,
    })
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        runs: [] // Retornar array vazio em caso de erro
      },
      { status: 500 }
    )
  }
}
