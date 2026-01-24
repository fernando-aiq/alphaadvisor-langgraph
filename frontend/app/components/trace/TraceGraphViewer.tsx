'use client'

import { useMemo } from 'react'
import Card from '../Card'

interface Node {
  id: string
  label: string
  timestamp?: string
  duration_ms?: number
  data?: any
}

interface Edge {
  id: string
  source: string
  target: string
  label?: string
  timestamp?: string
}

interface TraceGraphData {
  trace_id: string
  nodes: Node[]
  edges: Edge[]
  route?: string
  intent?: string
  status?: string
}

interface TraceGraphViewerProps {
  data: TraceGraphData
}

export default function TraceGraphViewer({ data }: TraceGraphViewerProps) {
  const { nodes, edges, route, intent } = data

  // Determinar nós visitados (que têm timestamp)
  const visitedNodes = useMemo(() => {
    return new Set(nodes.filter(n => n.timestamp).map(n => n.id))
  }, [nodes])

  // Determinar edges percorridos (que têm timestamp)
  const visitedEdges = useMemo(() => {
    return new Set(edges.filter(e => e.timestamp).map(e => e.id))
  }, [edges])

  // Posicionamento simples dos nós (grid)
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const nodeOrder = ['detect_intent', 'route_decision', 'bypass_analysis', 'react_agent', 'format_response']
    const gridCols = 3
    const spacing = 200
    
    nodeOrder.forEach((nodeId, index) => {
      const row = Math.floor(index / gridCols)
      const col = index % gridCols
      positions[nodeId] = {
        x: col * spacing + 100,
        y: row * spacing + 100
      }
    })
    
    return positions
  }, [])

  const getNodeColor = (nodeId: string) => {
    // Cores mais vibrantes e consistentes
    if (!visitedNodes.has(nodeId)) return '#e0e0e0' // Não visitado - cinza claro
    if (nodeId === 'detect_intent') return '#4CAF50' // Verde - início do fluxo
    if (nodeId === 'route_decision') return '#2196F3' // Azul - decisão
    if (nodeId === 'bypass_analysis') return '#FF9800' // Laranja - análise direta
    if (nodeId === 'react_agent') return '#9C27B0' // Roxo - agente ReAct
    if (nodeId === 'format_response') return '#00BCD4' // Ciano - formatação final
    return '#757575' // Cinza padrão
  }

  const getNodeDescription = (nodeId: string) => {
    const descriptions: Record<string, string> = {
      'detect_intent': 'Detecta a intenção da mensagem do usuário usando análise de palavras-chave. Identifica se a pergunta é sobre carteira, adequação, diversificação, etc.',
      'route_decision': 'Decide qual rota seguir baseado na intenção detectada. Pode escolher "bypass" para análises simples ou "react" para raciocínio complexo.',
      'bypass_analysis': 'Análise direta sem agente ReAct. Usado para intenções simples como obter carteira, onde uma sequência fixa de ferramentas é suficiente.',
      'react_agent': 'Agente ReAct que usa ferramentas e raciocina passo a passo. Usado para perguntas complexas que requerem múltiplas iterações de pensamento, ação e observação.',
      'format_response': 'Formata a resposta final para o usuário, garantindo que seja clara, estruturada e útil.'
    }
    return descriptions[nodeId] || 'Nó do grafo de processamento'
  }

  const getNodeBorder = (nodeId: string) => {
    if (route === 'bypass' && nodeId === 'bypass_analysis') return '3px solid #FF9800'
    if (route === 'react' && nodeId === 'react_agent') return '3px solid #9C27B0'
    return '2px solid #ccc'
  }

  return (
    <Card className="trace-graph-viewer" style={{ padding: '1.5rem', height: '600px', overflow: 'auto' }}>
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>Fluxo do Grafo</h3>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>
            {visitedNodes.size > 0 && (
              <span>Nós visitados: <strong>{visitedNodes.size}</strong> de {nodes.length}</span>
            )}
          </div>
        </div>
        <div style={{ fontSize: '0.9rem', color: '#666' }}>
          {intent && (
            <span>
              Intenção: <strong>{intent}</strong>
              <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: '#999' }} title="Intenção detectada da mensagem do usuário">ℹ️</span>
            </span>
          )}
          {route && (
            <span style={{ marginLeft: '1rem' }}>
              Rota: <strong>{route}</strong>
              <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: '#999' }} title="Rota escolhida pelo grafo (bypass para análises simples, react para raciocínio complexo)">ℹ️</span>
            </span>
          )}
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', height: '500px', border: '1px solid #e0e0e0', borderRadius: '8px', background: '#f9f9f9' }}>
        {/* Renderizar edges */}
        <svg style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none' }}>
          {edges.map((edge) => {
            const sourcePos = nodePositions[edge.source]
            const targetPos = nodePositions[edge.target]
            if (!sourcePos || !targetPos) return null

            const isVisited = visitedEdges.has(edge.id)
            const strokeColor = isVisited ? '#2196F3' : '#e0e0e0'
            const strokeWidth = isVisited ? 2 : 1
            const strokeDasharray = isVisited ? 'none' : '5,5'

            return (
              <g key={edge.id}>
                <line
                  x1={sourcePos.x + 60}
                  y1={sourcePos.y + 30}
                  x2={targetPos.x + 60}
                  y2={targetPos.y + 30}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDasharray}
                  markerEnd="url(#arrowhead)"
                />
                {edge.label && (
                  <text
                    x={(sourcePos.x + targetPos.x) / 2 + 60}
                    y={(sourcePos.y + targetPos.y) / 2 + 25}
                    fontSize="10"
                    fill="#666"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            )
          })}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#2196F3" />
            </marker>
          </defs>
        </svg>

        {/* Renderizar nós */}
        {nodes.map((node) => {
          const pos = nodePositions[node.id]
          if (!pos) return null

          const isVisited = visitedNodes.has(node.id)
          const bgColor = getNodeColor(node.id)
          const border = getNodeBorder(node.id)

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                left: `${pos.x}px`,
                top: `${pos.y}px`,
                width: '140px',
                padding: '0.75rem',
                backgroundColor: bgColor,
                border: border,
                borderRadius: '8px',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                opacity: isVisited ? 1 : 0.5,
                boxShadow: isVisited ? '0 2px 8px rgba(0,0,0,0.15)' : 'none'
              }}
              title={`${node.label}\n\n${getNodeDescription(node.id)}\n\n${node.timestamp ? `Executado: ${new Date(node.timestamp).toLocaleTimeString()}` : 'Não executado'}\n${node.duration_ms ? `Duração: ${node.duration_ms.toFixed(0)}ms` : ''}\n\n${node.data?.input ? `Input: ${JSON.stringify(node.data.input).substring(0, 50)}...` : ''}\n${node.data?.output ? `Output: ${JSON.stringify(node.data.output).substring(0, 50)}...` : ''}`}
            >
              <div style={{ fontSize: '0.85rem', fontWeight: '600', color: '#333' }}>
                {node.label}
              </div>
              {node.duration_ms && (
                <div style={{ fontSize: '0.7rem', color: '#666', marginTop: '0.25rem' }}>
                  {node.duration_ms.toFixed(0)}ms
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#666' }}>
        <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Legenda:</div>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div title="Nó que foi executado durante o processamento">
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#4CAF50', borderRadius: '2px', marginRight: '0.5rem' }}></span>
            Nó visitado
          </div>
          <div title="Nó que não foi executado (caminho não seguido)">
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#e0e0e0', borderRadius: '2px', marginRight: '0.5rem' }}></span>
            Nó não visitado
          </div>
          <div title="Transição (edge) que foi percorrida entre nós">
            <span style={{ display: 'inline-block', width: '12px', height: '12px', border: '2px solid #2196F3', borderRadius: '2px', marginRight: '0.5rem' }}></span>
            Edge percorrido
          </div>
        </div>
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', backgroundColor: '#f5f5f5', borderRadius: '4px', fontSize: '0.8rem' }}>
          <strong>Dica:</strong> Passe o mouse sobre os nós para ver mais detalhes sobre sua execução, incluindo input, output e duração.
        </div>
      </div>
    </Card>
  )
}

