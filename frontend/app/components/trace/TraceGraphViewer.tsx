'use client'

import { useMemo, useCallback, useEffect } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Panel
} from 'reactflow'
import 'reactflow/dist/style.css'
import dagre from 'dagre'

interface TraceNode {
  id: string
  label: string
  type?: string
  timestamp?: string
  duration_ms?: number
  status?: string
  data?: {
    input?: any
    output?: any
    metadata?: any
  }
}

interface TraceEdge {
  id: string
  source: string
  target: string
  label?: string
  timestamp?: string
}

interface TraceGraphData {
  trace_id: string
  nodes: TraceNode[]
  edges: TraceEdge[]
  route?: string
  intent?: string
  status?: string
}

interface TraceGraphViewerProps {
  data: TraceGraphData
  onNodeClick?: (nodeId: string) => void
  selectedNodeId?: string | null
}

// Custom node component
function CustomNode({ data }: { data: any }) {
  const { label, type, status, duration_ms, isVisited } = data

  const getNodeColor = () => {
    if (!isVisited) return '#e5e7eb'
    
    const nodeType = type || 'unknown'
    if (nodeType === 'tool') return '#f59e0b'
    if (nodeType === 'llm' || nodeType === 'chat') return '#3b82f6'
    if (nodeType === 'chain') return '#10b981'
    if (nodeType === 'retriever') return '#8b5cf6'
    if (status === 'error') return '#ef4444'
    
    return '#6b7280'
  }

  const getBorderColor = () => {
    if (status === 'error') return '#ef4444'
    if (status === 'success') return '#10b981'
    if (isVisited) return '#3b82f6'
    return '#d1d5db'
  }

  return (
    <div
      style={{
        backgroundColor: getNodeColor(),
        border: `2px solid ${getBorderColor()}`,
        borderRadius: '8px',
        padding: '0.75rem',
        minWidth: '140px',
        textAlign: 'center',
        boxShadow: isVisited ? '0 2px 8px rgba(0,0,0,0.15)' : 'none',
        opacity: isVisited ? 1 : 0.6,
        transition: 'all 0.2s'
      }}
    >
      <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111827', marginBottom: '0.25rem' }}>
        {label}
      </div>
      {type && (
        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
          {type}
        </div>
      )}
      {duration_ms && (
        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
          {duration_ms.toFixed(0)}ms
        </div>
      )}
    </div>
  )
}

const nodeTypes = {
  custom: CustomNode
}

// Layout com dagre
function getLayoutedElements(nodes: Node[], edges: Edge[], direction = 'TB') {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: direction, nodesep: 100, ranksep: 150 })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 160, height: 100 })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    node.targetPosition = 'top' as any
    node.sourcePosition = 'bottom' as any
    node.position = {
      x: nodeWithPosition.x - 80,
      y: nodeWithPosition.y - 50
    }
  })

  return { nodes, edges }
}

export default function TraceGraphViewer({ 
  data, 
  onNodeClick,
  selectedNodeId 
}: TraceGraphViewerProps) {
  const { nodes: traceNodes, edges: traceEdges } = data

  // Determinar nós visitados
  const visitedNodes = useMemo(() => {
    return new Set(traceNodes.filter(n => n.timestamp).map(n => n.id))
  }, [traceNodes])

  // Converter para formato ReactFlow
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = traceNodes.map((node) => {
      const nodeType = (node as any).type || 'unknown'
      return {
        id: node.id,
        type: 'custom',
        data: {
          label: node.label,
          type: nodeType,
          status: (node as any).status,
          duration_ms: node.duration_ms,
          isVisited: visitedNodes.has(node.id),
          input: node.data?.input,
          output: node.data?.output,
          metadata: node.data?.metadata
        },
        position: { x: 0, y: 0 } // Será calculado pelo dagre
      }
    })

    const edges: Edge[] = traceEdges.map((edge) => {
      const isVisited = visitedNodes.has(edge.source) && visitedNodes.has(edge.target)
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: isVisited,
        style: {
          stroke: isVisited ? '#3b82f6' : '#d1d5db',
          strokeWidth: isVisited ? 2 : 1
        },
        markerEnd: {
          type: 'arrowclosed',
          color: isVisited ? '#3b82f6' : '#d1d5db'
        }
      }
    })

    // Aplicar layout
    const layouted = getLayoutedElements(nodes, edges)
    return { initialNodes: layouted.nodes, initialEdges: layouted.edges }
  }, [traceNodes, traceEdges, visitedNodes])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Atualizar quando dados mudarem
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = getLayoutedElements(initialNodes, initialEdges)
    setNodes(newNodes)
    setEdges(newEdges)
  }, [initialNodes, initialEdges, setNodes, setEdges])

  const onNodeClickHandler = useCallback((event: React.MouseEvent, node: Node) => {
    if (onNodeClick) {
      onNodeClick(node.id)
    }
  }, [onNodeClick])

  // Destacar nó selecionado
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        const isSelected = node.id === selectedNodeId
        return {
          ...node,
          selected: isSelected,
          style: {
            ...node.style,
            border: isSelected ? '3px solid #3b82f6' : node.style?.border
          }
        }
      })
    )
  }, [selectedNodeId, setNodes])

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-left"
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as any
            if (!data?.isVisited) return '#e5e7eb'
            const type = data.type || 'unknown'
            if (type === 'tool') return '#f59e0b'
            if (type === 'llm' || type === 'chat') return '#3b82f6'
            if (type === 'chain') return '#10b981'
            return '#6b7280'
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Panel position="top-left" style={{ backgroundColor: 'white', padding: '0.5rem', borderRadius: '6px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Nós visitados: <strong style={{ color: '#111827' }}>{visitedNodes.size}</strong> de {traceNodes.length}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
