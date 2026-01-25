'use client'

import { useMemo, useState, useRef, useEffect, useCallback } from 'react'
import { GraphStructure, ThreadState, Run } from '@/app/lib/studio/langsmith-client'

interface StudioGraphViewerProps {
  graphStructure: GraphStructure
  threadState?: ThreadState
  runs?: Run[]
}

// Constantes melhoradas
const NODE_WIDTH = 160
const NODE_HEIGHT = 80
const OFFSET_X = 80
const OFFSET_Y = 40
const LAYER_SPACING = 300
const NODE_SPACING = 200
const MIN_OPACITY = 0.7

// Ícones para tipos de nós
const getNodeIcon = (nodeId: string, nodeType?: string) => {
  if (nodeId === 'START' || nodeId === 'init') return '⚡'
  if (nodeId === 'agent' || nodeType === 'agent') return '🤖'
  if (nodeId === 'tools' || nodeType === 'tool') return '🔧'
  if (nodeId === 'end' || nodeId === 'END' || nodeType === 'end') return '✅'
  return '●'
}

export default function StudioGraphViewer({
  graphStructure,
  threadState,
  runs = [],
}: StudioGraphViewerProps) {
  const { nodes, edges, entry_point } = graphStructure

  // Estado para zoom e pan
  const [transform, setTransform] = useState({
    scale: 1,
    translateX: 0,
    translateY: 0
  })
  const [isDragging, setIsDragging] = useState(false)
  const [lastPanPoint, setLastPanPoint] = useState({ x: 0, y: 0 })
  const [initialTransform, setInitialTransform] = useState<{ scale: number; translateX: number; translateY: number } | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const graphContainerRef = useRef<HTMLDivElement>(null)

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
    if (threadState.next && threadState.next.length > 0) {
      const nextNode = threadState.next[0]
      
      if (nextNode === 'end' || nextNode === '__end__') {
        visited.add('init')
        visited.add('agent')
        if (hasToolMessages || hasToolCalls) {
          visited.add('tools')
        }
        visited.add('end')
      } else {
        visited.add('init')
        visited.add('agent')
        if (nextNode === 'tools' || hasToolMessages || hasToolCalls) {
          visited.add('tools')
        }
      }
    } else {
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

  // Layout hierárquico top-down baseado em camadas
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    
    // Definir camadas hierárquicas
    const layers: Record<number, string[]> = {
      0: ['START'],
      1: ['init'],
      2: ['agent'],
      3: ['tools'],
      4: ['end'],
      5: ['END'],
    }

    // Calcular posições baseadas em camadas
    const layerYPositions: Record<number, number> = {}
    const startY = 80
    
    // Calcular Y para cada camada
    Object.keys(layers).forEach((layerStr) => {
      const layer = parseInt(layerStr)
      layerYPositions[layer] = startY + layer * LAYER_SPACING
    })

    // Posicionar nós conhecidos nas camadas
    Object.entries(layers).forEach(([layerStr, nodeIds]) => {
      const layer = parseInt(layerStr)
      const nodesInLayer = nodeIds.filter(nodeId => {
        return nodes.some(n => n.id === nodeId) || ['START', 'END'].includes(nodeId)
      })
      
      if (nodesInLayer.length > 0) {
        const totalWidth = (nodesInLayer.length - 1) * NODE_SPACING
        const startX = Math.max(200, (1200 - totalWidth) / 2) // Centralizar
        
        nodesInLayer.forEach((nodeId, idx) => {
          positions[nodeId] = {
            x: startX + idx * NODE_SPACING,
            y: layerYPositions[layer]
          }
        })
      }
    })

    // Posicionar nós não mapeados em camada adicional
    const unmappedNodes = nodes.filter(n => !positions[n.id])
    if (unmappedNodes.length > 0) {
      const extraLayer = 6
      layerYPositions[extraLayer] = startY + extraLayer * LAYER_SPACING
      const totalWidth = (unmappedNodes.length - 1) * NODE_SPACING
      const startX = Math.max(200, (1200 - totalWidth) / 2)
      
      unmappedNodes.forEach((node, idx) => {
        positions[node.id] = {
          x: startX + idx * NODE_SPACING,
          y: layerYPositions[extraLayer]
        }
      })
    }

    return positions
  }, [nodes])

  // Criar lista completa de edges incluindo START e END
  const allEdges = useMemo(() => {
    const result = [...edges]
    
    if (entry_point) {
      result.push({ source: 'START', target: entry_point })
    }
    
    const endNode = nodes.find(n => n.id === 'end')
    if (endNode) {
      result.push({ source: 'end', target: 'END' })
    }
    
    return result
  }, [edges, entry_point, nodes])

  // Função auxiliar para determinar camada do nó
  function getNodeLayer(nodeId: string): number {
    if (nodeId === 'START') return 0
    if (nodeId === 'init') return 1
    if (nodeId === 'agent') return 2
    if (nodeId === 'tools') return 3
    if (nodeId === 'end') return 4
    if (nodeId === 'END') return 5
    return 6
  }

  // Detectar loops (arestas que voltam)
  const isLoop = useMemo(() => {
    const loopSet = new Set<string>()
    allEdges.forEach(edge => {
      const sourceLayer = getNodeLayer(edge.source)
      const targetLayer = getNodeLayer(edge.target)
      // Se target está em camada anterior ou igual, é um loop
      if (targetLayer <= sourceLayer && edge.source !== 'START' && edge.target !== 'END') {
        loopSet.add(`${edge.source}->${edge.target}`)
      }
    })
    return loopSet
  }, [allEdges])

  const maxX = useMemo(() => {
    let m = 0
    Object.values(nodePositions).forEach(pos => {
      m = Math.max(m, pos.x + NODE_WIDTH)
    })
    return Math.max(m, 1200)
  }, [nodePositions])

  const maxY = useMemo(() => {
    let m = 0
    Object.values(nodePositions).forEach(pos => {
      m = Math.max(m, pos.y + NODE_HEIGHT)
    })
    return Math.max(m, 600)
  }, [nodePositions])

  // Calcular escala inicial automática para caber na viewport
  useEffect(() => {
    let resizeTimeout: NodeJS.Timeout | null = null
    
    const calculateInitialScale = () => {
      if (!containerRef.current || maxX <= 0 || maxY <= 0) return
      
      const container = containerRef.current
      const containerWidth = container.clientWidth
      const containerHeight = container.clientHeight
      
      // Verificar se container tem dimensões válidas
      if (containerWidth <= 0 || containerHeight <= 0) return
      
      // Sem padding, usar margem de segurança menor já que área é maior
      const safetyMargin = 40 // Margem de segurança reduzida
      const totalPadding = safetyMargin * 2
      
      const availableWidth = containerWidth - totalPadding
      const availableHeight = containerHeight - totalPadding
      
      // Verificar se há espaço disponível
      if (availableWidth <= 0 || availableHeight <= 0) return
      
      // Calcular escala para caber em ambas dimensões
      const scaleX = availableWidth / maxX
      const scaleY = availableHeight / maxY
      
      // Usar menor escala com fator de segurança de 5%
      const rawScale = Math.min(scaleX, scaleY)
      const initialScale = rawScale * 0.95 // Fator de segurança de 5%
      
      // Centralizar o grafo
      const scaledWidth = maxX * initialScale
      const scaledHeight = maxY * initialScale
      const initialTranslateX = (containerWidth - scaledWidth) / 2
      const initialTranslateY = (containerHeight - scaledHeight) / 2
      
      // Validar que realmente cabe
      if (initialTranslateX < 0 || initialTranslateY < 0 || 
          scaledWidth > containerWidth || scaledHeight > containerHeight) {
        // Se não couber, reduzir escala adicional
        const adjustedScale = Math.min(
          (containerWidth - totalPadding) / maxX,
          (containerHeight - totalPadding) / maxY
        ) * 0.9
        const adjustedWidth = maxX * adjustedScale
        const adjustedHeight = maxY * adjustedScale
        const adjustedTransform = {
          scale: adjustedScale,
          translateX: (containerWidth - adjustedWidth) / 2,
          translateY: (containerHeight - adjustedHeight) / 2
        }
        setTransform(adjustedTransform)
        setInitialTransform(adjustedTransform)
        return
      }
      
      const initial = {
        scale: initialScale,
        translateX: initialTranslateX,
        translateY: initialTranslateY
      }
      
      setTransform(initial)
      setInitialTransform(initial)
    }
    
    // Usar delay maior e requestAnimationFrame para garantir renderização completa
    const initialTimeout = setTimeout(() => {
      requestAnimationFrame(() => {
        // Tentar calcular, se não funcionar, tentar novamente após pequeno delay
        calculateInitialScale()
        setTimeout(() => {
          if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect()
            if (rect.width > 0 && rect.height > 0) {
              calculateInitialScale()
            }
          }
        }, 50)
      })
    }, 100)
    
    // Recalcular ao redimensionar janela com debounce
    const handleResize = () => {
      if (resizeTimeout) {
        clearTimeout(resizeTimeout)
      }
      resizeTimeout = setTimeout(() => {
        requestAnimationFrame(() => {
          calculateInitialScale()
        })
      }, 150)
    }
    
    window.addEventListener('resize', handleResize)
    
    return () => {
      clearTimeout(initialTimeout)
      if (resizeTimeout) {
        clearTimeout(resizeTimeout)
      }
      window.removeEventListener('resize', handleResize)
    }
  }, [maxX, maxY])

  // Handlers de zoom e pan
  // Usar listener não-passive para permitir preventDefault
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const wheelHandler = (e: WheelEvent) => {
      e.preventDefault()
      
      if (!graphContainerRef.current) return

      const rect = container.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top

      const delta = e.deltaY > 0 ? 0.9 : 1.1
      const newScale = Math.max(0.2, Math.min(3.0, transform.scale * delta))

      // Zoom centrado no ponto do mouse
      const scaleChange = newScale / transform.scale
      const newTranslateX = mouseX - (mouseX - transform.translateX) * scaleChange
      const newTranslateY = mouseY - (mouseY - transform.translateY) * scaleChange

      setTransform({
        scale: newScale,
        translateX: newTranslateX,
        translateY: newTranslateY
      })
    }

    container.addEventListener('wheel', wheelHandler, { passive: false })

    return () => {
      container.removeEventListener('wheel', wheelHandler)
    }
  }, [transform])

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return // Apenas botão esquerdo
    setIsDragging(true)
    setLastPanPoint({ x: e.clientX, y: e.clientY })
    if (containerRef.current) {
      containerRef.current.style.cursor = 'grabbing'
    }
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return

    const deltaX = e.clientX - lastPanPoint.x
    const deltaY = e.clientY - lastPanPoint.y

    setTransform(prev => ({
      ...prev,
      translateX: prev.translateX + deltaX,
      translateY: prev.translateY + deltaY
    }))

    setLastPanPoint({ x: e.clientX, y: e.clientY })
  }, [isDragging, lastPanPoint])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    if (containerRef.current) {
      containerRef.current.style.cursor = 'grab'
    }
  }, [])

  // Event listeners para pan global
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  // Handlers de controles de zoom
  const handleZoomIn = useCallback(() => {
    if (!containerRef.current) return
    const container = containerRef.current
    const centerX = container.clientWidth / 2
    const centerY = container.clientHeight / 2

    const newScale = Math.min(3.0, transform.scale * 1.2)
    const scaleChange = newScale / transform.scale
    const newTranslateX = centerX - (centerX - transform.translateX) * scaleChange
    const newTranslateY = centerY - (centerY - transform.translateY) * scaleChange

    setTransform({
      scale: newScale,
      translateX: newTranslateX,
      translateY: newTranslateY
    })
  }, [transform])

  const handleZoomOut = useCallback(() => {
    if (!containerRef.current) return
    const container = containerRef.current
    const centerX = container.clientWidth / 2
    const centerY = container.clientHeight / 2

    const newScale = Math.max(0.2, transform.scale / 1.2)
    const scaleChange = newScale / transform.scale
    const newTranslateX = centerX - (centerX - transform.translateX) * scaleChange
    const newTranslateY = centerY - (centerY - transform.translateY) * scaleChange

    setTransform({
      scale: newScale,
      translateX: newTranslateX,
      translateY: newTranslateY
    })
  }, [transform])

  const handleReset = useCallback(() => {
    if (!containerRef.current || maxX <= 0 || maxY <= 0) return
    
    const container = containerRef.current
    const containerWidth = container.clientWidth
    const containerHeight = container.clientHeight
    
    // Verificar se container tem dimensões válidas
    if (containerWidth <= 0 || containerHeight <= 0) {
      // Se não tiver dimensões válidas, usar initialTransform se disponível
      if (initialTransform) {
        setTransform(initialTransform)
      }
      return
    }
    
    // Sem padding, usar margem de segurança menor
    const safetyMargin = 40
    const totalPadding = safetyMargin * 2
    
    const availableWidth = containerWidth - totalPadding
    const availableHeight = containerHeight - totalPadding
    
    if (availableWidth <= 0 || availableHeight <= 0) {
      if (initialTransform) {
        setTransform(initialTransform)
      }
      return
    }
    
    const scaleX = availableWidth / maxX
    const scaleY = availableHeight / maxY
    const rawScale = Math.min(scaleX, scaleY)
    const resetScale = rawScale * 0.95 // Fator de segurança de 5%
    
    // Centralizar o grafo
    const scaledWidth = maxX * resetScale
    const scaledHeight = maxY * resetScale
    const resetTranslateX = (containerWidth - scaledWidth) / 2
    const resetTranslateY = (containerHeight - scaledHeight) / 2
    
    // Validar que realmente cabe
    if (resetTranslateX < 0 || resetTranslateY < 0 || 
        scaledWidth > containerWidth || scaledHeight > containerHeight) {
      // Se não couber, reduzir escala adicional
      const adjustedScale = Math.min(
        (containerWidth - totalPadding) / maxX,
        (containerHeight - totalPadding) / maxY
      ) * 0.9
      const adjustedWidth = maxX * adjustedScale
      const adjustedHeight = maxY * adjustedScale
      const resetTransform = {
        scale: adjustedScale,
        translateX: (containerWidth - adjustedWidth) / 2,
        translateY: (containerHeight - adjustedHeight) / 2
      }
      setTransform(resetTransform)
      setInitialTransform(resetTransform)
      return
    }
    
    const resetTransform = {
      scale: resetScale,
      translateX: resetTranslateX,
      translateY: resetTranslateY
    }
    
    setTransform(resetTransform)
    setInitialTransform(resetTransform)
  }, [maxX, maxY, initialTransform])

  // Cores melhoradas com gradientes sutis
  const getNodeColor = (nodeId: string) => {
    const isVisited = visitedNodes.has(nodeId)
    const isCurrent = currentNode === nodeId
    const node = nodes.find(n => n.id === nodeId)

    if (isCurrent) return 'linear-gradient(135deg, #FFC107 0%, #FFB300 100%)'
    if (!isVisited) return '#f5f5f5'
    if (nodeId === entry_point || nodeId === 'init') return 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)'
    if (nodeId === 'end' || nodeId === 'END') return 'linear-gradient(135deg, #F44336 0%, #e53935 100%)'
    if (nodeId === 'agent') return 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)'
    if (nodeId === 'tools') return 'linear-gradient(135deg, #FF9800 0%, #F57C00 100%)'
    return 'linear-gradient(135deg, #9E9E9E 0%, #757575 100%)'
  }

  const getNodeTextColor = (nodeId: string) => {
    const isVisited = visitedNodes.has(nodeId)
    const isCurrent = currentNode === nodeId
    
    if (isCurrent) return '#000'
    if (!isVisited) return '#666'
    // Texto branco para nós coloridos visitados
    if (nodeId === entry_point || nodeId === 'init' || nodeId === 'end' || nodeId === 'END' || 
        nodeId === 'agent' || nodeId === 'tools') {
      return '#fff'
    }
    return '#333'
  }

  const getNodeBorder = (nodeId: string) => {
    const isCurrent = currentNode === nodeId
    if (isCurrent) return '3px solid #FF6F00'
    if (nodeId === entry_point || nodeId === 'init') return '2px solid #2E7D32'
    if (nodeId === 'end' || nodeId === 'END') return '2px solid #C62828'
    return '2px solid #bdbdbd'
  }

  const getEdgeStyle = (source: string, target: string) => {
    const edgeKey = `${source}->${target}`
    const isVisited = visitedEdges.has(edgeKey)
    const isLoopEdge = isLoop.has(edgeKey)
    
    return {
      stroke: isVisited ? '#2196F3' : '#bdbdbd',
      strokeWidth: isVisited ? 3 : 2,
      strokeDasharray: isVisited ? 'none' : (isLoopEdge ? '6,4' : 'none'),
    }
  }

  // Calcular curva Bézier para loops
  const getCurvedPath = (x1: number, y1: number, x2: number, y2: number, isLoop: boolean) => {
    if (!isLoop) {
      return `M ${x1} ${y1} L ${x2} ${y2}`
    }
    
    // Curva para loop: descer, curvar à direita, subir
    const midX = (x1 + x2) / 2
    const midY = Math.max(y1, y2) + 100
    const controlX1 = x1 + (x2 - x1) * 0.5
    const controlY1 = y1 + 80
    const controlX2 = x2 - (x2 - x1) * 0.5
    const controlY2 = y2 + 80
    
    return `M ${x1} ${y1} Q ${controlX1} ${controlY1}, ${midX} ${midY} Q ${controlX2} ${controlY2}, ${x2} ${y2}`
  }

  const getNodeLabel = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId)
    if (node) return node.label || node.name || nodeId
    
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

      <div 
        ref={containerRef}
        style={{ 
          flex: 1, 
          overflow: 'hidden', 
          padding: 0,
          minHeight: '400px', 
          background: '#fff',
          backgroundImage: `
            linear-gradient(to right, #f0f0f0 1px, transparent 1px),
            linear-gradient(to bottom, #f0f0f0 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          position: 'relative',
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
        onMouseDown={handleMouseDown}
      >
        {/* Controles de Zoom */}
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          background: 'white',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          padding: '4px',
        }}>
          <button
            onClick={handleZoomIn}
            style={{
              width: '32px',
              height: '32px',
              border: '1px solid #e0e0e0',
              background: '#fff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '18px',
              fontWeight: 'bold',
              color: '#333',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f5f5f5'
              e.currentTarget.style.borderColor = '#2196F3'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#fff'
              e.currentTarget.style.borderColor = '#e0e0e0'
            }}
            title="Zoom In (+)"
          >
            +
          </button>
          <button
            onClick={handleZoomOut}
            style={{
              width: '32px',
              height: '32px',
              border: '1px solid #e0e0e0',
              background: '#fff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '18px',
              fontWeight: 'bold',
              color: '#333',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f5f5f5'
              e.currentTarget.style.borderColor = '#2196F3'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#fff'
              e.currentTarget.style.borderColor = '#e0e0e0'
            }}
            title="Zoom Out (-)"
          >
            −
          </button>
          <button
            onClick={handleReset}
            style={{
              width: '32px',
              height: '32px',
              border: '1px solid #e0e0e0',
              background: '#fff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#333',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f5f5f5'
              e.currentTarget.style.borderColor = '#2196F3'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#fff'
              e.currentTarget.style.borderColor = '#e0e0e0'
            }}
            title="Reset Zoom (0)"
          >
            ↺
          </button>
        </div>

        {/* Indicador de Zoom */}
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.9)',
          borderRadius: '4px',
          padding: '4px 8px',
          fontSize: '12px',
          fontWeight: '600',
          color: '#666',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}>
          {Math.round(transform.scale * 100)}%
        </div>

        <div
          ref={graphContainerRef}
          style={{
            position: 'relative',
            width: maxX,
            height: maxY,
            minHeight: '500px',
            transform: `translate(${transform.translateX}px, ${transform.translateY}px) scale(${transform.scale})`,
            transformOrigin: '0 0',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
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
              const edgeKey = `${edge.source}->${edge.target}`
              const isLoopEdge = isLoop.has(edgeKey)
              const style = getEdgeStyle(edge.source, edge.target)
              const isVisited = visitedEdges.has(edgeKey)
              const path = getCurvedPath(x1, y1, x2, y2, isLoopEdge)

              return (
                <g key={`${edge.source}-${edge.target}-${idx}`}>
                  <path
                    d={path}
                    fill="none"
                    stroke={style.stroke}
                    strokeWidth={style.strokeWidth}
                    strokeDasharray={style.strokeDasharray}
                    markerEnd={`url(#sgv-arrow${isVisited ? '-visited' : ''})`}
                  />
                  {edge.condition && (
                    <g>
                      <rect
                        x={(x1 + x2) / 2 - 30}
                        y={(y1 + y2) / 2 - 18}
                        width="60"
                        height="16"
                        fill="rgba(255, 255, 255, 0.9)"
                        stroke={isVisited ? '#2196F3' : '#bdbdbd'}
                        strokeWidth="1"
                        rx="4"
                      />
                      <text
                        x={(x1 + x2) / 2}
                        y={(y1 + y2) / 2 - 6}
                        fontSize="11"
                        fill={isVisited ? '#1976D2' : '#666'}
                        textAnchor="middle"
                        fontWeight={600}
                      >
                        {edge.condition}
                      </text>
                    </g>
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
              const textColor = getNodeTextColor(node.id)
              const border = getNodeBorder(node.id)
              const label = getNodeLabel(node.id)
              const description = getNodeDescription(node.id)
              const icon = getNodeIcon(node.id, node.type)
              const nodeType = nodes.find(n => n.id === node.id)?.type

              return (
                <div
                  key={node.id}
                  style={{
                    position: 'absolute',
                    left: pos.x,
                    top: pos.y,
                    width: `${NODE_WIDTH}px`,
                    minHeight: `${NODE_HEIGHT}px`,
                    padding: '12px 16px',
                    background: bgColor,
                    border: border,
                    borderRadius: '10px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 600,
                    color: textColor,
                    boxSizing: 'border-box',
                    opacity: isVisited ? 1 : MIN_OPACITY,
                    boxShadow: isVisited || isCurrent 
                      ? '0 4px 12px rgba(0,0,0,0.2)' 
                      : '0 2px 4px rgba(0,0,0,0.1)',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                  }}
                  onMouseEnter={(e) => {
                    e.stopPropagation()
                    e.currentTarget.style.transform = 'scale(1.05)'
                    e.currentTarget.style.zIndex = '10'
                  }}
                  onMouseLeave={(e) => {
                    e.stopPropagation()
                    e.currentTarget.style.transform = 'scale(1)'
                    e.currentTarget.style.zIndex = '1'
                  }}
                  onMouseDown={(e) => {
                    e.stopPropagation() // Prevenir pan quando clicar no nó
                  }}
                  title={`${label}\n\n${description}\n\n${isCurrent ? 'Próximo nó a ser executado' : isVisited ? 'Nó visitado' : 'Nó não visitado'}`}
                >
                  <div style={{ fontSize: '20px', lineHeight: '1' }}>{icon}</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, lineHeight: '1.2' }}>{label}</div>
                  {isCurrent && (
                    <div style={{ fontSize: '10px', color: '#000', marginTop: '2px', fontWeight: 700 }}>
                      PRÓXIMO
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      </div>

      <div style={{ padding: '12px 16px', fontSize: '12px', color: '#666', borderTop: '1px solid #eee', background: 'white' }}>
        <div style={{ fontWeight: '600', marginBottom: '6px' }}>Legenda:</div>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '16px' }}>⚡</span>
            <span>Entry point</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '16px' }}>🤖</span>
            <span>Agente</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '16px' }}>🔧</span>
            <span>Ferramentas</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '16px' }}>✅</span>
            <span>End point</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ display: 'inline-block', width: '16px', height: '0', border: '3px solid #2196F3', marginRight: '4px' }}></span>
            <span>Aresta percorrida</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ display: 'inline-block', width: '16px', height: '0', border: '2px dashed #bdbdbd', marginRight: '4px' }}></span>
            <span>Loop (feedback)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
