'use client'

import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import Card from '../Card'

interface TimelineEvent {
  type: string
  node?: string
  reasoning_type?: string
  tool?: string
  timestamp: string
  relative_time_ms: number
  duration_ms?: number
  label: string
}

interface TraceTimelineData {
  trace_id: string
  start_time: string
  end_time?: string
  timeline: TimelineEvent[]
  total_events: number
}

interface TraceTimelineViewerProps {
  data: TraceTimelineData
}

export default function TraceTimelineViewer({ data }: TraceTimelineViewerProps) {
  const { timeline, start_time, end_time } = data

  // Preparar dados para o gráfico
  const chartData = useMemo(() => {
    const maxTime = Math.max(...timeline.map(e => e.relative_time_ms), 0)
    const buckets: Record<number, { time: number; nodes: number; reasoning: number; duration: number }> = {}
    
    // Agrupar eventos em buckets de 100ms
    timeline.forEach(event => {
      const bucket = Math.floor(event.relative_time_ms / 100) * 100
      if (!buckets[bucket]) {
        buckets[bucket] = { time: bucket, nodes: 0, reasoning: 0, duration: 0 }
      }
      
      if (event.type === 'node_execution') {
        buckets[bucket].nodes++
        if (event.duration_ms) {
          buckets[bucket].duration += event.duration_ms
        }
      } else if (event.type === 'reasoning') {
        buckets[bucket].reasoning++
      }
    })
    
    return Object.values(buckets).sort((a, b) => a.time - b.time)
  }, [timeline])

  // Timeline detalhada
  const timelineList = useMemo(() => {
    return timeline.map((event, index) => ({
      ...event,
      index,
      formattedTime: `${(event.relative_time_ms / 1000).toFixed(2)}s`
    }))
  }, [timeline])

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <Card className="trace-timeline-viewer" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>Timeline Cronológica</h3>
        <div style={{ fontSize: '0.9rem', color: '#666' }}>
          {start_time && (
            <span>
              Início: {new Date(start_time).toLocaleString()}
              <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: '#999' }} title="Momento em que o trace foi iniciado">ℹ️</span>
            </span>
          )}
          {end_time && (
            <span style={{ marginLeft: '1rem' }}>
              Fim: {new Date(end_time).toLocaleString()}
              <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: '#999' }} title="Momento em que o trace foi finalizado">ℹ️</span>
            </span>
          )}
        </div>
      </div>

      {/* Gráfico de barras */}
      <div style={{ marginBottom: '2rem' }}>
        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Distribuição Temporal
          <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Gráfico mostrando quando os eventos ocorreram ao longo do tempo">ℹ️</span>
        </h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Tempo (ms)', position: 'insideBottom', offset: -5 }}
              tickFormatter={(value) => formatTime(value)}
            />
            <YAxis label={{ value: 'Eventos', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: any, name: string) => {
                if (name === 'duration') return formatTime(value)
                return value
              }}
              labelFormatter={(label) => `Tempo: ${formatTime(label)}`}
            />
            <Legend />
            <Bar dataKey="nodes" fill="#4CAF50" name="Execuções de Nós" />
            <Bar dataKey="reasoning" fill="#2196F3" name="Raciocínio (ReAct)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Lista detalhada */}
      <div>
        <h4 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Eventos Detalhados
          <span style={{ fontSize: '0.75rem', color: '#999', fontWeight: 'normal' }} title="Lista cronológica de todos os eventos que ocorreram durante o processamento">ℹ️</span>
        </h4>
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {timelineList.map((event, index) => (
            <div
              key={index}
              style={{
                padding: '0.75rem',
                borderLeft: `4px solid ${
                  event.type === 'node_execution' ? '#4CAF50' : '#2196F3'
                }`,
                backgroundColor: '#f9f9f9',
                marginBottom: '0.5rem',
                borderRadius: '4px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                    {event.label}
                  </div>
                  {event.node && (
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                      Nó: {event.node}
                    </div>
                  )}
                  {event.tool && (
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                      Tool: {event.tool}
                    </div>
                  )}
                  {event.reasoning_type && (
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                      Tipo: {event.reasoning_type}
                    </div>
                  )}
                </div>
                <div style={{ textAlign: 'right', fontSize: '0.85rem', color: '#666' }}>
                  <div>{event.formattedTime}</div>
                  {event.duration_ms && (
                    <div style={{ marginTop: '0.25rem' }}>
                      Duração: {formatTime(event.duration_ms)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

