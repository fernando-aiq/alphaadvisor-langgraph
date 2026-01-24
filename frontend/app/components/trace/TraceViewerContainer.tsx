'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import TraceGraphViewer from './TraceGraphViewer'
import TraceStepViewer from './TraceStepViewer'
import TraceTimelineViewer from './TraceTimelineViewer'
import TraceDetailsPanel from './TraceDetailsPanel'
import TraceHelpPanel from './TraceHelpPanel'
import TraceToolsViewer from './TraceToolsViewer'
import Card from '../Card'

interface TraceViewerContainerProps {
  traceId: string
}

const getApiUrl = () => {
  const fallbackUrl = 'http://localhost:8000'
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || fallbackUrl
  }
  const isVercel = window.location.hostname.includes('vercel.app') ||
                   window.location.hostname.includes('vercel.com')
  if (isVercel) {
    return process.env.NEXT_PUBLIC_API_URL || ''
  }
  return process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || 'http://localhost:8000'
}

type TabType = 'graph' | 'steps' | 'timeline' | 'details' | 'tools' | 'help'

export default function TraceViewerContainer({ traceId }: TraceViewerContainerProps) {
  const [activeTab, setActiveTab] = useState<TabType>('graph')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [traceData, setTraceData] = useState<any>(null)
  const [graphData, setGraphData] = useState<any>(null)
  const [stepsData, setStepsData] = useState<any>(null)
  const [timelineData, setTimelineData] = useState<any>(null)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      setError(null)
      const apiUrl = getApiUrl()

      try {
        // Carregar dados em paralelo
        const base = apiUrl || ''
        const [traceRes, graphRes, stepsRes, timelineRes] = await Promise.all([
          axios.get(`${base}/api/trace/${traceId}`),
          axios.get(`${base}/api/trace/${traceId}/graph`),
          axios.get(`${base}/api/trace/${traceId}/steps`),
          axios.get(`${base}/api/trace/${traceId}/timeline`)
        ])

        setTraceData(traceRes.data)
        setGraphData(graphRes.data)
        setStepsData(stepsRes.data)
        setTimelineData(timelineRes.data)
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

  if (loading) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div>Carregando trace...</div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ color: '#F44336' }}>Erro: {error}</div>
      </Card>
    )
  }

  const tabs = [
    { id: 'graph' as TabType, label: 'Grafo', icon: '🔷' },
    { id: 'steps' as TabType, label: 'Passos', icon: '📝' },
    { id: 'timeline' as TabType, label: 'Timeline', icon: '⏱️' },
    { id: 'details' as TabType, label: 'Detalhes', icon: 'ℹ️' },
    { id: 'tools' as TabType, label: 'Tools', icon: '🔧' },
    { id: 'help' as TabType, label: 'Ajuda', icon: '❓' }
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Tabs */}
      <Card style={{ padding: '0' }}>
        <div style={{ display: 'flex', borderBottom: '1px solid #e0e0e0' }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                padding: '1rem',
                border: 'none',
                backgroundColor: activeTab === tab.id ? '#f5f5f5' : 'transparent',
                borderBottom: activeTab === tab.id ? '2px solid #2196F3' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: activeTab === tab.id ? '600' : '400',
                transition: 'all 0.2s'
              }}
            >
              <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Conteúdo */}
      <div>
        {activeTab === 'graph' && graphData && (
          <TraceGraphViewer data={graphData} />
        )}
        {activeTab === 'steps' && stepsData && (
          <TraceStepViewer data={stepsData} />
        )}
        {activeTab === 'timeline' && timelineData && (
          <TraceTimelineViewer data={timelineData} />
        )}
        {activeTab === 'details' && traceData && (
          <TraceDetailsPanel trace={traceData} />
        )}
        {activeTab === 'tools' && (
          <TraceToolsViewer traceId={traceId} />
        )}
        {activeTab === 'help' && (
          <TraceHelpPanel />
        )}
      </div>
    </div>
  )
}

