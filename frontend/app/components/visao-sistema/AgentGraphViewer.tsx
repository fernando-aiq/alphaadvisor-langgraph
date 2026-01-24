'use client'

import { useMemo } from 'react'

interface StructureNode {
  id: string
  label?: string
  description?: string
  position?: { x: number; y: number }
  tools_used?: string[]
  is_entry_point?: boolean
  is_final?: boolean
  metadata?: { conditional?: boolean }
}

interface StructureEdge {
  id: string
  source: string
  target: string
  type?: string
  label?: string
  condition?: string
  description?: string
}

interface ConditionalEdge {
  source: string
  function?: string
  function_description?: string
  conditions?: Record<string, { target: string; description?: string; condition_logic?: string }>
}

interface Structure {
  nodes?: StructureNode[]
  edges?: StructureEdge[]
  entry_point?: string
  conditional_edges?: ConditionalEdge[]
}

interface TraceNode {
  id: string
  label?: string
  timestamp?: string
  duration_ms?: number
  data?: unknown
}

interface TraceEdge {
  id: string
  source: string
  target: string
  label?: string
  timestamp?: string
}

interface TraceHandoff {
  occurred?: boolean
  reason?: string
  rule?: string
  at_node?: string
}

interface TraceGraph {
  trace_id?: string
  nodes?: TraceNode[]
  edges?: TraceEdge[]
  route?: string
  intent?: string
  status?: string
  handoff?: TraceHandoff | null
}

interface AgentGraphViewerProps {
  structure: Structure | null
  traceGraph?: TraceGraph | null
}

const NODE_WIDTH = 140
const NODE_HEIGHT = 60
const OFFSET_X = 70
const OFFSET_Y = 30

export default function AgentGraphViewer({ structure, traceGraph }: AgentGraphViewerProps) {
  const nodes = structure?.nodes ?? []
  const edges = structure?.edges ?? []
  const conditionalEdges = structure?.conditional_edges ?? []

  const decisionNodeIds = useMemo(
    () => new Set(conditionalEdges.map((ce) => ce.source)),
    [conditionalEdges]
  )

  const visitedNodeIds = useMemo(() => {
    if (!traceGraph?.nodes) return new Set<string>()
    return new Set(traceGraph.nodes.filter((n) => n.timestamp).map((n) => n.id))
  }, [traceGraph?.nodes])

  const visitedEdgeKeys = useMemo(() => {
    if (!traceGraph?.edges) return new Set<string>()
    return new Set(
      traceGraph.edges.filter((e) => e.timestamp).map((e) => `${e.source}->${e.target}`)
    )
  }, [traceGraph?.edges])

  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const fallbackOrder = ['detect_intent', 'route_decision', 'bypass_analysis', 'react_agent', 'format_response']
    const spacing = 200
    const gridCols = 3

    nodes.forEach((node, idx) => {
      if (node.position && typeof node.position.x === 'number' && typeof node.position.y === 'number') {
        positions[node.id] = { x: node.position.x, y: node.position.y }
      } else {
        const order = fallbackOrder.indexOf(node.id) >= 0 ? fallbackOrder.indexOf(node.id) : idx
        const row = Math.floor(order / gridCols)
        const col = order % gridCols
        positions[node.id] = { x: col * spacing + 100, y: row * spacing + 100 }
      }
    })
    return positions
  }, [nodes])

  const maxX = useMemo(() => {
    let m = 0
    nodes.forEach((n) => {
      const p = nodePositions[n.id]
      if (p) m = Math.max(m, p.x + NODE_WIDTH)
    })
    return Math.max(m, 900)
  }, [nodes, nodePositions])

  const maxY = useMemo(() => {
    let m = 0
    nodes.forEach((n) => {
      const p = nodePositions[n.id]
      if (p) m = Math.max(m, p.y + NODE_HEIGHT)
    })
    return Math.max(m, 450)
  }, [nodes, nodePositions])

  const getNodeStyle = (node: StructureNode, isVisited: boolean) => {
    const base: React.CSSProperties = {
      backgroundColor: isVisited ? '#e3f2fd' : '#f5f5f5',
      border: '2px solid #bdbdbd',
      opacity: traceGraph && !isVisited ? 0.5 : 1
    }
    if (node.is_entry_point) return { ...base, borderLeft: '4px solid #4CAF50' }
    if (node.is_final) return { ...base, borderRight: '4px solid #00BCD4' }
    if (decisionNodeIds.has(node.id)) return { ...base, borderColor: '#2196F3', transform: 'rotate(0deg)' }
    return base
  }

  const getEdgeStyle = (edge: StructureEdge) => {
    const isCond = edge.type === 'conditional'
    const isVisited = traceGraph ? visitedEdgeKeys.has(`${edge.source}->${edge.target}`) : false
    return {
      stroke: isVisited ? '#2196F3' : isCond ? '#FF9800' : '#9e9e9e',
      strokeWidth: isVisited ? 2.5 : 1.5,
      strokeDasharray: isCond && !isVisited ? '6,4' : 'none'
    }
  }

  const getConditionalTooltip = (sourceId: string) => {
    const ce = conditionalEdges.find((c) => c.source === sourceId)
    if (!ce) return ''
    const parts = [ce.function_description || '']
    if (ce.conditions) {
      for (const [k, v] of Object.entries(ce.conditions)) {
        parts.push(`Se ${v.condition_logic || k} → ${v.target}`)
      }
    }
    return parts.filter(Boolean).join('\n')
  }

  const handoff = traceGraph?.handoff
  const showHandoff = handoff?.occurred === true

  if (!structure || (nodes.length === 0 && edges.length === 0)) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
        Carregando estrutura do grafo...
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fafafa' }}>
      <div style={{ padding: '12px 16px', background: 'white', borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Fluxo do Agente</h3>
        <div style={{ marginTop: '4px', fontSize: '13px', color: '#666' }}>
          {nodes.length} nós, {edges.length} arestas
          {traceGraph?.route && ` · Rota: ${traceGraph.route}`}
          {traceGraph?.intent && ` · Intenção: ${traceGraph.intent}`}
          {showHandoff && (
            <span style={{ marginLeft: '8px', color: '#f57c00', fontWeight: '600' }}> · Handoff para humano</span>
          )}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '1rem', minHeight: '360px' }}>
        <div
          style={{
            position: 'relative',
            width: maxX,
            height: maxY,
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            background: '#fff'
          }}
        >
          {/* Edges */}
          <svg
            style={{
              position: 'absolute',
              width: maxX,
              height: maxY,
              pointerEvents: 'none',
              overflow: 'visible'
            }}
          >
            <defs>
              <marker id="agv-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#9e9e9e" />
              </marker>
              <marker id="agv-arrow-visited" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#2196F3" />
              </marker>
            </defs>
            {edges.map((edge) => {
              const sp = nodePositions[edge.source]
              const tp = nodePositions[edge.target]
              if (!sp || !tp) return null
              const x1 = sp.x + OFFSET_X
              const y1 = sp.y + OFFSET_Y
              const x2 = tp.x + OFFSET_X
              const y2 = tp.y + OFFSET_Y
              const label = edge.label || edge.condition || ''
              const isVisited = traceGraph ? visitedEdgeKeys.has(`${edge.source}->${edge.target}`) : false
              const style = getEdgeStyle(edge)
              return (
                <g key={edge.id}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={style.stroke}
                    strokeWidth={style.strokeWidth}
                    strokeDasharray={style.strokeDasharray}
                    markerEnd={`url(#agv-arrow${isVisited ? '-visited' : ''})`}
                  />
                  {label && (
                    <text
                      x={(x1 + x2) / 2}
                      y={(y1 + y2) / 2 - 6}
                      fontSize="10"
                      fill={edge.type === 'conditional' ? '#e65100' : '#666'}
                      textAnchor="middle"
                      fontWeight={edge.type === 'conditional' ? 600 : 400}
                    >
                      {label}
                    </text>
                  )}
                </g>
              )
            })}
          </svg>

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node.id]
            if (!pos) return null
            const label = node.label || node.id
            const desc = node.description || ''
            const toolsStr = node.tools_used?.length ? `\nTools: ${node.tools_used.join(', ')}` : ''
            const condTip = decisionNodeIds.has(node.id) ? `\n\n[Decisão if/else]\n${getConditionalTooltip(node.id)}` : ''
            const isVisited = traceGraph ? visitedNodeIds.has(node.id) : false
            const isDecision = decisionNodeIds.has(node.id)

            return (
              <div
                key={node.id}
                style={{
                  position: 'absolute',
                  left: pos.x,
                  top: pos.y,
                  width: '140px',
                  padding: '8px 10px',
                  borderRadius: isDecision ? '4px' : '8px',
                  textAlign: 'center',
                  cursor: 'default',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: '#424242',
                  boxSizing: 'border-box',
                  ...getNodeStyle(node, isVisited)
                }}
                title={`${label}\n\n${desc}${toolsStr}${condTip}`}
              >
                {isDecision && <span style={{ fontSize: 10, marginRight: 4 }}>◆</span>}
                {label}
                {node.tools_used && node.tools_used.length > 0 && (
                  <div style={{ fontSize: 9, color: '#757575', marginTop: 2, fontWeight: 400 }}>
                    {node.tools_used.length} tool(s)
                  </div>
                )}
              </div>
            )
          })}

          {/* Handoff callout */}
          {showHandoff && handoff && (
            <div
              style={{
                position: 'absolute',
                left: (() => {
                  const atId = handoff.at_node
                  const id = atId || (traceGraph?.nodes?.filter((n) => n.timestamp).slice(-1)[0]?.id)
                  const p = id ? nodePositions[id] : null
                  return p ? p.x + NODE_WIDTH + 12 : maxX - 220
                })(),
                top: (() => {
                  const atId = handoff.at_node
                  const id = atId || (traceGraph?.nodes?.filter((n) => n.timestamp).slice(-1)[0]?.id)
                  const p = id ? nodePositions[id] : null
                  return p ? p.y : 80
                })(),
                padding: '8px 12px',
                background: '#fff3e0',
                border: '2px solid #ff9800',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                color: '#e65100',
                maxWidth: '200px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
              title={`Motivo: ${handoff.reason || 'N/A'}\nRegra: ${handoff.rule || 'N/A'}`}
            >
              Handoff para humano
              <div style={{ fontSize: 10, fontWeight: 400, marginTop: 4, color: '#666' }}>
                {handoff.reason || handoff.rule || '—'}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: '8px 16px', fontSize: 11, color: '#666', borderTop: '1px solid #eee' }}>
        Legenda: <span style={{ marginLeft: 8 }}>◆ decisão (if/else)</span>
        <span style={{ marginLeft: 12 }}>— aresta tracejada = condicional</span>
        {traceGraph && (
          <span style={{ marginLeft: 12 }}>
            · Nós/arestas destacados = caminho da última execução
          </span>
        )}
      </div>
    </div>
  )
}
