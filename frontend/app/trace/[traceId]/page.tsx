'use client'

import { useParams } from 'next/navigation'
import TraceViewerContainer from '../../components/trace/TraceViewerContainer'
import Card from '../../components/Card'

export default function TracePage() {
  const params = useParams()
  const traceId = params.traceId as string

  return (
    <div style={{ 
      width: '100%', 
      height: '100vh',
      overflow: 'hidden',
      backgroundColor: '#f9fafb'
    }}>
      {traceId ? (
        <TraceViewerContainer traceId={traceId} />
      ) : (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%' 
        }}>
          <Card style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ color: '#ef4444', fontSize: '1rem' }}>Trace ID não fornecido</div>
          </Card>
        </div>
      )}
    </div>
  )
}
