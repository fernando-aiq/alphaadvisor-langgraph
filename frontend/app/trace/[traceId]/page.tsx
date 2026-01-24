'use client'

import { useParams, useRouter } from 'next/navigation'
import TraceViewerContainer from '../../components/trace/TraceViewerContainer'
import Card from '../../components/Card'

export default function TracePage() {
  const params = useParams()
  const router = useRouter()
  const traceId = params.traceId as string

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button
          onClick={() => router.back()}
          style={{
            padding: '0.5rem 1rem',
            border: '1px solid #e0e0e0',
            borderRadius: '4px',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}
        >
          ← Voltar
        </button>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Visualização de Trace</h1>
      </div>

      {traceId ? (
        <TraceViewerContainer traceId={traceId} />
      ) : (
        <Card style={{ padding: '2rem', textAlign: 'center' }}>
          <div style={{ color: '#F44336' }}>Trace ID não fornecido</div>
        </Card>
      )}
    </div>
  )
}

