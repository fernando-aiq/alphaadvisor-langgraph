'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import TraceHeader from './TraceHeader'
import TraceSidebar from './TraceSidebar'
import TraceGraphViewer from './TraceGraphViewer'
import TraceTimelineViewer from './TraceTimelineViewer'
import Card from '../Card'

interface TraceViewerContainerProps {
  traceId: string
}

const getApiUrl = () => {
  // Para endpoints de trace, sempre usar API routes do Next.js (relativo)
  // Não usar NEXT_PUBLIC_API_URL que é para LangGraph Deployment
  return ''
}

type ViewMode = 'graph' | 'timeline'

export default function TraceViewerContainer({ traceId }: TraceViewerContainerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('graph')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [traceData, setTraceData] = useState<any>(null)
  const [graphData, setGraphData] = useState<any>(null)
  const [stepsData, setStepsData] = useState<any>(null)
  const [timelineData, setTimelineData] = useState<any>(null)
  const [toolsData, setToolsData] = useState<any>(null)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      setError(null)
      const apiUrl = getApiUrl()

      try {
        // Carregar dados em paralelo
        const base = apiUrl || ''
        const [traceRes, graphRes, stepsRes, timelineRes, toolsRes] = await Promise.all([
          axios.get(`${base}/api/trace/${traceId}`),
          axios.get(`${base}/api/trace/${traceId}/graph`),
          axios.get(`${base}/api/trace/${traceId}/steps`),
          axios.get(`${base}/api/trace/${traceId}/timeline`),
          axios.get(`${base}/api/trace/${traceId}/tools`).catch(() => ({ data: null }))
        ])

        setTraceData(traceRes.data)
        setGraphData(graphRes.data)
        setStepsData(stepsRes.data)
        setTimelineData(timelineRes.data)
        setToolsData(toolsRes.data)
      } catch (err: any) {
        console.error('Erro ao carregar trace:', err)
        setError(err.response?.data?.error || err.message || 'Erro ao carregar trace')
      } finally {
        setLoading(false)
      }
    }

    if (traceId) {
      loadData()
    }
  }, [traceId])

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId)
    // Abrir sidebar se estiver fechada
    if (!sidebarOpen) {
      setSidebarOpen(true)
    }
  }

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '400px',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{ fontSize: '1.125rem', color: '#6b7280' }}>Carregando trace...</div>
      </div>
    )
  }

  if (error) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ color: '#ef4444', fontSize: '1rem', marginBottom: '0.5rem' }}>Erro ao carregar trace</div>
        <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>{error}</div>
      </Card>
    )
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: 'calc(100vh - 80px)',
      overflow: 'hidden',
      backgroundColor: 'white'
    }}>
      {/* Header */}
      <TraceHeader
        traceId={traceId}
        traceData={traceData}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
      />

      {/* Main Content Area */}
      <div style={{ 
        display: 'flex', 
        flex: 1, 
        overflow: 'hidden'
      }}>
        {/* Sidebar */}
        {sidebarOpen && (
          <TraceSidebar
            traceData={traceData}
            stepsData={stepsData}
            toolsData={toolsData}
            selectedRunId={selectedNodeId}
            onSelectRun={setSelectedNodeId}
          />
        )}

        {/* Main Visualization Area */}
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden',
          backgroundColor: '#f9fafb'
        }}>
          {/* View Mode Toggle */}
          <div style={{
            padding: '0.75rem 1rem',
            borderBottom: '1px solid #e5e7eb',
            backgroundColor: 'white',
            display: 'flex',
            gap: '0.5rem'
          }}>
            <button
              onClick={() => setViewMode('graph')}
              style={{
                padding: '0.5rem 1rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                backgroundColor: viewMode === 'graph' ? '#3b82f6' : 'white',
                color: viewMode === 'graph' ? 'white' : '#374151',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
            >
              Grafo
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              style={{
                padding: '0.5rem 1rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                backgroundColor: viewMode === 'timeline' ? '#3b82f6' : 'white',
                color: viewMode === 'timeline' ? 'white' : '#374151',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s'
              }}
            >
              Timeline
            </button>
          </div>

          {/* Visualization */}
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            {viewMode === 'graph' && graphData && (
              <TraceGraphViewer
                data={graphData}
                onNodeClick={handleNodeClick}
                selectedNodeId={selectedNodeId}
              />
            )}
            {viewMode === 'timeline' && timelineData && (
              <div style={{ height: '100%', overflow: 'auto', padding: '1rem' }}>
                <TraceTimelineViewer data={timelineData} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
