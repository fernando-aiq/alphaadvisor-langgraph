'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Card from '../components/Card'
import '../globals.css'
import { 
  FiActivity, 
  FiUsers, 
  FiAlertCircle, 
  FiTool, 
  FiArrowRight,
  FiFilter,
  FiDownload,
  FiShield,
  FiFileText,
  FiEye,
  FiCalendar,
  FiLoader
} from 'react-icons/fi'

// Função para obter configuração do LangSmith
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

interface Trace {
  trace_id: string
  timestamp: string
  user_input: string
  intent?: string
  route?: string
  status: string
  client_id?: string
  client_name?: string
  tool_calls_count: number
  has_handoff: boolean
  errors_count: number
}

interface Handoff {
  trace_id: string
  timestamp: string
  reason: string
  rule: string
  client_id?: string
  client_name?: string
  user_input: string
  intent?: string
  route?: string
}

interface Summary {
  total_traces: number
  total_tool_calls: number
  total_handoffs: number
  total_errors: number
  status_counts: Record<string, number>
  intent_counts: Record<string, number>
  route_counts: Record<string, number>
  top_intents: Array<{ intent: string; count: number }>
}

interface Client {
  client_id: string
  client_name: string
  traces_count: number
}

export default function PainelDoAgente() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'handoffs' | 'compliance'>('overview')
  const [error, setError] = useState<string | null>(null)
  
  // Dados
  const [summary, setSummary] = useState<Summary | null>(null)
  const [traces, setTraces] = useState<Trace[]>([])
  const [handoffs, setHandoffs] = useState<Handoff[]>([])
  const [clients, setClients] = useState<Client[]>([])
  
  // Filtros
  const [selectedClient, setSelectedClient] = useState<string>('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [selectedIntent, setSelectedIntent] = useState<string>('')
  const [selectedRoute, setSelectedRoute] = useState<string>('')
  const [hasHandoffFilter, setHasHandoffFilter] = useState<string>('')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  
  // Cache para evitar múltiplas chamadas
  const [threadsCache, setThreadsCache] = useState<any[]>([])
  const [runsCache, setRunsCache] = useState<Record<string, any[]>>({})
  const [statesCache, setStatesCache] = useState<Record<string, any>>({})

  useEffect(() => {
    loadInitialData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (activeTab === 'overview') {
      loadSummary()
    } else if (activeTab === 'activity') {
      loadTraces()
    } else if (activeTab === 'handoffs') {
      loadHandoffs()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, selectedClient, selectedStatus, selectedIntent, selectedRoute, hasHandoffFilter, startDate, endDate])

  // Função principal para buscar e agregar dados do LangSmith
  const aggregateData = async () => {
    console.log('[Painel do Agente] Iniciando agregação de dados...')
    
    try {
      // 1. Buscar runs diretamente do LangSmith usando a nova rota API
      console.log('[Painel do Agente] Buscando runs do LangSmith...')
      const runsResponse = await fetch(`/api/painel-agente/runs?limit=1000`)
      
      if (!runsResponse.ok) {
        const errorText = await runsResponse.text().catch(() => 'Unknown error')
        console.error('[Painel do Agente] Erro ao buscar runs:', {
          status: runsResponse.status,
          statusText: runsResponse.statusText,
          errorText,
        })
        // Se retornar 404 ou 405, retornar dados vazios
        if (runsResponse.status === 404 || runsResponse.status === 405) {
          console.warn('[Painel do Agente] Endpoint de runs não disponível, retornando dados vazios')
          return {
            summary: {
              total_traces: 0,
              total_tool_calls: 0,
              total_handoffs: 0,
              total_errors: 0,
              status_counts: {},
              intent_counts: {},
              route_counts: {},
              top_intents: [],
            },
            traces: [],
            handoffs: [],
            clients: [],
          }
        }
        throw new Error(`Failed to fetch runs: ${runsResponse.status} ${runsResponse.statusText}`)
      }
      
      const runsData = await runsResponse.json()
      const runs = Array.isArray(runsData.runs) ? runsData.runs : (runsData.runs || [])
      console.log('[Painel do Agente] Runs encontrados:', runs.length)
      setRunsCache({ all: runs })
      
      if (runs.length === 0) {
        console.warn('[Painel do Agente] Nenhum run encontrado')
        return {
          summary: {
            total_traces: 0,
            total_tool_calls: 0,
            total_handoffs: 0,
            total_errors: 0,
            status_counts: {},
            intent_counts: {},
            route_counts: {},
            top_intents: [],
          },
          traces: [],
          handoffs: [],
          clients: [],
        }
      }
      
      // 2. Agregar dados dos runs para criar traces, summary e handoffs
      console.log('[Painel do Agente] Agregando dados para criar traces...')
      const traces: Trace[] = []
      const handoffs: Handoff[] = []
      
      runs.forEach((run: any) => {
        // Extrair informações do run do LangSmith
        const runId = run.run_id || run.id || run.runId
        const traceId = run.trace_id || runId
        if (!runId) {
          console.warn('[Painel do Agente] Run sem ID válido:', run)
          return
        }
        
        // Extrair metadata do run
        const metadata = run.metadata || run.extra || {}
        const inputs = run.inputs || {}
        const outputs = run.outputs || {}
        
        // Tentar extrair user input de diferentes lugares
        // Priorizar user_input que vem da API (extraído do thread state)
        let userInput = run.user_input || ''
        
        // Fallback: tentar extrair de outras fontes se user_input não estiver disponível
        if (!userInput) {
          if (inputs.messages && Array.isArray(inputs.messages) && inputs.messages.length > 0) {
            const firstMessage = inputs.messages[0]
            userInput = typeof firstMessage === 'string' ? firstMessage : (firstMessage.content || firstMessage.text || '')
          } else if (inputs.input) {
            userInput = typeof inputs.input === 'string' ? inputs.input : JSON.stringify(inputs.input)
          } else if (inputs.query) {
            userInput = inputs.query
          } else if (metadata.user_input) {
            userInput = metadata.user_input
          }
        }
        
        // Determinar se há handoff
        const hasHandoff = metadata.has_handoff === true || 
                          metadata.handoff === true ||
                          (metadata.next && Array.isArray(metadata.next) && metadata.next.some((n: any) => String(n).includes('handoff')))
        
        // Contar tool calls
        let toolCallsCount = 0
        if (run.child_runs && Array.isArray(run.child_runs)) {
          toolCallsCount = run.child_runs.filter((r: any) => r.run_type === 'tool').length
        } else if (metadata.tool_calls_count) {
          toolCallsCount = metadata.tool_calls_count
        }
        
        // Status do run
        const status = run.status || (run.error ? 'error' : 'completed')
        const hasError = status === 'error' || !!run.error
        
        // Criar trace
        const trace: Trace = {
          trace_id: traceId,
          timestamp: run.start_time || run.created_at || run.timestamp || new Date().toISOString(),
          user_input: userInput || 'Sem input',
          intent: metadata.intent || inputs.intent,
          route: metadata.route || inputs.route,
          status: status,
          client_id: metadata.client_id,
          client_name: metadata.client_name,
          tool_calls_count: toolCallsCount,
          has_handoff: hasHandoff,
          errors_count: hasError ? 1 : 0,
        }
        
        traces.push(trace)
        
        // Se há handoff, criar entrada de handoff
        if (hasHandoff) {
          const handoff: Handoff = {
            trace_id: trace.trace_id,
            timestamp: trace.timestamp,
            reason: metadata.handoff_reason || metadata.reason || 'Regra de handoff acionada',
            rule: metadata.handoff_rule || metadata.rule || 'Regra desconhecida',
            client_id: trace.client_id,
            client_name: trace.client_name,
            user_input: trace.user_input,
            intent: trace.intent,
            route: trace.route,
          }
          handoffs.push(handoff)
        }
      })
      
      console.log('[Painel do Agente] Traces criados:', traces.length)
      console.log('[Painel do Agente] Handoffs encontrados:', handoffs.length)
      
      // 5. Criar summary agregado
      const statusCounts: Record<string, number> = {}
      const intentCounts: Record<string, number> = {}
      const routeCounts: Record<string, number> = {}
      let totalToolCalls = 0
      let totalErrors = 0
      
      traces.forEach(trace => {
        statusCounts[trace.status] = (statusCounts[trace.status] || 0) + 1
        if (trace.intent) {
          intentCounts[trace.intent] = (intentCounts[trace.intent] || 0) + 1
        }
        if (trace.route) {
          routeCounts[trace.route] = (routeCounts[trace.route] || 0) + 1
        }
        totalToolCalls += trace.tool_calls_count
        totalErrors += trace.errors_count
      })
      
      const topIntents = Object.entries(intentCounts)
        .map(([intent, count]) => ({ intent, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
      
      const summary: Summary = {
        total_traces: traces.length,
        total_tool_calls: totalToolCalls,
        total_handoffs: handoffs.length,
        total_errors: totalErrors,
        status_counts: statusCounts,
        intent_counts: intentCounts,
        route_counts: routeCounts,
        top_intents: topIntents,
      }
      
      // 6. Criar lista de clientes
      const clientMap: Record<string, { client_id: string; client_name: string; traces_count: number }> = {}
      traces.forEach(trace => {
        const clientId = trace.client_id || 'unknown'
        const clientName = trace.client_name || clientId
        if (!clientMap[clientId]) {
          clientMap[clientId] = {
            client_id: clientId,
            client_name: clientName,
            traces_count: 0,
          }
        }
        clientMap[clientId].traces_count++
      })
      
      const clients = Object.values(clientMap)
      
      console.log('[Painel do Agente] Agregação concluída:', {
        traces: traces.length,
        handoffs: handoffs.length,
        clients: clients.length,
        summary: {
          total_traces: summary.total_traces,
          total_tool_calls: summary.total_tool_calls,
          total_handoffs: summary.total_handoffs,
          total_errors: summary.total_errors,
        }
      })
      
      return { summary, traces, handoffs, clients }
    } catch (error: any) {
      console.error('[Painel do Agente] Erro ao agregar dados do LangSmith:', error)
      console.error('[Painel do Agente] Stack trace:', error.stack)
      // Retornar dados vazios em caso de erro
      return {
        summary: {
          total_traces: 0,
          total_tool_calls: 0,
          total_handoffs: 0,
          total_errors: 0,
          status_counts: {},
          intent_counts: {},
          route_counts: {},
          top_intents: [],
        },
        traces: [],
        handoffs: [],
        clients: [],
      }
    }
  }

  const loadInitialData = async () => {
    try {
      setError(null)
      setLoading(true)
      const data = await aggregateData()
      setSummary(data.summary)
      setTraces(data.traces)
      setHandoffs(data.handoffs)
      setClients(data.clients)
      
      if (data.traces.length === 0 && data.summary.total_traces === 0) {
        setError('Nenhum dado encontrado. Verifique se há runs no LangSmith.')
      }
    } catch (error: any) {
      console.error('Erro ao carregar dados iniciais:', error)
      setError(error.message || 'Erro ao carregar dados do LangSmith. Verifique as configurações da API.')
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async () => {
    try {
      setError(null)
      const data = await aggregateData()
      setSummary(data.summary)
    } catch (error: any) {
      console.error('Erro ao carregar resumo:', error)
      setError(error.message || 'Erro ao carregar resumo')
    }
  }

  const loadTraces = async () => {
    try {
      setError(null)
      const data = await aggregateData()
      let filteredTraces = data.traces
      
      // Aplicar filtros
      if (selectedClient) {
        filteredTraces = filteredTraces.filter(t => t.client_id === selectedClient)
      }
      if (selectedStatus) {
        filteredTraces = filteredTraces.filter(t => t.status === selectedStatus)
      }
      if (selectedIntent) {
        filteredTraces = filteredTraces.filter(t => t.intent?.includes(selectedIntent))
      }
      if (selectedRoute) {
        filteredTraces = filteredTraces.filter(t => t.route === selectedRoute)
      }
      if (hasHandoffFilter) {
        const hasHandoff = hasHandoffFilter === 'true'
        filteredTraces = filteredTraces.filter(t => t.has_handoff === hasHandoff)
      }
      if (startDate) {
        filteredTraces = filteredTraces.filter(t => new Date(t.timestamp) >= new Date(startDate))
      }
      if (endDate) {
        filteredTraces = filteredTraces.filter(t => new Date(t.timestamp) <= new Date(endDate))
      }
      
      setTraces(filteredTraces.slice(0, 50))
    } catch (error: any) {
      console.error('Erro ao carregar traces:', error)
      setError(error.message || 'Erro ao carregar traces')
    }
  }

  const loadHandoffs = async () => {
    try {
      setError(null)
      const data = await aggregateData()
      let filteredHandoffs = data.handoffs
      
      // Aplicar filtros
      if (selectedClient) {
        filteredHandoffs = filteredHandoffs.filter(h => h.client_id === selectedClient)
      }
      if (startDate) {
        filteredHandoffs = filteredHandoffs.filter(h => new Date(h.timestamp) >= new Date(startDate))
      }
      if (endDate) {
        filteredHandoffs = filteredHandoffs.filter(h => new Date(h.timestamp) <= new Date(endDate))
      }
      
      setHandoffs(filteredHandoffs.slice(0, 50))
    } catch (error: any) {
      console.error('Erro ao carregar handoffs:', error)
      setError(error.message || 'Erro ao carregar handoffs')
    }
  }

  const handleExportCompliance = async () => {
    try {
      const data = await aggregateData()
      let filteredTraces = data.traces
      
      // Aplicar filtros
      if (selectedClient) {
        filteredTraces = filteredTraces.filter(t => t.client_id === selectedClient)
      }
      if (startDate) {
        filteredTraces = filteredTraces.filter(t => new Date(t.timestamp) >= new Date(startDate))
      }
      if (endDate) {
        filteredTraces = filteredTraces.filter(t => new Date(t.timestamp) <= new Date(endDate))
      }
      
      // Criar CSV
      const headers = ['Trace ID', 'Timestamp', 'Cliente', 'Input', 'Intent', 'Route', 'Status', 'Tool Calls', 'Handoff', 'Erros']
      const rows = filteredTraces.map(t => [
        t.trace_id,
        t.timestamp,
        t.client_name || t.client_id || 'N/A',
        t.user_input || '',
        t.intent || 'N/A',
        t.route || 'N/A',
        t.status,
        t.tool_calls_count.toString(),
        t.has_handoff ? 'Sim' : 'Não',
        t.errors_count.toString(),
      ])
      
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      ].join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `compliance_export_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Erro ao exportar compliance:', error)
      alert('Erro ao exportar dados de compliance')
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return '-'
    try {
      const date = new Date(dateString)
      return date.toLocaleString('pt-BR')
    } catch {
      return dateString
    }
  }

  const formatDateShort = (dateString: string) => {
    if (!dateString) return '-'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('pt-BR')
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <FiLoader className="animate-spin" style={{ fontSize: '2rem', margin: '0 auto 1rem', color: '#2196F3' }} />
        <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Carregando Painel do Agente...</div>
        <div style={{ color: '#666', fontSize: '0.9rem' }}>Buscando dados do LangSmith...</div>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Painel do Agente</h1>
        <p style={{ color: '#666' }}>Visualize todas as interações, redirecionamentos e métricas de compliance</p>
      </div>

      {/* Mensagem de Erro */}
      {error && (
        <Card style={{ marginBottom: '2rem', padding: '1.5rem', background: '#fff3cd', border: '1px solid #ffc107' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <FiAlertCircle style={{ fontSize: '1.5rem', color: '#f59e0b' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.25rem', color: '#856404' }}>Erro ao carregar dados</div>
              <div style={{ color: '#856404', fontSize: '0.9rem' }}>{error}</div>
            </div>
            <button
              onClick={() => {
                setError(null)
                loadInitialData()
              }}
              style={{
                padding: '0.5rem 1rem',
                background: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Tentar Novamente
            </button>
          </div>
        </Card>
      )}

      {/* Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem', 
        marginBottom: '2rem',
        borderBottom: '2px solid #e0e0e0'
      }}>
        {[
          { id: 'overview', label: 'Visão Geral', icon: FiActivity },
          { id: 'activity', label: 'Atividade', icon: FiFileText },
          { id: 'handoffs', label: 'Redirecionamentos', icon: FiArrowRight },
          { id: 'compliance', label: 'Compliance', icon: FiShield }
        ].map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '0.75rem 1.5rem',
                border: 'none',
                background: 'transparent',
                borderBottom: activeTab === tab.id ? '3px solid #2196F3' : '3px solid transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: activeTab === tab.id ? '600' : '400',
                color: activeTab === tab.id ? '#2196F3' : '#666',
                transition: 'all 0.2s'
              }}
            >
              <Icon />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Filtros */}
      <Card style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <FiFilter />
          <h3 style={{ margin: 0 }}>Filtros</h3>
        </div>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '1rem' 
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Cliente</label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              {clients.map(client => (
                <option key={client.client_id} value={client.client_id}>
                  {client.client_name} ({client.traces_count})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="completed">Completo</option>
              <option value="in_progress">Em Progresso</option>
              <option value="error">Erro</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Intent</label>
            <input
              type="text"
              value={selectedIntent}
              onChange={(e) => setSelectedIntent(e.target.value)}
              placeholder="Filtrar por intent"
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Route</label>
            <select
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="bypass">Bypass</option>
              <option value="react">React</option>
              <option value="llm_direct">LLM Direct</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Com Handoff</label>
            <select
              value={hasHandoffFilter}
              onChange={(e) => setHasHandoffFilter(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="true">Sim</option>
              <option value="false">Não</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Data Início</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Data Fim</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>
      </Card>

      {/* Conteúdo das Tabs */}
      {activeTab === 'overview' && summary && (
        <div>
          {/* Cards de Resumo */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <Card style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <FiActivity style={{ fontSize: '2rem', color: '#2196F3' }} />
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Total de Interações</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{summary.total_traces}</div>
                </div>
              </div>
            </Card>
            <Card style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <FiTool style={{ fontSize: '2rem', color: '#10b981' }} />
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Tool Calls</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{summary.total_tool_calls}</div>
                </div>
              </div>
            </Card>
            <Card style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <FiArrowRight style={{ fontSize: '2rem', color: '#f59e0b' }} />
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Redirecionamentos</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{summary.total_handoffs}</div>
                </div>
              </div>
            </Card>
            <Card style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <FiAlertCircle style={{ fontSize: '2rem', color: '#ef4444' }} />
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Erros</div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{summary.total_errors}</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Top Intents */}
          {summary.top_intents && summary.top_intents.length > 0 && (
            <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Top Intents</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {summary.top_intents.map((item, idx) => (
                  <div key={idx} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '0.75rem',
                    background: '#f5f5f5',
                    borderRadius: '4px'
                  }}>
                    <span>{item.intent || 'Desconhecido'}</span>
                    <span style={{ fontWeight: 'bold' }}>{item.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Status e Routes */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            <Card style={{ padding: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Status</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Object.entries(summary.status_counts || {}).map(([status, count]) => (
                  <div key={status} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{status}</span>
                    <span style={{ fontWeight: 'bold' }}>{count}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card style={{ padding: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem' }}>Routes</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Object.entries(summary.route_counts || {}).map(([route, count]) => (
                  <div key={route} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{route || 'Desconhecido'}</span>
                    <span style={{ fontWeight: 'bold' }}>{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'activity' && (
        <Card style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Atividade Recente</h3>
          {traces.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
              Nenhum trace encontrado com os filtros aplicados
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {traces.map(trace => (
                <div
                  key={trace.trace_id}
                  style={{
                    padding: '1rem',
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => router.push(`/trace/${trace.trace_id}`)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f5f5f5'
                    e.currentTarget.style.borderColor = '#2196F3'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'white'
                    e.currentTarget.style.borderColor = '#e0e0e0'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                        {trace.user_input?.substring(0, 100) || 'Sem input'}
                        {trace.user_input && trace.user_input.length > 100 && '...'}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#666', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        <span>Cliente: {trace.client_name || trace.client_id || 'N/A'}</span>
                        <span>Intent: {trace.intent || 'N/A'}</span>
                        <span>Route: {trace.route || 'N/A'}</span>
                        <span>Status: {trace.status}</span>
                        <span>Tools: {trace.tool_calls_count}</span>
                        {trace.has_handoff && <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>HANDOFF</span>}
                        {trace.errors_count > 0 && <span style={{ color: '#ef4444' }}>Erros: {trace.errors_count}</span>}
                      </div>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#666', textAlign: 'right' }}>
                      {formatDate(trace.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'handoffs' && (
        <Card style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Redirecionamentos (Handoffs)</h3>
          {handoffs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
              Nenhum redirecionamento encontrado com os filtros aplicados
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {handoffs.map((handoff, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '1.5rem',
                    border: '1px solid #f59e0b',
                    borderRadius: '8px',
                    background: '#fffbf0'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#f59e0b' }}>
                        Redirecionamento para Humano
                      </div>
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Motivo:</strong> {handoff.reason}
                      </div>
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Regra:</strong> {handoff.rule}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
                        <div>Cliente: {handoff.client_name || handoff.client_id || 'N/A'}</div>
                        <div>Input: {handoff.user_input}</div>
                        <div>Intent: {handoff.intent || 'N/A'} | Route: {handoff.route || 'N/A'}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#666', textAlign: 'right' }}>
                      {formatDate(handoff.timestamp)}
                    </div>
                  </div>
                  <button
                    onClick={() => router.push(`/trace/${handoff.trace_id}`)}
                    style={{
                      padding: '0.5rem 1rem',
                      background: '#2196F3',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.9rem'
                    }}
                  >
                    Ver Trace Completo
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === 'compliance' && (
        <div>
          <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}>Compliance e Auditoria</h3>
              <button
                onClick={handleExportCompliance}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.9rem'
                }}
              >
                <FiDownload />
                Exportar CSV
              </button>
            </div>
            <div style={{ color: '#666', lineHeight: '1.6' }}>
              <p><strong>LGPD:</strong> Todos os traces são armazenados com base legal e consentimento quando aplicável.</p>
              <p><strong>Auditoria:</strong> Trilha completa de eventos e acessos é mantida para cada interação.</p>
              <p><strong>Mascaramento:</strong> Dados sensíveis (PII) são mascarados automaticamente quando necessário.</p>
              <p><strong>Retenção:</strong> Traces são mantidos por 90 dias (configurável) para fins de auditoria e compliance.</p>
            </div>
          </Card>

          <Card style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Informações de Compliance por Trace</h3>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>
              Clique em um trace na aba &quot;Atividade&quot; para ver detalhes completos de compliance, incluindo:
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                <li>Base legal LGPD aplicada</li>
                <li>Status de consentimento</li>
                <li>Dados mascarados (PII)</li>
                <li>Idade do trace e política de retenção</li>
                <li>Log de acessos e auditoria</li>
              </ul>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

