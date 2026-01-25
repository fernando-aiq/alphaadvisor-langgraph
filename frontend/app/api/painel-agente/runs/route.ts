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
        url: langSmithUrl,
        hasProjectName: !!finalProjectName,
      })
      
      // Se for 404 ou 405, tentar endpoint de traces como fallback
      if (response.status === 404 || response.status === 405) {
        console.log('[Painel Agente API] Endpoint runs não disponível, tentando traces...')
        try {
          const tracesUrl = `https://api.smith.langchain.com/v1/traces${queryParams.toString() ? `?${queryParams}` : ''}`
          const tracesResponse = await fetch(tracesUrl, {
            method: 'GET',
            headers: createHeaders(apiKey),
          })
          
          if (tracesResponse.ok) {
            const tracesData = await tracesResponse.json()
            let runs: any[] = []
            if (Array.isArray(tracesData)) {
              runs = tracesData
            } else if (tracesData.traces && Array.isArray(tracesData.traces)) {
              runs = tracesData.traces
            } else if (tracesData.data && Array.isArray(tracesData.data)) {
              runs = tracesData.data
            }
            console.log('[Painel Agente API] Traces encontrados via fallback:', runs.length)
            return NextResponse.json({ runs })
          }
        } catch (traceError) {
          console.warn('[Painel Agente API] Erro ao buscar traces como fallback:', traceError)
        }
        return NextResponse.json({ runs: [], debug: { error: errorText, status: response.status } })
      }
      
      return NextResponse.json(
        { error: 'Failed to fetch runs from LangSmith', details: errorText, runs: [] },
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
    } else if (data.results && Array.isArray(data.results)) {
      runs = data.results
    }
    
    console.log('[Painel Agente API] Resposta do LangSmith:', {
      dataType: Array.isArray(data) ? 'array' : typeof data,
      hasRuns: !!(data as any).runs,
      hasData: !!(data as any).data,
      hasItems: !!(data as any).items,
      hasResults: !!(data as any).results,
      runsCount: runs.length,
      sampleKeys: !Array.isArray(data) ? Object.keys(data).slice(0, 10) : [],
      sampleData: !Array.isArray(data) ? JSON.stringify(data).substring(0, 500) : 'array'
    })
    
    // Se não encontrou runs e a resposta foi bem-sucedida mas vazia, tentar endpoint de traces
    if (runs.length === 0 && response.ok) {
      console.log('[Painel Agente API] Nenhum run encontrado, tentando endpoint de traces...')
      try {
        const tracesUrl = `https://api.smith.langchain.com/v1/traces${queryParams.toString() ? `?${queryParams}` : ''}`
        console.log('[Painel Agente API] Tentando traces:', tracesUrl)
        
        const tracesResponse = await fetch(tracesUrl, {
          method: 'GET',
          headers: createHeaders(apiKey),
        })
        
        if (tracesResponse.ok) {
          const tracesData = await tracesResponse.json()
          // Traces podem ser convertidos para runs
          if (Array.isArray(tracesData)) {
            runs = tracesData
          } else if (tracesData.traces && Array.isArray(tracesData.traces)) {
            runs = tracesData.traces
          } else if (tracesData.data && Array.isArray(tracesData.data)) {
            runs = tracesData.data
          }
          console.log('[Painel Agente API] Traces encontrados:', runs.length)
        }
      } catch (traceError) {
        console.warn('[Painel Agente API] Erro ao buscar traces:', traceError)
      }
    }
    
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
