import { NextRequest, NextResponse } from 'next/server'

function getLangSmithConfig() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() || ''
  const apiKey = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY?.trim() || ''
  
  if (!apiUrl) {
    throw new Error('NEXT_PUBLIC_API_URL não configurada')
  }
  
  if (!apiKey) {
    throw new Error('NEXT_PUBLIC_LANGSMITH_API_KEY não configurada')
  }
  
  return { apiUrl, apiKey }
}

function createHeaders(apiKey: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'x-api-key': apiKey,
  }
}

/**
 * GET /api/studio/assistants/[assistantId]/graph
 * Obtém a estrutura do grafo de um assistente do LangGraph Deployment
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ assistantId: string }> }
) {
  try {
    const { assistantId } = await params
    const { apiUrl, apiKey } = getLangSmithConfig()
    
    const response = await fetch(`${apiUrl}/assistants/${assistantId}/graph`, {
      method: 'GET',
      headers: createHeaders(apiKey),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      
      // Se endpoint não existir, retornar estrutura padrão baseada no grafo conhecido
      if (response.status === 404) {
        console.warn(`[Studio API] Endpoint /assistants/${assistantId}/graph não encontrado, usando estrutura padrão`)
        return NextResponse.json(getDefaultGraphStructure(assistantId))
      }
      
      return NextResponse.json(
        { error: 'Failed to fetch graph structure', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[Studio API] Erro ao obter estrutura do grafo:', error)
    
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
