'use client'

import RunsList from '@/app/components/studio/RunsList'

export default function StudioRunsPage() {
  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Studio - Execuções</h1>
        <p style={{ color: '#666' }}>Visualize e gerencie todas as execuções do agente</p>
      </div>
      <RunsList />
    </div>
  )
}
