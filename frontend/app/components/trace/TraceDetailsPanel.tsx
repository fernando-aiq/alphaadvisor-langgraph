'use client'

import Card from '../Card'

interface TraceDetails {
  trace_id: string
  timestamp: string
  user_input: string
  intent?: string
  route?: string
  status: string
  completed_at?: string
  tools_used?: string[]
  tool_calls?: Array<{
    tool_name: string
    timestamp: string
    input: any
    output: any
    duration_ms?: number
    error?: string
  }>
  final_output?: any
  explanation?: any
}

interface TraceDetailsPanelProps {
  trace: TraceDetails
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

export default function TraceDetailsPanel({ trace }: TraceDetailsPanelProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  return (
    <Card className="trace-details-panel" style={{ padding: '1.5rem' }}>
      <h3 style={{ margin: 0, marginBottom: '1rem' }}>Detalhes do Trace</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Trace ID
            <span style={{ fontSize: '0.75rem', color: '#999' }} title="Identificador único deste trace">ℹ️</span>
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{trace.trace_id}</div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Mensagem do Usuário
            <span style={{ fontSize: '0.75rem', color: '#999' }} title="Mensagem original enviada pelo usuário que iniciou este trace">ℹ️</span>
          </div>
          <div style={{ padding: '0.75rem', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            {trace.user_input}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Intenção
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Intenção detectada da mensagem do usuário (ex: carteira_analysis, buscar_oportunidades)">ℹ️</span>
            </div>
            <div style={{ fontWeight: '600' }}>{trace.intent || 'N/A'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Rota
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Rota escolhida pelo grafo (bypass para análises simples, react para raciocínio complexo, llm_direct para chamadas diretas)">ℹ️</span>
            </div>
            <div style={{ fontWeight: '600' }}>
              {trace.route ? (
                <span style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: trace.route === 'bypass' ? '#FF9800' : trace.route === 'react' ? '#9C27B0' : '#757575',
                  color: 'white',
                  borderRadius: '4px',
                  fontSize: '0.85rem'
                }}>
                  {trace.route}
                </span>
              ) : 'N/A'}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Status
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Status do trace (in_progress: em execução, completed: concluído, error: erro)">ℹ️</span>
            </div>
            <div>
              <span style={{
                padding: '0.25rem 0.5rem',
                backgroundColor: trace.status === 'completed' ? '#4CAF50' : trace.status === 'error' ? '#F44336' : '#FF9800',
                color: 'white',
                borderRadius: '4px',
                fontSize: '0.85rem'
              }}>
                {trace.status}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Iniciado em
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Data e hora em que o trace foi iniciado">ℹ️</span>
            </div>
            <div style={{ fontSize: '0.9rem' }}>{formatDate(trace.timestamp)}</div>
          </div>
        </div>

        {trace.completed_at && (
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Completado em
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Data e hora em que o trace foi finalizado">ℹ️</span>
            </div>
            <div style={{ fontSize: '0.9rem' }}>{formatDate(trace.completed_at)}</div>
          </div>
        )}

        {trace.tools_used && trace.tools_used.length > 0 && (
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Tools Utilizadas
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Lista de ferramentas (tools) que foram chamadas durante o processamento">ℹ️</span>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              {trace.tools_used.map((tool, idx) => (
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
            {trace.tool_calls && trace.tool_calls.length > 0 && (
              <div style={{ fontSize: '0.8rem', color: '#666', fontStyle: 'italic' }}>
                Total: {trace.tool_calls.length} chamada(s) de tool(s)
              </div>
            )}
          </div>
        )}

        {trace.explanation && (
          <div>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Explicação
              <span style={{ fontSize: '0.75rem', color: '#999' }} title="Detalhes sobre como o agente processou a mensagem, incluindo intenção, rota escolhida e ferramentas utilizadas">ℹ️</span>
            </div>
            <pre style={{
              padding: '0.75rem',
              backgroundColor: '#f5f5f5',
              borderRadius: '4px',
              fontSize: '0.85rem',
              overflow: 'auto',
              maxHeight: '200px'
            }}>
              {JSON.stringify(trace.explanation, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </Card>
  )
}

