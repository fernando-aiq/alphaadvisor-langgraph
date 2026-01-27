import { NextRequest, NextResponse } from 'next/server'
import { createLangGraphClient, getLangGraphConfig } from '@/app/lib/langgraph-client'

/**
 * GET /api/studio/assistants/[assistantId]/graph
 * Obtém a estrutura do grafo de um assistente do LangGraph Deployment
 * Tenta SDK primeiro, depois HTTP direto, depois fallback padrão
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ assistantId: string }> }
) {
  try {
    const { assistantId } = await params
    const client = createLangGraphClient()
    const { apiUrl, apiKey } = getLangGraphConfig()
    
    // Estratégia 1: Tentar obter via SDK
    try {
      const assistant = await client.assistants.get(assistantId)
      
      // Se o assistant tiver estrutura de grafo, retornar
      if (assistant && (assistant as any).graph) {
        console.log(`[Studio API] Grafo obtido via SDK para assistant ${assistantId}`)
        return NextResponse.json((assistant as any).graph)
      }
      
      console.log(`[Studio API] Assistant ${assistantId} obtido via SDK mas sem estrutura de grafo, tentando HTTP direto`)
    } catch (sdkError: any) {
      console.warn('[Studio API] Erro ao obter assistant via SDK, tentando HTTP direto:', {
        message: sdkError.message,
        status: sdkError.status || sdkError.statusCode,
      })
    }
    
    // Estratégia 2: Tentar HTTP direto para endpoint /graph
    try {
      const graphUrl = `${apiUrl}/assistants/${assistantId}/graph`
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      if (apiKey) {
        headers['x-api-key'] = apiKey
      }
      
      const response = await fetch(graphUrl, {
        method: 'GET',
        headers,
      })
      
      if (response.ok) {
        const graphData = await response.json()
        console.log(`[Studio API] Grafo obtido via HTTP direto para assistant ${assistantId}`)
        return NextResponse.json(graphData)
      } else {
        console.warn(`[Studio API] Endpoint /graph retornou ${response.status} para assistant ${assistantId}`)
      }
    } catch (httpError: any) {
      console.warn('[Studio API] Erro ao buscar grafo via HTTP direto:', {
        message: httpError.message,
      })
    }
    
    // Estratégia 3: Usar estrutura padrão como fallback
    console.warn(`[Studio API] Usando estrutura padrão do grafo para assistant ${assistantId}`)
    return NextResponse.json(getDefaultGraphStructure(assistantId))
  } catch (error: any) {
    console.error('[Studio API] Erro ao obter estrutura do grafo:', {
      message: error.message,
      stack: error.stack,
      name: error.name,
    })
    
    // Em caso de erro, retornar estrutura padrão
    try {
      const { assistantId } = await params
      return NextResponse.json(getDefaultGraphStructure(assistantId))
    } catch {
      return NextResponse.json(
        { error: error.message || 'Internal server error' },
        { status: 500 }
      )
    }
  }
}

/**
 * Retorna estrutura padrão do grafo baseada no código conhecido
 * Fallback quando a API não retorna estrutura completa
 */
function getDefaultGraphStructure(assistantId: string) {
  // Estrutura baseada em langgraph-app/src/agent/graph_chat.py
  return {
    nodes: [
      {
        id: 'init',
        name: 'init',
        type: 'init',
        label: 'Inicialização',
      },
      {
        id: 'agent',
        name: 'agent',
        type: 'agent',
        label: 'Agente',
      },
      {
        id: 'tools',
        name: 'tools',
        type: 'tool',
        label: 'Ferramentas',
      },
      {
        id: 'end',
        name: 'end',
        type: 'end',
        label: 'Fim',
      },
    ],
    edges: [
      {
        source: 'START',
        target: 'init',
      },
      {
        source: 'init',
        target: 'agent',
      },
      {
        source: 'agent',
        target: 'tools',
        condition: 'has_tool_calls',
      },
      {
        source: 'agent',
        target: 'end',
        condition: 'no_tool_calls',
      },
      {
        source: 'tools',
        target: 'agent',
      },
      {
        source: 'end',
        target: 'END',
      },
    ],
    entry_point: 'init',
  }
}
