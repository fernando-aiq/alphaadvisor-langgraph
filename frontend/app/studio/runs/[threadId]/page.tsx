'use client'

import { useState, useEffect } from 'react'
import RunDetails from '@/app/components/studio/RunDetails'

export default function StudioRunDetailsPage({
  params,
}: {
  params: Promise<{ threadId: string }>
}) {
  // Resolver params se for Promise (Next.js 15+)
  const [threadId, setThreadId] = useState<string>('')
  
  useEffect(() => {
    params.then((resolved) => {
      setThreadId(resolved.threadId)
    })
  }, [params])

  if (!threadId) {
    return <div style={{ padding: '2rem' }}>Carregando...</div>
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <RunDetails threadId={threadId} />
    </div>
  )
}
