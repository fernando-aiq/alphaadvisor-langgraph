import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

function getLangSmithConfig() {
  const apiKey = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY?.trim() || ''
  const projectName = process.env.NEXT_PUBLIC_LANGSMITH_PROJECT_NAME?.trim() || ''
  
  if (!apiKey) {
    throw new Error('NEXT_PUBLIC_LANGSMITH_API_KEY não configurada')
  }
  
  return { apiKey, projectName }
}

function createHeaders(apiKey: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'x-api-key': apiKey,
  }
}

/**
 * GET /api/painel-agente/runs
 * Busca runs diretamente do LangSmith usando a API REST
 */
export async function GET(request: NextRequest) {
  try {
    const { apiKey, projectName } = getLangSmithConfig()
    const searchParams = request.nextUrl.searchParams
    
    // Construir query params para a API do LangSmith
    const queryParams = new URLSearchParams()
    
    // Parâmetros suportados pela API do LangSmith
    if (searchParams.get('limit')) {
      queryParams.append('limit', searchParams.get('limit')!)
    } else {
      queryParams.append('limit', '1000') // Default
    }
    
    if (searchParams.get('offset')) {
      queryParams.append('offset', searchParams.get('offset')!)
    }
    
    // Project name - usar da query string ou variável de ambiente
    const finalProjectName = searchParams.get('project_name') || projectName
    if (finalProjectName) {
      queryParams.append('project_name', finalProjectName)
    }
    
    if (searchParams.get('start_time')) {
      queryParams.append('start_time', searchParams.get('start_time')!)
    }
    
    if (searchParams.get('end_time')) {
      queryParams.append('end_time', searchParams.get('end_time')!)
    }
    
    // URL da API do LangSmith
    const langSmithUrl = `https://api.smith.langchain.com/v1/runs${queryParams.toString() ? `?${queryParams}` : ''}`
    
    console.log('[Painel Agente API] Buscando runs do LangSmith:', langSmithUrl)
    
    const response = await fetch(langSmithUrl, {
      method: 'GET',
      headers: createHeaders(apiKey),
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      console.error('[Painel Agente API] Erro ao buscar runs:', {
        status: response.status,
        statusText: response.statusText,
        errorText,
      })
      
      // Se for 404 ou 405, retornar array vazio (endpoint pode não existir)
      if (response.status === 404 || response.status === 405) {
        return NextResponse.json({ runs: [] })
      }
      
      return NextResponse.json(
        { error: 'Failed to fetch runs from LangSmith', details: errorText },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    
    // A API do LangSmith retorna runs em diferentes formatos
    // Pode ser um array direto ou um objeto com propriedade 'runs' ou 'data'
    let runs: any[] = []
    
    if (Array.isArray(data)) {
      runs = data
    } else if (data.runs && Array.isArray(data.runs)) {
      runs = data.runs
    } else if (data.data && Array.isArray(data.data)) {
      runs = data.data
    } else if (data.items && Array.isArray(data.items)) {
      runs = data.items
    }
    
    console.log('[Painel Agente API] Resposta do LangSmith:', {
      dataType: Array.isArray(data) ? 'array' : typeof data,
      hasRuns: !!(data as any).runs,
      hasData: !!(data as any).data,
      hasItems: !!(data as any).items,
      runsCount: runs.length,
      sampleKeys: !Array.isArray(data) ? Object.keys(data).slice(0, 5) : []
    })
    
    return NextResponse.json({ runs })
  } catch (error: any) {
    console.error('[Painel Agente API] Erro ao buscar runs do LangSmith:', error)
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error',
        runs: [] // Retornar array vazio em caso de erro
      },
      { status: 500 }
    )
  }
}
