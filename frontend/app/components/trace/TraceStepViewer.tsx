'use client'

import { useState } from 'react'
import Card from '../Card'

interface Step {
  type: string
  node?: string
  timestamp?: string
  duration_ms?: number
  content?: string
  tool?: string
  input?: any
  output?: any
  tools_used?: string[]
  tool_calls?: Array<{
    tool_name: string
    timestamp: string
    input: any
    output: any
    duration_ms?: number
    error?: string
  }>
}

interface TraceStepsData {
  trace_id: string
  steps: Step[]
  total_steps: number
}

interface TraceStepViewerProps {
  data: TraceStepsData
}

const getToolDescription = (toolName: string): string => {
  const descriptions: Record<string, string> = {
    'obter_carteira': 'Obtém dados completos da carteira do cliente',
    'analisar_adequacao': 'Analisa se a carteira está adequada ao perfil de risco',
    'analisar_alinhamento_objetivos': 'Verifica alinhamento com objetivos de curto/médio/longo prazo',
    'analisar_diversificacao': 'Analisa a diversificação da carteira',
    'recomendar_rebalanceamento': 'Recomenda ajustes na alocação de ativos',
    'buscar_oportunidades': 'Busca oportunidades de investimento',
    'calcular_projecao': 'Calcula projeções futuras baseadas em aportes e rentabilidade',
    'llm_with_carteira': 'Chamada direta ao LLM com contexto da carteira'
  }
  return descriptions[toolName] || 'Ferramenta utilizada durante o processamento'
}

export default function TraceStepViewer({ data }: TraceStepViewerProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())
  const { steps } = data

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedSteps(newExpanded)
  }

  const getStepIcon = (step: Step) => {
    if (step.type === 'thought') return '💭'
    if (step.type === 'action') return '⚡'
    if (step.type === 'observation') return '👁️'
    if (step.type === 'graph_step') return '🔷'
    return '📝'
  }

  const getStepDescription = (step: Step) => {
    const descriptions: Record<string, string> = {
      'graph_step': 'Execução de um nó do grafo LangGraph. Mostra quando cada nó foi executado e seus resultados.',
      'thought': 'Raciocínio do agente ReAct - o que o agente está pensando antes de tomar uma ação.',
      'action': 'Ação executada - chamada de uma ferramenta (tool) para obter informações ou realizar uma análise.',
      'observation': 'Observação/resultado de uma ação - o que a ferramenta retornou após ser executada.'
    }
    return descriptions[step.type] || 'Passo de execução do trace'
  }

  const getStepColor = (step: Step) => {
    if (step.type === 'thought') return '#E3F2FD'
    if (step.type === 'action') return '#FFF3E0'
    if (step.type === 'observation') return '#F3E5F5'
    if (step.type === 'graph_step') return '#E8F5E9'
    return '#F5F5F5'
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return ''
    try {
      return new Date(timestamp).toLocaleTimeString()
    } catch {
      return timestamp
    }
  }

  return (
    <Card className="trace-step-viewer" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>Passos de Execução</h3>
        <div style={{ fontSize: '0.9rem', color: '#666' }}>
          Total: <strong>{data.total_steps}</strong> passos
          <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: '#999' }} title="Cada passo representa uma ação, raciocínio ou execução de nó durante o processamento">ℹ️</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {steps.map((step, index) => {
          const isExpanded = expandedSteps.has(index)
          const bgColor = getStepColor(step)
          const icon = getStepIcon(step)

          return (
            <div
              key={index}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                backgroundColor: bgColor,
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
                onClick={() => toggleStep(index)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1 }}>
                  <span style={{ fontSize: '1.2rem' }} title={getStepDescription(step)}>{icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {step.type === 'graph_step' ? `Nó: ${step.node}` : step.type.toUpperCase()}
                      <span style={{ fontSize: '0.75rem', color: '#999' }} title={getStepDescription(step)}>ℹ️</span>
                    </div>
                    {step.tool && (
                      <div style={{ fontSize: '0.85rem', color: '#666' }}>
                        Tool: <strong>{step.tool}</strong>
                        <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: '#999' }} title="Ferramenta (tool) que foi chamada para obter informações ou realizar uma análise">ℹ️</span>
                      </div>
                    )}
                    {step.content && (
                      <div style={{ fontSize: '0.9rem', color: '#333', marginTop: '0.25rem' }}>
                        {step.content.substring(0, 100)}{step.content.length > 100 ? '...' : ''}
                      </div>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: '#666' }}>
                  {step.duration_ms && (
                    <span>{step.duration_ms.toFixed(0)}ms</span>
                  )}
                  {step.timestamp && (
                    <span>{formatTimestamp(step.timestamp)}</span>
                  )}
                  <span style={{ fontSize: '1.2rem' }}>
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {isExpanded && (
                <div style={{ padding: '1rem', borderTop: '1px solid #e0e0e0', backgroundColor: '#fff' }}>
                  {step.input && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Input:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Dados de entrada passados para este passo">ℹ️</span>
                      </div>
                      <pre style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: '4px', 
                        fontSize: '0.85rem',
                        overflow: 'auto',
                        maxHeight: '200px'
                      }}>
                        {JSON.stringify(step.input, null, 2)}
                      </pre>
                    </div>
                  )}
                  {step.output && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Output:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Dados de saída gerados por este passo">ℹ️</span>
                      </div>
                      <pre style={{ 
                        padding: '0.75rem', 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: '4px', 
                        fontSize: '0.85rem',
                        overflow: 'auto',
                        maxHeight: '200px'
                      }}>
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {step.tools_used && step.tools_used.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Tools Utilizadas:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Lista de ferramentas (tools) que foram utilizadas neste passo">ℹ️</span>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {step.tools_used.map((tool, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: '#2196F3',
                              color: 'white',
                              borderRadius: '4px',
                              fontSize: '0.85rem',
                              fontWeight: '500'
                            }}
                            title={getToolDescription(tool)}
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {step.tool_calls && step.tool_calls.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        Detalhes das Tool Calls:
                        <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Detalhes completos de cada chamada de tool neste passo">ℹ️</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {step.tool_calls.map((toolCall: any, idx: number) => (
                          <div
                            key={idx}
                            style={{
                              padding: '0.75rem',
                              backgroundColor: '#f5f5f5',
                              borderRadius: '4px',
                              border: '1px solid #e0e0e0'
                            }}
                          >
                            <div style={{ fontWeight: '600', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                              {toolCall.tool_name}
                              {toolCall.duration_ms && (
                                <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: '#666', fontWeight: 'normal' }}>
                                  ({toolCall.duration_ms.toFixed(0)}ms)
                                </span>
                              )}
                            </div>
                            {toolCall.input && (
                              <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                                <strong>Input:</strong> {JSON.stringify(toolCall.input).substring(0, 100)}
                                {JSON.stringify(toolCall.input).length > 100 && '...'}
                              </div>
                            )}
                            {toolCall.error && (
                              <div style={{ fontSize: '0.8rem', color: '#F44336', marginTop: '0.25rem' }}>
                                <strong>Erro:</strong> {toolCall.error}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

