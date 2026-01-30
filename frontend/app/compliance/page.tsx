'use client'

import { useState, useEffect, useCallback } from 'react'
import Card from '../components/Card'
import '../globals.css'
import {
  FiShield,
  FiFilter,
  FiDownload,
  FiLoader,
  FiAlertCircle,
  FiPlus,
  FiEye,
  FiX,
  FiExternalLink
} from 'react-icons/fi'

interface ComplianceItem {
  trace_id: string
  timestamp?: string
  client_id?: string
  client_name?: string
  intent?: string
  route?: string
  trace_age_days?: number | null
  has_pii_masked?: boolean
  lgpd_base_legal?: string
  lgpd_consent?: boolean
  retention_days?: number
  access_events_count?: number
}

interface ComplianceSummary {
  total_traces: number
  with_consent: number
  with_pii_masked: number
  retention_days: number
}

interface ComplianceRule {
  id: string
  title: string
  description: string
  category?: string | null
  created_at: string
}

interface Client {
  client_id: string
  client_name: string
  traces_count: number
}

interface Regulacao {
  id: string
  titulo: string
  norma: string
  fonte_url: string
  vigencia: string
  resumo: string
}

interface RegulacaoDetail extends Regulacao {
  texto_completo?: string
}

const POLICIES = [
  {
    id: 'lgpd',
    title: 'LGPD',
    description: 'Todos os traces são armazenados com base legal e consentimento quando aplicável. Base legal e status de consentimento devem ser verificados por interação.'
  },
  {
    id: 'cvm',
    title: 'CVM – Regras do assessor',
    description: 'Conformidade com as regras da CVM para assessoria de investimentos. Recomendações e explicações devem ser registradas para auditoria.'
  },
  {
    id: 'auditoria',
    title: 'Auditoria',
    description: 'Trilha completa de eventos e acessos é mantida para cada interação. Logs de acesso disponíveis por trace.'
  },
  {
    id: 'pii',
    title: 'Mascaramento de PII',
    description: 'Dados sensíveis (PII) são mascarados automaticamente quando necessário. Verificar status de mascaramento por trace.'
  },
  {
    id: 'retencao',
    title: 'Retenção',
    description: 'Traces são mantidos por 90 dias (configurável) para fins de auditoria e compliance.'
  }
]

export default function CompliancePage() {
  const [loading, setLoading] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [complianceList, setComplianceList] = useState<ComplianceItem[]>([])
  const [summary, setSummary] = useState<ComplianceSummary | null>(null)
  const [clients, setClients] = useState<Client[]>([])
  const [rules, setRules] = useState<ComplianceRule[]>([])
  const [selectedClient, setSelectedClient] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [detailTraceId, setDetailTraceId] = useState<string | null>(null)
  const [detailData, setDetailData] = useState<Record<string, unknown> | null>(null)
  const [showRuleModal, setShowRuleModal] = useState(false)
  const [newRuleTitle, setNewRuleTitle] = useState('')
  const [newRuleDescription, setNewRuleDescription] = useState('')
  const [newRuleCategory, setNewRuleCategory] = useState('')
  const [submittingRule, setSubmittingRule] = useState(false)
  const [regulacoes, setRegulacoes] = useState<Regulacao[]>([])
  const [loadingRegulacoes, setLoadingRegulacoes] = useState(true)
  const [regulacaoModalId, setRegulacaoModalId] = useState<string | null>(null)
  const [regulacaoDetail, setRegulacaoDetail] = useState<RegulacaoDetail | null>(null)
  const [loadingRegulacaoDetail, setLoadingRegulacaoDetail] = useState(false)

  const loadClients = useCallback(async () => {
    try {
      const res = await fetch('/api/painel-agente/clients')
      if (!res.ok) return
      const data = await res.json()
      setClients(data.clients || [])
    } catch {
      // ignore
    }
  }, [])

  const loadComplianceList = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (selectedClient) params.set('client_id', selectedClient)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      params.set('limit', '100')
      const res = await fetch(`/api/painel-agente/compliance/list?${params.toString()}`)
      if (!res.ok) throw new Error('Falha ao carregar lista de compliance')
      const data = await res.json()
      setComplianceList(data.compliance_list || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar lista')
      setComplianceList([])
    }
  }, [selectedClient, startDate, endDate])

  const loadSummary = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (selectedClient) params.set('client_id', selectedClient)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      const res = await fetch(`/api/painel-agente/compliance/summary?${params.toString()}`)
      if (!res.ok) return
      const data = await res.json()
      setSummary(data)
    } catch {
      setSummary(null)
    }
  }, [selectedClient, startDate, endDate])

  const loadRules = useCallback(async () => {
    try {
      const res = await fetch('/api/painel-agente/compliance/rules')
      if (!res.ok) return
      const data = await res.json()
      setRules(data.rules || [])
    } catch {
      setRules([])
    }
  }, [])

  const loadRegulacoes = useCallback(async () => {
    setLoadingRegulacoes(true)
    try {
      const res = await fetch('/api/regulacoes')
      if (!res.ok) throw new Error('Falha ao carregar normas')
      const data = await res.json()
      setRegulacoes(data.regulacoes || [])
    } catch {
      setRegulacoes([])
    } finally {
      setLoadingRegulacoes(false)
    }
  }, [])

  useEffect(() => {
    loadClients()
    loadRules()
    loadRegulacoes()
  }, [loadClients, loadRules, loadRegulacoes])

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([loadComplianceList(), loadSummary()]).finally(() => setLoading(false))
  }, [loadComplianceList, loadSummary])

  const openDetail = async (traceId: string) => {
    setDetailTraceId(traceId)
    setDetailData(null)
    setLoadingDetail(true)
    try {
      const res = await fetch(`/api/painel-agente/compliance/${encodeURIComponent(traceId)}`)
      if (res.ok) {
        const data = await res.json()
        setDetailData(data)
      }
    } catch {
      setDetailData({ error: 'Falha ao carregar detalhe' })
    } finally {
      setLoadingDetail(false)
    }
  }

  const closeDetail = () => {
    setDetailTraceId(null)
    setDetailData(null)
  }

  const openRegulacaoDetail = async (id: string) => {
    setRegulacaoModalId(id)
    setRegulacaoDetail(null)
    setLoadingRegulacaoDetail(true)
    try {
      const res = await fetch(`/api/regulacoes/${encodeURIComponent(id)}`)
      if (res.ok) {
        const data = await res.json()
        setRegulacaoDetail(data)
      }
    } catch {
      setRegulacaoDetail(null)
    } finally {
      setLoadingRegulacaoDetail(false)
    }
  }

  const closeRegulacaoModal = () => {
    setRegulacaoModalId(null)
    setRegulacaoDetail(null)
  }

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const params = new URLSearchParams()
      params.set('format', format)
      if (selectedClient) params.set('client_id', selectedClient)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      const res = await fetch(`/api/painel-agente/compliance/export?${params.toString()}`)
      if (!res.ok) throw new Error('Falha no export')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `compliance_export_${new Date().toISOString().split('T')[0]}.${format === 'csv' ? 'csv' : 'json'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Erro ao exportar')
    }
  }

  const submitNewRule = async () => {
    const title = newRuleTitle.trim()
    if (!title) {
      alert('Título é obrigatório')
      return
    }
    setSubmittingRule(true)
    try {
      const res = await fetch('/api/painel-agente/compliance/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description: newRuleDescription.trim(),
          category: newRuleCategory.trim() || undefined
        })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.error || 'Falha ao criar regra')
      }
      setNewRuleTitle('')
      setNewRuleDescription('')
      setNewRuleCategory('')
      setShowRuleModal(false)
      await loadRules()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Erro ao incluir regra')
    } finally {
      setSubmittingRule(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    try {
      return new Date(dateString).toLocaleString('pt-BR')
    } catch {
      return dateString
    }
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiShield />
          Compliance
        </h1>
        <p style={{ color: '#666' }}>Políticas, regras específicas e auditoria de traces</p>
      </div>

      {error && (
        <Card style={{ marginBottom: '2rem', padding: '1.5rem', background: '#fff3cd', border: '1px solid #ffc107' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <FiAlertCircle style={{ fontSize: '1.5rem', color: '#f59e0b' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.25rem', color: '#856404' }}>Erro</div>
              <div style={{ color: '#856404', fontSize: '0.9rem' }}>{error}</div>
            </div>
            <button
              onClick={() => { setError(null); loadComplianceList(); loadSummary(); }}
              style={{ padding: '0.5rem 1rem', background: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.9rem' }}
            >
              Tentar novamente
            </button>
          </div>
        </Card>
      )}

      {/* Políticas que o assessor deve acompanhar */}
      <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>Políticas que o assessor deve acompanhar</h2>
        <div style={{ display: 'grid', gap: '1rem' }}>
          {POLICIES.map((p) => (
            <div
              key={p.id}
              style={{
                padding: '1rem',
                background: '#f8fafc',
                borderRadius: '8px',
                borderLeft: '4px solid #2196F3'
              }}
            >
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{p.title}</div>
              <div style={{ fontSize: '0.9rem', color: '#555' }}>{p.description}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Normas que o agente utiliza */}
      <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>Normas que o agente utiliza</h2>
        <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Normas regulatórias consultadas pelo agente (CVM, Lei Mercado de Capitais, LGPD, ANBIMA). Clique em &quot;Ver texto completo&quot; para abrir o conteúdo integral.
        </p>
        {loadingRegulacoes ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: '#666' }}>
            <FiLoader className="animate-spin" style={{ fontSize: '1.5rem', marginBottom: '0.5rem', display: 'block' }} />
            Carregando normas...
          </div>
        ) : regulacoes.length === 0 ? (
          <p style={{ color: '#666', fontSize: '0.9rem' }}>Nenhuma norma disponível. Verifique se o backend está acessível.</p>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {regulacoes.map((r) => (
              <div
                key={r.id}
                style={{
                  padding: '1rem',
                  background: '#f8fafc',
                  borderRadius: '8px',
                  borderLeft: '4px solid #10b981'
                }}
              >
                <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{r.titulo}</div>
                <div style={{ fontSize: '0.85rem', color: '#555', marginBottom: '0.25rem' }}>{r.norma}</div>
                {r.vigencia && <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '0.5rem' }}>Vigência: {r.vigencia}</div>}
                <div style={{ fontSize: '0.9rem', color: '#555', marginBottom: '0.75rem' }}>{r.resumo}</div>
                <button
                  onClick={() => openRegulacaoDetail(r.id)}
                  style={{
                    padding: '0.4rem 0.8rem',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  Ver texto completo
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Regras de compliance específicas */}
      <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Regras de compliance específicas</h2>
          <button
            onClick={() => setShowRuleModal(true)}
            style={{
              padding: '0.5rem 1rem',
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
            <FiPlus />
            Incluir regra
          </button>
        </div>
        {rules.length === 0 ? (
          <p style={{ color: '#666', fontSize: '0.9rem' }}>Nenhuma regra específica cadastrada. Use &quot;Incluir regra&quot; para adicionar.</p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {rules.map((r) => (
              <li
                key={r.id}
                style={{
                  padding: '0.75rem',
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem'
                }}
              >
                <div style={{ fontWeight: '600' }}>{r.title}</div>
                {r.description && <div style={{ fontSize: '0.9rem', color: '#555' }}>{r.description}</div>}
                {r.category && <div style={{ fontSize: '0.8rem', color: '#888' }}>Categoria: {r.category}</div>}
                <div style={{ fontSize: '0.8rem', color: '#999' }}>{formatDate(r.created_at)}</div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Filtros e resumo */}
      <Card style={{ marginBottom: '2rem', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <FiFilter />
          <h3 style={{ margin: 0 }}>Filtros</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Cliente</label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              {clients.map((c) => (
                <option key={c.client_id} value={c.client_id}>
                  {c.client_name} ({c.traces_count})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Data início</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Data fim</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>
      </Card>

      {/* Cards resumo */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Total de traces</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{summary.total_traces}</div>
          </Card>
          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Com consentimento LGPD</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{summary.with_consent}</div>
          </Card>
          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>PII mascarado</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{summary.with_pii_masked}</div>
          </Card>
          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Retenção (dias)</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600' }}>{summary.retention_days}</div>
          </Card>
        </div>
      )}

      {/* Export e tabela */}
      <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>Traces e compliance</h3>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => handleExport('csv')}
              style={{ padding: '0.5rem 1rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}
            >
              <FiDownload />
              Exportar CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              style={{ padding: '0.5rem 1rem', background: '#6366f1', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}
            >
              <FiDownload />
              Exportar JSON
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
            <FiLoader className="animate-spin" style={{ fontSize: '1.5rem', marginBottom: '0.5rem', display: 'block' }} />
            Carregando lista de compliance...
          </div>
        ) : complianceList.length === 0 ? (
          <p style={{ color: '#666', fontSize: '0.9rem' }}>Nenhum trace no período com dados de compliance.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem' }}>Trace ID</th>
                  <th style={{ padding: '0.75rem' }}>Data/Hora</th>
                  <th style={{ padding: '0.75rem' }}>Cliente</th>
                  <th style={{ padding: '0.75rem' }}>Intent</th>
                  <th style={{ padding: '0.75rem' }}>Base legal</th>
                  <th style={{ padding: '0.75rem' }}>Consent.</th>
                  <th style={{ padding: '0.75rem' }}>PII mask.</th>
                  <th style={{ padding: '0.75rem' }}>Idade (d)</th>
                  <th style={{ padding: '0.75rem' }}>Retenção</th>
                  <th style={{ padding: '0.75rem' }}>Acessos</th>
                  <th style={{ padding: '0.75rem' }}></th>
                </tr>
              </thead>
              <tbody>
                {complianceList.map((row) => (
                  <tr
                    key={row.trace_id}
                    style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                    onClick={() => openDetail(row.trace_id)}
                  >
                    <td style={{ padding: '0.75rem', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis' }} title={row.trace_id}>
                      {row.trace_id?.slice(0, 8)}…
                    </td>
                    <td style={{ padding: '0.75rem' }}>{formatDate(row.timestamp)}</td>
                    <td style={{ padding: '0.75rem' }}>{row.client_name || row.client_id || '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.intent || '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.lgpd_base_legal ?? '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.lgpd_consent ? 'Sim' : 'Não'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.has_pii_masked ? 'Sim' : 'Não'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.trace_age_days ?? '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.retention_days ?? '-'}</td>
                    <td style={{ padding: '0.75rem' }}>{row.access_events_count ?? 0}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <button
                        onClick={(e) => { e.stopPropagation(); openDetail(row.trace_id); }}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}
                        title="Ver detalhe"
                      >
                        <FiEye />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal detalhe trace */}
      {detailTraceId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem'
          }}
          onClick={closeDetail}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              maxWidth: '560px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              padding: '1.5rem',
              boxShadow: '0 4px 20px rgba(0,0,0,0.15)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}>Detalhe de compliance – {detailTraceId.slice(0, 8)}…</h3>
              <button onClick={closeDetail} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}>
                <FiX size={24} />
              </button>
            </div>
            {loadingDetail ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <FiLoader className="animate-spin" style={{ fontSize: '1.5rem' }} />
              </div>
            ) : detailData ? (
              <pre style={{ fontSize: '0.85rem', overflow: 'auto', background: '#f8fafc', padding: '1rem', borderRadius: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {JSON.stringify(detailData, null, 2)}
              </pre>
            ) : null}
          </div>
        </div>
      )}

      {/* Modal incluir regra */}
      {showRuleModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem'
          }}
          onClick={() => !submittingRule && setShowRuleModal(false)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              maxWidth: '480px',
              width: '100%',
              padding: '1.5rem',
              boxShadow: '0 4px 20px rgba(0,0,0,0.15)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 1rem 0' }}>Incluir regra de compliance</h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Título *</label>
              <input
                type="text"
                value={newRuleTitle}
                onChange={(e) => setNewRuleTitle(e.target.value)}
                placeholder="Ex.: Não divulgar rentabilidade futura"
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Descrição</label>
              <textarea
                value={newRuleDescription}
                onChange={(e) => setNewRuleDescription(e.target.value)}
                placeholder="Descrição opcional da regra"
                rows={3}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px', resize: 'vertical' }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Categoria</label>
              <input
                type="text"
                value={newRuleCategory}
                onChange={(e) => setNewRuleCategory(e.target.value)}
                placeholder="Ex.: CVM, LGPD"
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button
                onClick={() => !submittingRule && setShowRuleModal(false)}
                style={{ padding: '0.5rem 1rem', background: '#e0e0e0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancelar
              </button>
              <button
                onClick={submitNewRule}
                disabled={submittingRule}
                style={{ padding: '0.5rem 1rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: submittingRule ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                {submittingRule ? <FiLoader className="animate-spin" size={16} /> : <FiPlus size={16} />}
                {submittingRule ? 'Salvando...' : 'Incluir'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal texto completo da norma */}
      {regulacaoModalId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem'
          }}
          onClick={closeRegulacaoModal}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '8px',
              maxWidth: '800px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 4px 20px rgba(0,0,0,0.15)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: '1px solid #eee' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
                {regulacaoDetail ? regulacaoDetail.titulo : regulacaoModalId}
              </h3>
              <button onClick={closeRegulacaoModal} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}>
                <FiX size={24} />
              </button>
            </div>
            <div style={{ padding: '1rem 1.5rem', overflow: 'auto', flex: 1 }}>
              {loadingRegulacaoDetail ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <FiLoader className="animate-spin" style={{ fontSize: '1.5rem' }} />
                </div>
              ) : regulacaoDetail ? (
                <>
                  {regulacaoDetail.norma && <div style={{ fontSize: '0.9rem', color: '#555', marginBottom: '0.5rem' }}>{regulacaoDetail.norma}</div>}
                  {regulacaoDetail.fonte_url && (
                    <a
                      href={regulacaoDetail.fonte_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginBottom: '1rem', color: '#2196F3', fontSize: '0.9rem' }}
                    >
                      <FiExternalLink size={14} />
                      Fonte oficial
                    </a>
                  )}
                  {regulacaoDetail.texto_completo && (
                    <div
                      style={{
                        fontSize: '0.85rem',
                        overflow: 'auto',
                        background: '#f8fafc',
                        padding: '1rem',
                        borderRadius: '4px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        maxHeight: '50vh'
                      }}
                    >
                      {regulacaoDetail.texto_completo}
                    </div>
                  )}
                </>
              ) : (
                <p style={{ color: '#666' }}>Não foi possível carregar o texto da norma.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
