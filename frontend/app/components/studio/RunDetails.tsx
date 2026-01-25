'use client'

import { useState, useEffect, useMemo } from 'react'
import { langSmithClient, type ThreadState, type Run, type GraphStructure } from '@/app/lib/studio/langsmith-client'
import Card from '@/app/components/Card'
import { FiArrowLeft, FiRefreshCw, FiLoader, FiCheckCircle, FiXCircle, FiClock, FiLayers } from 'react-icons/fi'
import Link from 'next/link'
import StudioGraphViewer from './StudioGraphViewer'

interface RunDetailsProps {
  threadId: string
}

export default function RunDetails({ threadId }: RunDetailsProps) {
  
  const [threadState, setThreadState] = useState<ThreadState | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [graphStructure, setGraphStructure] = useState<GraphStructure | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'details' | 'graph' | 'messages'>('details')
  
  // Obter assistantId do primeiro run ou do ambiente
  const assistantId = useMemo(() => {
    if (runs.length > 0) {
      return runs[0].assistant_id
    }
    // Fallback para variável de ambiente (apenas no cliente)
    if (typeof window !== 'undefined') {
      return process.env.NEXT_PUBLIC_ASSISTANT_ID?.trim() || 'agent'
    }
    return 'agent'
  }, [runs])

  const loadData = async () => {
    if (!threadId) return
    
    try {
      setLoading(true)
      setError(null)
      
      const [state, runsData] = await Promise.all([
        langSmithClient.getThreadState(threadId),
        langSmithClient.listRuns(threadId),
      ])
      
      setThreadState(state)
      setRuns(runsData)
      
      // Carregar estrutura do grafo após obter runs (para ter assistantId)
      const assistantIdToUse = runsData.length > 0 ? runsData[0].assistant_id : (typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_ASSISTANT_ID?.trim() || 'agent' : 'agent')
      if (assistantIdToUse) {
        await loadGraphStructure(assistantIdToUse)
      }
    } catch (err: any) {
      console.error('Erro ao carregar dados:', err)
      setError(err.message || 'Erro ao carregar detalhes da execução')
    } finally {
      setLoading(false)
    }
  }

  const loadGraphStructure = async (assistantIdToUse: string) => {
    if (!assistantIdToUse) return
    
    try {
      setLoadingGraph(true)
      const structure = await langSmithClient.getGraphStructure(assistantIdToUse)
      setGraphStructure(structure)
    } catch (err: any) {
      console.error('Erro ao carregar estrutura do grafo:', err)
      // Não definir erro aqui, apenas logar - estrutura padrão será usada
    } finally {
      setLoadingGraph(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [threadId])

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleString('pt-BR')
    } catch {
      return dateString
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <FiCheckCircle style={{ color: '#4CAF50' }} />
      case 'error':
        return <FiXCircle style={{ color: '#F44336' }} />
      case 'running':
        return <FiLoader className="animate-spin" style={{ color: '#FF9800' }} />
      default:
        return <FiClock style={{ color: '#999' }} />
    }
  }

  if (loading) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <FiLoader className="animate-spin" style={{ fontSize: '2rem', margin: '0 auto' }} />
        <div style={{ marginTop: '1rem' }}>Carregando detalhes...</div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ color: '#F44336', marginBottom: '1rem' }}>Erro: {error}</div>
        <button
          onClick={loadData}
          style={{
            padding: '0.5rem 1rem',
            background: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Tentar Novamente
        </button>
      </Card>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Link
          href="/studio/runs"
          style={{
            padding: '0.5rem',
            background: '#f5f5f5',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            textDecoration: 'none',
            color: 'inherit',
          }}
        >
          <FiArrowLeft />
        </Link>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Detalhes da Execução</h1>
        <button
          onClick={loadData}
          style={{
            padding: '0.5rem 1rem',
            background: '#f5f5f5',
            border: '1px solid #ddd',
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginLeft: 'auto',
          }}
        >
          <FiRefreshCw />
          Atualizar
        </button>
      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '1.5rem', borderBottom: '2px solid #e0e0e0', display: 'flex', gap: '1rem' }}>
        <button
          onClick={() => setActiveTab('details')}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'details' ? '2px solid #2196F3' : '2px solid transparent',
            color: activeTab === 'details' ? '#2196F3' : '#666',
            fontWeight: activeTab === 'details' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            marginBottom: '-2px',
          }}
        >
          Detalhes
        </button>
        <button
          onClick={() => setActiveTab('graph')}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'graph' ? '2px solid #2196F3' : '2px solid transparent',
            color: activeTab === 'graph' ? '#2196F3' : '#666',
            fontWeight: activeTab === 'graph' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            marginBottom: '-2px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <FiLayers />
          Visualização do Grafo
        </button>
        <button
          onClick={() => setActiveTab('messages')}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'messages' ? '2px solid #2196F3' : '2px solid transparent',
            color: activeTab === 'messages' ? '#2196F3' : '#666',
            fontWeight: activeTab === 'messages' ? '600' : '400',
            cursor: 'pointer',
            fontSize: '0.95rem',
            marginBottom: '-2px',
          }}
        >
          Mensagens
        </button>
      </div>

      {/* Conteúdo baseado na aba ativa */}
      {activeTab === 'details' && (
        <>
          {/* Thread ID */}
          <Card style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#666' }}>Thread ID</div>
            <div style={{ fontFamily: 'monospace', fontSize: '1rem', fontWeight: 'bold' }}>{threadId}</div>
          </Card>

          {/* Runs */}
          {runs.length > 0 && (
            <Card style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Runs ({runs.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {runs.map((run) => (
                  <div
                    key={run.run_id}
                    style={{
                      padding: '1rem',
                      border: '1px solid #e0e0e0',
                      borderRadius: '8px',
                      background: '#fafafa',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '0.9rem' }}>
                          {run.run_id}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.25rem' }}>
                          Assistant: {run.assistant_id}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {getStatusIcon(run.status)}
                        <span style={{ textTransform: 'capitalize' }}>{run.status}</span>
                      </div>
                    </div>
                    {run.created_at && (
                      <div style={{ fontSize: '0.85rem', color: '#666', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                        <FiClock />
                        Criado: {formatDate(run.created_at)}
                      </div>
                    )}
                    {run.error && (
                      <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#ffebee', borderRadius: '4px', color: '#F44336', fontSize: '0.85rem' }}>
                        Erro: {run.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Estado da Thread */}
          {threadState && (
            <Card style={{ padding: '1.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Estado da Thread</h3>
              
              {/* Próximos nós */}
              {threadState.next && threadState.next.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ marginBottom: '0.75rem' }}>Próximos Nós</h4>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {threadState.next.map((node) => (
                      <span
                        key={node}
                        style={{
                          padding: '0.25rem 0.75rem',
                          background: '#e8f5e9',
                          borderRadius: '4px',
                          fontSize: '0.85rem',
                          fontFamily: 'monospace',
                        }}
                      >
                        {node}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              {threadState.metadata && Object.keys(threadState.metadata).length > 0 && (
                <div>
                  <h4 style={{ marginBottom: '0.75rem' }}>Metadata</h4>
                  <pre style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px', overflow: 'auto', fontSize: '0.85rem' }}>
                    {JSON.stringify(threadState.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </Card>
          )}
        </>
      )}

      {activeTab === 'graph' && (
        <Card style={{ padding: '0', marginBottom: '1.5rem', minHeight: '600px' }}>
          {loadingGraph ? (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <FiLoader className="animate-spin" style={{ fontSize: '2rem', margin: '0 auto' }} />
              <div style={{ marginTop: '1rem' }}>Carregando estrutura do grafo...</div>
            </div>
          ) : graphStructure ? (
            <StudioGraphViewer
              graphStructure={graphStructure}
              threadState={threadState || undefined}
              runs={runs}
            />
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
              Não foi possível carregar a estrutura do grafo.
            </div>
          )}
        </Card>
      )}

      {activeTab === 'messages' && threadState && (
        <Card style={{ padding: '1.5rem' }}>
          <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Mensagens ({threadState.values?.messages?.length || 0})</h3>
          {threadState.values?.messages && threadState.values.messages.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {threadState.values.messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #e0e0e0',
                    borderRadius: '4px',
                    background: msg.type === 'human' ? '#e3f2fd' : msg.type === 'ai' ? '#f3e5f5' : '#fff3e0',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 'bold', textTransform: 'capitalize' }}>{msg.type}</span>
                    {msg.id && (
                      <span style={{ fontSize: '0.75rem', color: '#999', fontFamily: 'monospace' }}>{msg.id}</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.9rem' }}>
                    {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2)}
                  </div>
                  {msg.tool_calls && msg.tool_calls.length > 0 && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#666' }}>
                      Tool Calls: {msg.tool_calls.map(tc => tc.name).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>Nenhuma mensagem encontrada.</div>
          )}
        </Card>
      )}
    </div>
  )
}
