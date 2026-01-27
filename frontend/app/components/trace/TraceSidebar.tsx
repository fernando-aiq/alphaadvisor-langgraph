'use client'

import { useState } from 'react'
import { Info, List, Wrench, Database, ChevronRight, ChevronDown } from 'lucide-react'

type TabType = 'overview' | 'steps' | 'tools' | 'metadata'

interface TraceSidebarProps {
  traceData?: any
  stepsData?: any
  toolsData?: any
  selectedRunId?: string | null
  onSelectRun?: (runId: string) => void
}

export default function TraceSidebar({
  traceData,
  stepsData,
  toolsData,
  selectedRunId,
  onSelectRun
}: TraceSidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: Info },
    { id: 'steps' as TabType, label: 'Steps', icon: List },
    { id: 'tools' as TabType, label: 'Tools', icon: Wrench },
    { id: 'metadata' as TabType, label: 'Metadata', icon: Database }
  ]

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedSteps(newExpanded)
  }

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const formatDuration = (ms?: number | null) => {
    if (!ms) return 'N/A'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}min`
  }

  return (
    <div style={{
      width: '300px',
      borderRight: '1px solid #e5e7eb',
      backgroundColor: '#f9fafb',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden'
    }}>
      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: 'white'
      }}>
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                padding: '0.75rem 0.5rem',
                border: 'none',
                backgroundColor: isActive ? '#f9fafb' : 'white',
                borderBottom: isActive ? '2px solid #3b82f6' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: isActive ? '600' : '400',
                color: isActive ? '#111827' : '#6b7280',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.25rem',
                transition: 'all 0.2s'
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        scrollbarWidth: 'thin',
        scrollbarColor: '#d1d5db #f9fafb'
      }}>
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {traceData && (
              <>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', fontWeight: '600' }}>
                    Informações Gerais
                  </div>
                  <div style={{
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    padding: '0.75rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem'
                  }}>
                    {traceData.name && (
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Nome</div>
                        <div style={{ fontSize: '0.875rem', color: '#111827', fontWeight: '500' }}>
                          {traceData.name}
                        </div>
                      </div>
                    )}
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Status</div>
                      <div style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '500',
                        backgroundColor: traceData.status === 'success' ? '#10b98120' : 
                                       traceData.status === 'error' ? '#ef444420' : '#3b82f620',
                        color: traceData.status === 'success' ? '#10b981' : 
                               traceData.status === 'error' ? '#ef4444' : '#3b82f6'
                      }}>
                        {traceData.status}
                      </div>
                    </div>
                    {traceData.run_count !== undefined && (
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Total de Runs</div>
                        <div style={{ fontSize: '0.875rem', color: '#111827', fontWeight: '500' }}>
                          {traceData.run_count}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {traceData.start_time && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', fontWeight: '600' }}>
                      Timestamps
                    </div>
                    <div style={{
                      backgroundColor: 'white',
                      borderRadius: '6px',
                      padding: '0.75rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Início</div>
                        <div style={{ fontSize: '0.875rem', color: '#111827' }}>
                          {formatDate(traceData.start_time)}
                        </div>
                      </div>
                      {traceData.end_time && (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Fim</div>
                          <div style={{ fontSize: '0.875rem', color: '#111827' }}>
                            {formatDate(traceData.end_time)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {traceData.error && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', fontWeight: '600' }}>
                      Erro
                    </div>
                    <div style={{
                      backgroundColor: '#fee2e2',
                      borderRadius: '6px',
                      padding: '0.75rem',
                      color: '#dc2626',
                      fontSize: '0.875rem'
                    }}>
                      {traceData.error}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'steps' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {stepsData?.steps && stepsData.steps.length > 0 ? (
              stepsData.steps.map((step: any, index: number) => {
                const isExpanded = expandedSteps.has(index)
                return (
                  <div
                    key={index}
                    style={{
                      backgroundColor: 'white',
                      borderRadius: '6px',
                      border: '1px solid #e5e7eb',
                      overflow: 'hidden'
                    }}
                  >
                    <button
                      onClick={() => toggleStep(index)}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: 'none',
                        backgroundColor: 'transparent',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        textAlign: 'left'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        <div>
                          <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>
                            {step.name || step.type || `Step ${index + 1}`}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                            {step.type} {step.duration_ms && `• ${formatDuration(step.duration_ms)}`}
                          </div>
                        </div>
                      </div>
                    </button>
                    {isExpanded && (
                      <div style={{
                        padding: '0.75rem',
                        borderTop: '1px solid #e5e7eb',
                        backgroundColor: '#f9fafb'
                      }}>
                        {step.input && (
                          <div style={{ marginBottom: '0.75rem' }}>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem', fontWeight: '600' }}>
                              Input
                            </div>
                            <pre style={{
                              fontSize: '0.75rem',
                              padding: '0.5rem',
                              backgroundColor: 'white',
                              borderRadius: '4px',
                              overflow: 'auto',
                              maxHeight: '150px',
                              margin: 0
                            }}>
                              {JSON.stringify(step.input, null, 2)}
                            </pre>
                          </div>
                        )}
                        {step.output && (
                          <div style={{ marginBottom: '0.75rem' }}>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem', fontWeight: '600' }}>
                              Output
                            </div>
                            <pre style={{
                              fontSize: '0.75rem',
                              padding: '0.5rem',
                              backgroundColor: 'white',
                              borderRadius: '4px',
                              overflow: 'auto',
                              maxHeight: '150px',
                              margin: 0
                            }}>
                              {JSON.stringify(step.output, null, 2)}
                            </pre>
                          </div>
                        )}
                        {step.error && (
                          <div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem', fontWeight: '600' }}>
                              Erro
                            </div>
                            <div style={{
                              fontSize: '0.75rem',
                              padding: '0.5rem',
                              backgroundColor: '#fee2e2',
                              color: '#dc2626',
                              borderRadius: '4px'
                            }}>
                              {step.error}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div style={{ textAlign: 'center', color: '#6b7280', fontSize: '0.875rem', padding: '2rem' }}>
                Nenhum step encontrado
              </div>
            )}
          </div>
        )}

        {activeTab === 'tools' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {toolsData?.tool_calls && toolsData.tool_calls.length > 0 ? (
              <>
                {toolsData.statistics && (
                  <div style={{
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    padding: '0.75rem',
                    marginBottom: '0.5rem'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', fontWeight: '600' }}>
                      Estatísticas
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem' }}>
                      <div>Total: {toolsData.statistics.total_tools}</div>
                      <div>Únicas: {toolsData.statistics.unique_tools}</div>
                      {toolsData.statistics.average_duration_ms && (
                        <div>Duração média: {formatDuration(toolsData.statistics.average_duration_ms)}</div>
                      )}
                    </div>
                  </div>
                )}
                {toolsData.tool_calls.map((tool: any, index: number) => (
                  <div
                    key={index}
                    style={{
                      backgroundColor: 'white',
                      borderRadius: '6px',
                      padding: '0.75rem',
                      border: '1px solid #e5e7eb'
                    }}
                  >
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>
                      {tool.tool_name || `Tool ${index + 1}`}
                    </div>
                    {tool.duration_ms && (
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                        Duração: {formatDuration(tool.duration_ms)}
                      </div>
                    )}
                    {tool.input && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>Input</div>
                        <pre style={{
                          fontSize: '0.75rem',
                          padding: '0.5rem',
                          backgroundColor: '#f9fafb',
                          borderRadius: '4px',
                          overflow: 'auto',
                          maxHeight: '100px',
                          margin: 0
                        }}>
                          {JSON.stringify(tool.input, null, 2)}
                        </pre>
                      </div>
                    )}
                    {tool.output && (
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>Output</div>
                        <pre style={{
                          fontSize: '0.75rem',
                          padding: '0.5rem',
                          backgroundColor: '#f9fafb',
                          borderRadius: '4px',
                          overflow: 'auto',
                          maxHeight: '100px',
                          margin: 0
                        }}>
                          {JSON.stringify(tool.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </>
            ) : (
              <div style={{ textAlign: 'center', color: '#6b7280', fontSize: '0.875rem', padding: '2rem' }}>
                Nenhuma tool encontrada
              </div>
            )}
          </div>
        )}

        {activeTab === 'metadata' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {traceData?.runs && traceData.runs.length > 0 ? (
              traceData.runs.map((run: any, index: number) => (
                <div
                  key={run.id || run.run_id || index}
                  style={{
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    padding: '0.75rem',
                    border: '1px solid #e5e7eb',
                    cursor: onSelectRun ? 'pointer' : 'default'
                  }}
                  onClick={() => onSelectRun && (run.id || run.run_id) && onSelectRun(run.id || run.run_id)}
                >
                  <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>
                    {run.name || run.run_type || `Run ${index + 1}`}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div>Tipo: {run.run_type || 'unknown'}</div>
                    {run.status && <div>Status: {run.status}</div>}
                    {run.start_time && <div>Início: {formatDate(run.start_time)}</div>}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', color: '#6b7280', fontSize: '0.875rem', padding: '2rem' }}>
                Nenhum metadata disponível
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
