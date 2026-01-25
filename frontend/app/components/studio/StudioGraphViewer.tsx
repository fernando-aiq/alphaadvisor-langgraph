'use client'

import { useMemo } from 'react'
import { GraphStructure, ThreadState, Run } from '@/app/lib/studio/langsmith-client'

interface StudioGraphViewerProps {
  graphStructure: GraphStructure
  threadState?: ThreadState
  runs?: Run[]
}

const NODE_WIDTH = 140
const NODE_HEIGHT = 60
const OFFSET_X = 70
const OFFSET_Y = 30

export default function StudioGraphViewer({
  graphStructure,
  threadState,
  runs = [],
}: StudioGraphViewerProps) {
  const { nodes, edges, entry_point } = graphStructure

  // Determinar nós visitados baseado em threadState.next e histórico
  const visitedNodes = useMemo(() => {
    const visited = new Set<string>()
    
    if (!threadState) return visited

    // Adicionar entry point como visitado
    if (entry_point) {
      visited.add(entry_point)
    }

    // Analisar mensagens para inferir nós visitados
    const messages = threadState.values?.messages || []
    
    // Se há mensagens tool, o nó 'tools' foi visitado
    const hasToolMessages = messages.some(m => m.type === 'tool')
    if (hasToolMessages) {
      visited.add('tools')
    }

    // Se há mensagens ai, o nó 'agent' foi visitado
    const hasAiMessages = messages.some(m => m.type === 'ai')
    if (hasAiMessages) {
      visited.add('agent')
    }

    // Se há tool_calls nas mensagens ai, o nó 'tools' foi visitado
    const hasToolCalls = messages.some(m => m.type === 'ai' && m.tool_calls && m.tool_calls.length > 0)
    if (hasToolCalls) {
      visited.add('tools')
    }

    // Se threadState.next existe, todos os nós anteriores foram visitados
    // Construir caminho baseado na estrutura do grafo
    if (threadState.next && threadState.next.length > 0) {
      const nextNode = threadState.next[0]
      
      // Se next é 'end', então todos os nós principais foram visitados
      if (nextNode === 'end' || nextNode === '__end__') {
        visited.add('init')
        visited.add('agent')
        if (hasToolMessages || hasToolCalls) {
          visited.add('tools')
        }
        visited.add('end')
      } else {
        // Adicionar nós no caminho até o próximo nó
        visited.add('init')
        visited.add('agent')
        if (nextNode === 'tools' || hasToolMessages || hasToolCalls) {
          visited.add('tools')
        }
      }
    } else {
      // Se não há next, assumir que chegou ao fim
      visited.add('init')
      visited.add('agent')
      if (hasToolMessages || hasToolCalls) {
        visited.add('tools')
      }
      visited.add('end')
    }

    return visited
  }, [threadState, entry_point])

  // Determinar próximo nó (atual)
  const currentNode = useMemo(() => {
    if (!threadState?.next || threadState.next.length === 0) {
      return null
    }
    return threadState.next[0]
  }, [threadState])

  // Determinar edges percorridos
  const visitedEdges = useMemo(() => {
    const visited = new Set<string>()
    
    if (!threadState) return visited

    const visitedNodeList = Array.from(visitedNodes)
    
    // Para cada par de nós visitados consecutivos, marcar edge como visitado
    for (let i = 0; i < visitedNodeList.length - 1; i++) {
      const source = visitedNodeList[i]
      const target = visitedNodeList[i + 1]
      visited.add(`${source}->${target}`)
    }

    // Adicionar edges específicos baseados no caminho
    if (visitedNodes.has('init')) {
      visited.add('START->init')
      visited.add('init->agent')
    }
    
    if (visitedNodes.has('agent')) {
      const hasToolCalls = threadState.values?.messages?.some(
        m => m.type === 'ai' && m.tool_calls && m.tool_calls.length > 0
      )
      
      if (hasToolCalls && visitedNodes.has('tools')) {
        visited.add('agent->tools')
        visited.add('tools->agent')
      } else if (!hasToolCalls && visitedNodes.has('end')) {
        visited.add('agent->end')
      }
    }

    if (visitedNodes.has('end')) {
      visited.add('end->END')
    }

    return visited
  }, [visitedNodes, threadState])

  // Posicionamento dos nós (layout horizontal simples)
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const spacing = 250
    const startY = 100
    
    // Ordem dos nós no layout
    const nodeOrder = ['START', 'init', 'agent', 'tools', 'end', 'END']
    
    nodeOrder.forEach((nodeId, index) => {
      // Verificar se o nó existe na estrutura
      const exists = nodes.some(n => n.id === nodeId) || ['START', 'END'].includes(nodeId)
      if (exists) {
        positions[nodeId] = {
          x: index * spacing + 100,
          y: startY
        }
      }
    })

    // Adicionar posições para nós não na ordem padrão
    nodes.forEach((node, idx) => {
      if (!positions[node.id]) {
        const orderIndex = nodeOrder.length + idx
        positions[node.id] = {
          x: orderIndex * spacing + 100,
          y: startY + 150 // Linha abaixo
        }
      }
    })

    return positions
  }, [nodes])

  const maxX = useMemo(() => {
    let m = 0
    Object.values(nodePositions).forEach(pos => {
      m = Math.max(m, pos.x + NODE_WIDTH)
    })
    return Math.max(m, 900)
  }, [nodePositions])

  const maxY = useMemo(() => {
    let m = 0
    Object.values(nodePositions).forEach(pos => {
      m = Math.max(m, pos.y + NODE_HEIGHT)
    })
    return Math.max(m, 300)
  }, [nodePositions])

  const getNodeColor = (nodeId: string) => {
    const isVisited = visitedNodes.has(nodeId)
    const isCurrent = currentNode === nodeId

    if (isCurrent) return '#FFC107' // Amarelo - nó atual
    if (!isVisited) return '#e0e0e0' // Cinza - não visitado
    if (nodeId === entry_point || nodeId === 'init') return '#4CAF50' // Verde - entry point
    if (nodeId === 'end' || nodeId === 'END') return '#F44336' // Vermelho - end point
    if (nodeId === 'agent') return '#2196F3' // Azul - agente
    if (nodeId === 'tools') return '#FF9800' // Laranja - ferramentas
    return '#9E9E9E' // Cinza padrão
  }

  const getNodeBorder = (nodeId: string) => {
    const isCurrent = currentNode === nodeId
    if (isCurrent) return '3px solid #FF6F00'
    if (nodeId === entry_point || nodeId === 'init') return '2px solid #2E7D32'
    if (nodeId === 'end' || nodeId === 'END') return '2px solid #C62828'
    return '2px solid #757575'
  }

  const getEdgeStyle = (source: string, target: string) => {
    const edgeKey = `${source}->${target}`
    const isVisited = visitedEdges.has(edgeKey)
    
    return {
      stroke: isVisited ? '#2196F3' : '#bdbdbd',
      strokeWidth: isVisited ? 2.5 : 1.5,
      strokeDasharray: isVisited ? 'none' : '5,5',
    }
  }

  const getNodeLabel = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId)
    if (node) return node.label || node.name || nodeId
    
    // Labels para nós especiais
    if (nodeId === 'START') return 'Início'
    if (nodeId === 'END') return 'Fim'
    return nodeId
  }

  const getNodeDescription = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId)
    if (node?.type) {
      const descriptions: Record<string, string> = {
        'init': 'Inicializa o estado da thread e prepara o contexto',
        'agent': 'Agente LLM que processa mensagens e decide quais ferramentas usar',
        'tool': 'Executa ferramentas (tools) solicitadas pelo agente',
        'end': 'Finaliza a execução e retorna a resposta final',
      }
      return descriptions[node.type] || `Nó do tipo ${node.type}`
    }
    return 'Nó do grafo LangGraph'
  }

  // Criar lista completa de edges incluindo START e END
  const allEdges = useMemo(() => {
    const result = [...edges]
    
    // Adicionar edges para START e END se necessário
    if (entry_point) {
      result.push({ source: 'START', target: entry_point })
    }
    
    // Adicionar edge de end para END se houver nó end
    const endNode = nodes.find(n => n.id === 'end')
    if (endNode) {
      result.push({ source: 'end', target: 'END' })
    }
    
    return result
  }, [edges, entry_point, nodes])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fafafa' }}>
      <div style={{ padding: '12px 16px', background: 'white', borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>Visualização do Grafo</h3>
        <div style={{ marginTop: '4px', fontSize: '13px', color: '#666' }}>
          {nodes.length} nós, {allEdges.length} arestas
          {currentNode && (
            <span style={{ marginLeft: '12px', color: '#FF6F00', fontWeight: '600' }}>
              · Próximo nó: {getNodeLabel(currentNode)}
            </span>
          )}
          {visitedNodes.size > 0 && (
            <span style={{ marginLeft: '12px' }}>
              · Nós visitados: {visitedNodes.size}/{nodes.length}
            </span>
          )}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '1rem', minHeight: '400px' }}>
        <div
          style={{
            position: 'relative',
            width: maxX,
            height: maxY,
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            background: '#fff',
            minHeight: '300px',
          }}
        >
          {/* Renderizar edges */}
          <svg
            style={{
              position: 'absolute',
              width: maxX,
              height: maxY,
              pointerEvents: 'none',
              overflow: 'visible',
            }}
          >
            <defs>
              <marker
                id="sgv-arrow"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#bdbdbd" />
              </marker>
              <marker
                id="sgv-arrow-visited"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#2196F3" />
              </marker>
            </defs>
            {allEdges.map((edge, idx) => {
              const sp = nodePositions[edge.source]
              const tp = nodePositions[edge.target]
              if (!sp || !tp) return null

              const x1 = sp.x + OFFSET_X
              const y1 = sp.y + OFFSET_Y
              const x2 = tp.x + OFFSET_X
              const y2 = tp.y + OFFSET_Y
              const style = getEdgeStyle(edge.source, edge.target)
              const isVisited = visitedEdges.has(`${edge.source}->${edge.target}`)

              return (
                <g key={`${edge.source}-${edge.target}-${idx}`}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={style.stroke}
                    strokeWidth={style.strokeWidth}
                    strokeDasharray={style.strokeDasharray}
                    markerEnd={`url(#sgv-arrow${isVisited ? '-visited' : ''})`}
                  />
                  {edge.condition && (
                    <text
                      x={(x1 + x2) / 2}
                      y={(y1 + y2) / 2 - 6}
                      fontSize="10"
                      fill={isVisited ? '#1976D2' : '#666'}
                      textAnchor="middle"
                      fontWeight={600}
                    >
                      {edge.condition}
                    </text>
                  )}
                </g>
              )
            })}
          </svg>

          {/* Renderizar nós */}
          {[...nodes, { id: 'START', name: 'START', type: 'start', label: 'Início' }, { id: 'END', name: 'END', type: 'end', label: 'Fim' }]
            .filter(node => nodePositions[node.id])
            .map((node) => {
              const pos = nodePositions[node.id]
              if (!pos) return null

              const isVisited = visitedNodes.has(node.id)
              const isCurrent = currentNode === node.id
              const bgColor = getNodeColor(node.id)
              const border = getNodeBorder(node.id)
              const label = getNodeLabel(node.id)
              const description = getNodeDescription(node.id)

              return (
                <div
                  key={node.id}
                  style={{
                    position: 'absolute',
                    left: pos.x,
                    top: pos.y,
                    width: `${NODE_WIDTH}px`,
                    minHeight: `${NODE_HEIGHT}px`,
                    padding: '8px 10px',
                    backgroundColor: bgColor,
                    border: border,
                    borderRadius: '8px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#333',
                    boxSizing: 'border-box',
                    opacity: isVisited ? 1 : 0.5,
                    boxShadow: isVisited || isCurrent ? '0 2px 8px rgba(0,0,0,0.15)' : 'none',
                    transition: 'all 0.2s',
                  }}
                  title={`${label}\n\n${description}\n\n${isCurrent ? 'Próximo nó a ser executado' : isVisited ? 'Nó visitado' : 'Nó não visitado'}`}
                >
                  {label}
                  {isCurrent && (
                    <div style={{ fontSize: '9px', color: '#FF6F00', marginTop: '4px', fontWeight: 700 }}>
                      ● PRÓXIMO
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      </div>

      <div style={{ padding: '8px 16px', fontSize: '11px', color: '#666', borderTop: '1px solid #eee', background: 'white' }}>
        <div style={{ fontWeight: '600', marginBottom: '4px' }}>Legenda:</div>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#4CAF50', borderRadius: '2px', marginRight: '6px' }}></span>
            Entry point
          </div>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#2196F3', borderRadius: '2px', marginRight: '6px' }}></span>
            Nó visitado
          </div>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#FFC107', borderRadius: '2px', marginRight: '6px' }}></span>
            Próximo nó
          </div>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#F44336', borderRadius: '2px', marginRight: '6px' }}></span>
            End point
          </div>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#e0e0e0', borderRadius: '2px', marginRight: '6px' }}></span>
            Nó não visitado
          </div>
          <div>
            <span style={{ display: 'inline-block', width: '12px', height: '0', border: '2px solid #2196F3', marginRight: '6px', marginTop: '6px' }}></span>
            Aresta percorrida
          </div>
        </div>
      </div>
    </div>
  )
}
