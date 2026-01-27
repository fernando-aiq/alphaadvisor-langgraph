'use client'

import { useState, useEffect } from 'react'
import RunDetails from '@/app/components/studio/RunDetails'

export default function StudioRunDetailsPage({
  params,
}: {
  params: Promise<{ threadId: string }> | { threadId: string }
}) {
  // Resolver params se for Promise (Next.js 15+) ou acessar diretamente
  const [threadId, setThreadId] = useState<string>('')
  
  useEffect(() => {
    const resolveParams = async () => {
      if (params instanceof Promise) {
        // Se for Promise, aguardar resolução
        const resolved = await params
        setThreadId(resolved.threadId)
      } else {
        // Se já for objeto, acessar diretamente
        setThreadId(params.threadId)
      }
    }
    
    resolveParams()
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
