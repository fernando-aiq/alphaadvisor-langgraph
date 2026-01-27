'use client'

import { useState, useEffect } from 'react'
import { langSmithClient } from '@/app/lib/studio/langsmith-client'
import Card from '@/app/components/Card'
import { FiSearch, FiRefreshCw, FiPlus, FiArrowRight } from 'react-icons/fi'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function RunsList() {
  const router = useRouter()
  const [threadIdInput, setThreadIdInput] = useState('')
  const [recentThreads, setRecentThreads] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Carregar threads recentes do localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('studio:recent_threads')
      if (stored) {
        try {
          setRecentThreads(JSON.parse(stored))
        } catch {
          // Ignorar erro de parse
        }
      }
    }
  }, [])

  const saveThreadId = (threadId: string) => {
    if (typeof window !== 'undefined') {
      const updated = [threadId, ...recentThreads.filter(t => t !== threadId)].slice(0, 20)
      setRecentThreads(updated)
      localStorage.setItem('studio:recent_threads', JSON.stringify(updated))
    }
  }

  const handleViewThread = async () => {
    if (!threadIdInput.trim()) {
      setError('Por favor, insira um Thread ID')
      return
    }

    const threadId = threadIdInput.trim()
    setLoading(true)
    setError(null)

    try {
      // Verificar se a thread existe tentando obter o estado
      await langSmithClient.getThreadState(threadId)
      saveThreadId(threadId)
      router.push(`/studio/runs/${threadId}`)
    } catch (err: any) {
      console.error('Erro ao verificar thread:', err)
      setError(err.message || 'Thread não encontrada ou erro ao acessar')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateThread = async () => {
    setLoading(true)
    setError(null)

    try {
      const thread = await langSmithClient.createThread({
        messages: [{ role: 'user', content: 'Olá' }],
      })
      saveThreadId(thread.thread_id)
      router.push(`/studio/runs/${thread.thread_id}`)
    } catch (err: any) {
      console.error('Erro ao criar thread:', err)
      setError(err.message || 'Erro ao criar thread')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Buscar/Criar Thread */}
      <Card style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Visualizar ou Criar Thread</h3>
        
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '300px' }}>
            <input
              type="text"
              placeholder="Cole ou digite o Thread ID aqui..."
              value={threadIdInput}
              onChange={(e) => setThreadIdInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleViewThread()
                }
              }}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '0.9rem',
                fontFamily: 'monospace',
              }}
            />
          </div>
          <button
            onClick={handleViewThread}
            disabled={loading || !threadIdInput.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || !threadIdInput.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !threadIdInput.trim() ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <FiSearch />
            Visualizar
          </button>
          <button
            onClick={handleCreateThread}
            disabled={loading}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <FiPlus />
            Nova Thread
          </button>
        </div>

        {error && (
          <div style={{ padding: '0.75rem', background: '#ffebee', borderRadius: '4px', color: '#F44336', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}
      </Card>

      {/* Threads Recentes */}
      {recentThreads.length > 0 && (
        <Card style={{ padding: '1.5rem' }}>
          <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Threads Recentes ({recentThreads.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {recentThreads.map((threadId) => (
              <Link
                key={threadId}
                href={`/studio/runs/${threadId}`}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  color: 'inherit',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f5f5f5'
                  e.currentTarget.style.borderColor = '#2196F3'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'white'
                  e.currentTarget.style.borderColor = '#e0e0e0'
                }}
              >
                <span style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>{threadId}</span>
                <FiArrowRight style={{ color: '#999' }} />
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Informação */}
      {recentThreads.length === 0 && (
        <Card style={{ padding: '1.5rem' }}>
          <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
            <p style={{ marginBottom: '1rem' }}>
              <strong>Como usar:</strong>
            </p>
            <ol style={{ textAlign: 'left', display: 'inline-block', lineHeight: '1.8' }}>
              <li>Cole um Thread ID no campo acima e clique em "Visualizar"</li>
              <li>Ou clique em "Nova Thread" para criar uma nova execução</li>
              <li>Threads visualizadas serão salvas aqui para acesso rápido</li>
            </ol>
            <p style={{ marginTop: '1.5rem', fontSize: '0.9rem' }}>
              <strong>Nota:</strong> A API não permite listar todas as threads.
              Você precisa ter o Thread ID para visualizar uma execução específica.
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}
