/**
 * Cliente para comunicação com a API do LangSmith Deployment
 * Todas as requisições devem passar pelas API routes do Next.js para segurança
 */

export interface Thread {
  thread_id: string
  created_at?: string
  metadata?: Record<string, any>
}

export interface Run {
  run_id: string
  thread_id: string
  assistant_id: string
  status: 'pending' | 'running' | 'completed' | 'error'
  created_at?: string
  started_at?: string
  ended_at?: string
  error?: string
  metadata?: Record<string, any>
}

export interface ThreadState {
  values: {
    messages: Array<{
      type: 'human' | 'ai' | 'tool'
      content: string | any
      id?: string
      tool_calls?: Array<{
        id: string
        name: string
        args: Record<string, any>
      }>
      tool_call_id?: string
    }>
  }
  next: string[]
  config?: Record<string, any>
  metadata?: Record<string, any>
}

export interface ListThreadsParams {
  limit?: number
  offset?: number
}

export interface ListRunsParams {
  limit?: number
  offset?: number
}

class LangSmithStudioClient {
  private baseUrl: string

  constructor() {
    // Usar API routes do Next.js como proxy
    this.baseUrl = '/api/studio'
  }

  /**
   * Lista todas as threads
   * NOTA: A API do LangGraph Deployment pode não suportar este endpoint.
   * Este método pode retornar erro 404 ou 405.
   */
  async listThreads(params?: ListThreadsParams): Promise<Thread[]> {
    try {
      const queryParams = new URLSearchParams()
      if (params?.limit) queryParams.append('limit', params.limit.toString())
      if (params?.offset) queryParams.append('offset', params.offset.toString())

      const url = `${this.baseUrl}/threads${queryParams.toString() ? `?${queryParams}` : ''}`
      const response = await fetch(url)
      
      if (!response.ok) {
        // Se não suportar, retornar array vazio
        if (response.status === 404 || response.status === 405) {
          return []
        }
        throw new Error(`Failed to list threads: ${response.statusText}`)
      }

      const data = await response.json()
      return data.threads || []
    } catch (error: any) {
      // Se der erro, retornar array vazio (endpoint pode não existir)
      console.warn('listThreads não disponível:', error.message)
      return []
    }
  }

  /**
   * Obtém o estado completo de uma thread
   */
  async getThreadState(threadId: string): Promise<ThreadState> {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/state`)
    
    if (!response.ok) {
      throw new Error(`Failed to get thread state: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Lista runs de uma thread
   */
  async listRuns(threadId: string, params?: ListRunsParams): Promise<Run[]> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())

    const url = `${this.baseUrl}/threads/${threadId}/runs${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Failed to list runs: ${response.statusText}`)
    }

    const data = await response.json()
    return data.runs || []
  }

  /**
   * Obtém detalhes de um run específico
   */
  async getRunDetails(threadId: string, runId: string): Promise<Run> {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/runs/${runId}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get run details: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Cria uma nova thread
   */
  async createThread(input: { messages?: Array<{ role: string; content: string }> }): Promise<Thread> {
    const response = await fetch(`${this.baseUrl}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to create thread: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Cria um novo run em uma thread
   */
  async createRun(
    threadId: string,
    assistantId: string,
    input: { messages?: Array<{ role: string; content: string }> }
  ): Promise<Run> {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: assistantId,
        input,
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to create run: ${response.statusText}`)
    }

    return response.json()
  }
}

// Exportar instância singleton
export const langSmithClient = new LangSmithStudioClient()
