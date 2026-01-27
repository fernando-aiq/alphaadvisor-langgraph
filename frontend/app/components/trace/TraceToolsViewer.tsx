'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import Card from '../Card'

interface ToolCall {
  tool_name: string
  timestamp: string
  input: any
  output: any
  duration_ms?: number
  error?: string
}

interface ToolsData {
  trace_id: string
  tools_used: string[]
  tool_calls: ToolCall[]
  statistics: {
    total_tools: number
    unique_tools: number
    total_duration_ms: number
    average_duration_ms: number
    tools_stats: Record<string, {
      count: number
      total_duration_ms: number
      calls: ToolCall[]
    }>
  }
}

interface TraceToolsViewerProps {
  traceId: string
}

const getApiUrl = () => {
  // Para endpoints de trace, sempre usar API routes do Next.js (relativo)
  // Não usar NEXT_PUBLIC_API_URL que é para LangGraph Deployment
  return ''
}

const getToolDescription = (toolName: string): string => {
  const descriptions: Record<string, string> = {
    'obter_carteira': 'Obtém dados completos da carteira do cliente, incluindo ativos, valores e distribuição',
    'analisar_adequacao': 'Analisa se a carteira está adequada ao perfil de risco do cliente',
    'analisar_alinhamento_objetivos': 'Verifica alinhamento da carteira com objetivos de curto/médio/longo prazo',
    'analisar_diversificacao': 'Analisa a diversificação da carteira entre diferentes classes de ativos',
    'recomendar_rebalanceamento': 'Recomenda ajustes na alocação de ativos para melhor adequação',
    'buscar_oportunidades': 'Busca oportunidades de investimento baseadas no perfil e objetivos',
    'calcular_projecao': 'Calcula projeções futuras baseadas em aportes e rentabilidade esperada',
    'llm_with_carteira': 'Chamada direta ao LLM com contexto da carteira'
  }
  return descriptions[toolName] || 'Ferramenta utilizada durante o processamento'
}

export default function TraceToolsViewer({ traceId }: TraceToolsViewerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [toolsData, setToolsData] = useState<ToolsData | null>(null)
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set())
  const [filter, setFilter] = useState<string>('all') // 'all', 'unique', 'by_name'

  useEffect(() => {
    const loadTools = async () => {
      setLoading(true)
      setError(null)
      const apiUrl = getApiUrl()

      try {
        const base = apiUrl || ''
        const response = await axios.get(`${base}/api/trace/${traceId}/tools`)
        setToolsData(response.data)
      } catch (err: any) {
        console.error('Erro ao carregar tools:', err)
        setError(err.response?.data?.error || err.message || 'Erro ao carregar tools')
      } finally {
        setLoading(false)
      }
    }

    if (traceId) {
      loadTools()
    }
  }, [traceId])

  const toggleTool = (index: number) => {
    const newExpanded = new Set(expandedTools)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedTools(newExpanded)
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return timestamp
    }
  }

  if (loading) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Carregando tools...</div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ color: '#F44336' }}>Erro: {error}</div>
      </Card>
    )
  }

  if (!toolsData) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Nenhum dado de tools disponível</div>
      </Card>
    )
  }

  const { tool_calls, statistics } = toolsData

  // Filtrar tool calls
  let filteredToolCalls = tool_calls
  if (filter === 'unique') {
    // Mostrar apenas uma chamada de cada tool
    const seen = new Set<string>()
    filteredToolCalls = tool_calls.filter(tc => {
      if (seen.has(tc.tool_name)) return false
      seen.add(tc.tool_name)
      return true
    })
  }

  return (
    <Card style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ margin: 0, marginBottom: '1rem' }}>Tools Utilizadas</h3>
        
        {/* Estatísticas */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '1rem',
          marginBottom: '1rem'
        }}>
          <div style={{ padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Total de Chamadas</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{statistics.total_tools}</div>
          </div>
          <div style={{ padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Tools Únicas</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{statistics.unique_tools}</div>
          </div>
          <div style={{ padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Tempo Total</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{formatDuration(statistics.total_duration_ms)}</div>
          </div>
          <div style={{ padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Tempo Médio</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{formatDuration(statistics.average_duration_ms)}</div>
          </div>
        </div>

        {/* Filtros */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <button
            onClick={() => setFilter('all')}
            style={{
              padding: '0.5rem 1rem',
              border: '1px solid #e0e0e0',
              borderRadius: '4px',
              backgroundColor: filter === 'all' ? '#2196F3' : 'white',
              color: filter === 'all' ? 'white' : '#333',
              cursor: 'pointer'
            }}
          >
            Todas ({tool_calls.length})
          </button>
          <button
            onClick={() => setFilter('unique')}
            style={{
              padding: '0.5rem 1rem',
              border: '1px solid #e0e0e0',
              borderRadius: '4px',
              backgroundColor: filter === 'unique' ? '#2196F3' : 'white',
              color: filter === 'unique' ? 'white' : '#333',
              cursor: 'pointer'
            }}
          >
            Únicas ({statistics.unique_tools})
          </button>
        </div>
      </div>

      {/* Lista de Tools */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {filteredToolCalls.map((toolCall, index) => {
          const isExpanded = expandedTools.has(index)
          const toolStats = statistics.tools_stats[toolCall.tool_name]
          const callCount = toolStats?.count || 1

          return (
            <div
              key={index}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                backgroundColor: '#f9f9f9',
                overflow: 'hidden'
              }}
            >
              <div
                style={{
                  padding: '1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  justifyContent: 'space-between'
                }}
                onClick={() => toggleTool(index)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1 }}>
                  <span style={{ fontSize: '1.2rem' }}>🔧</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {toolCall.tool_name}
                      {callCount > 1 && (
                        <span style={{ 
                          fontSize: '0.75rem', 
                          padding: '0.125rem 0.5rem', 
                          backgroundColor: '#FF9800', 
                          color: 'white', 
                          borderRadius: '12px' 
                        }}>
                          {callCount}x
                        </span>
                      )}
                      <span style={{ fontSize: '0.75rem', color: '#999' }} title={getToolDescription(toolCall.tool_name)}>ℹ️</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                      {getToolDescription(toolCall.tool_name)}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: '#666' }}>
                  {toolCall.duration_ms && (
                    <span>{formatDuration(toolCall.duration_ms)}</span>
                  )}
                  {toolCall.error && (
                    <span style={{ color: '#F44336' }}>⚠️ Erro</span>
                  )}
                  <span>{formatTimestamp(toolCall.timestamp)}</span>
                  <span style={{ fontSize: '1.2rem' }}>
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {isExpanded && (
                <div style={{ padding: '1rem', borderTop: '1px solid #e0e0e0', backgroundColor: '#fff' }}>
                  {toolCall.input && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Input:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Dados de entrada passados para a tool">ℹ️</span>
                      </div>
                      <pre style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: '4px', 
                        fontSize: '0.85rem',
                        overflow: 'auto',
                        maxHeight: '200px'
                      }}>
                        {JSON.stringify(toolCall.input, null, 2)}
                      </pre>
                    </div>
                  )}
                  {toolCall.output && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Output:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Dados de saída retornados pela tool">ℹ️</span>
                      </div>
                      <pre style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: '4px', 
                        fontSize: '0.85rem',
                        overflow: 'auto',
                        maxHeight: '200px'
                      }}>
                        {JSON.stringify(toolCall.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {toolCall.error && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#F44336' }}>
                        Erro:
                      </div>
                      <div style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#ffebee', 
                        borderRadius: '4px', 
                        fontSize: '0.85rem',
                        color: '#F44336'
                      }}>
                        {toolCall.error}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {filteredToolCalls.length === 0 && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
          Nenhuma tool foi utilizada neste trace
        </div>
      )}
    </Card>
  )
}

