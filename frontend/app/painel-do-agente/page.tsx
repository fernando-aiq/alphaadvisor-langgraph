'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
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
  FiCalendar
} from 'react-icons/fi'

// Função para obter URL da API
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    return process.env.API_URL || 'http://localhost:8000'
  }
  
  const isVercel = window.location.hostname.includes('vercel.app') || 
                   window.location.hostname.includes('vercel.com')
  
  // No Vercel, usar rotas de API do Next.js (proxy)
  if (isVercel) {
    return '' // URL relativa usa as rotas de API
  }
  
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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
  
  const apiUrl = getApiUrl()

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

  const loadInitialData = async () => {
    try {
      await Promise.all([
        loadSummary(),
        loadTraces(),
        loadHandoffs(),
        loadClients()
      ])
    } catch (error) {
      console.error('Erro ao carregar dados iniciais:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedClient) params.append('client_id', selectedClient)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const endpoint = apiUrl ? `${apiUrl}/api/painel-agente/summary` : '/api/painel-agente/summary'
      const response = await axios.get(`${endpoint}?${params}`)
      setSummary(response.data.summary)
    } catch (error) {
      console.error('Erro ao carregar resumo:', error)
    }
  }

  const loadTraces = async () => {
    try {
      const params = new URLSearchParams()
      params.append('limit', '50')
      if (selectedClient) params.append('client_id', selectedClient)
      if (selectedStatus) params.append('status', selectedStatus)
      if (selectedIntent) params.append('intent', selectedIntent)
      if (selectedRoute) params.append('route', selectedRoute)
      if (hasHandoffFilter) params.append('has_handoff', hasHandoffFilter)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const endpoint = apiUrl ? `${apiUrl}/api/painel-agente/traces` : '/api/painel-agente/traces'
      const response = await axios.get(`${endpoint}?${params}`)
      setTraces(response.data.traces || [])
    } catch (error) {
      console.error('Erro ao carregar traces:', error)
    }
  }

  const loadHandoffs = async () => {
    try {
      const params = new URLSearchParams()
      params.append('limit', '50')
      if (selectedClient) params.append('client_id', selectedClient)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const endpoint = apiUrl ? `${apiUrl}/api/painel-agente/handoffs` : '/api/painel-agente/handoffs'
      const response = await axios.get(`${endpoint}?${params}`)
      setHandoffs(response.data.handoffs || [])
    } catch (error) {
      console.error('Erro ao carregar handoffs:', error)
    }
  }

  const loadClients = async () => {
    try {
      const endpoint = apiUrl ? `${apiUrl}/api/painel-agente/clients` : '/api/painel-agente/clients'
      const response = await axios.get(endpoint)
      setClients(response.data.clients || [])
    } catch (error) {
      console.error('Erro ao carregar clientes:', error)
    }
  }

  const handleExportCompliance = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedClient) params.append('client_id', selectedClient)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      params.append('format', 'csv')
      
      const endpoint = apiUrl ? `${apiUrl}/api/painel-agente/compliance/export` : '/api/painel-agente/compliance/export'
      const response = await axios.get(`${endpoint}?${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
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
        <div>Carregando Painel do Agente...</div>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Painel do Agente</h1>
        <p style={{ color: '#666' }}>Visualize todas as interações, redirecionamentos e métricas de compliance</p>
      </div>

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

