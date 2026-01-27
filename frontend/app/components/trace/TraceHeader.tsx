'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Copy, Check, ExternalLink, ChevronLeft, Menu, X } from 'lucide-react'

interface TraceHeaderProps {
  traceId: string
  traceData?: {
    name?: string
    start_time?: string | null
    end_time?: string | null
    status: string
    langsmith_url?: string
    run_count?: number
  }
  onToggleSidebar?: () => void
  sidebarOpen?: boolean
}

export default function TraceHeader({ 
  traceId, 
  traceData,
  onToggleSidebar,
  sidebarOpen = true
}: TraceHeaderProps) {
  const router = useRouter()
  const [copied, setCopied] = useState(false)

  const copyTraceId = () => {
    navigator.clipboard.writeText(traceId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const calculateDuration = () => {
    if (!traceData?.start_time || !traceData?.end_time) return null
    try {
      const start = new Date(traceData.start_time).getTime()
      const end = new Date(traceData.end_time).getTime()
      const duration = end - start
      
      if (duration < 1000) return `${duration}ms`
      if (duration < 60000) return `${(duration / 1000).toFixed(2)}s`
      return `${(duration / 60000).toFixed(2)}min`
    } catch {
      return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
        return '#10b981'
      case 'error':
      case 'failed':
        return '#ef4444'
      case 'running':
      case 'in_progress':
        return '#3b82f6'
      default:
        return '#6b7280'
    }
  }

  const status = traceData?.status || 'unknown'
  const duration = calculateDuration()

  return (
    <div style={{
      borderBottom: '1px solid #e5e7eb',
      backgroundColor: 'white',
      padding: '1rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '1.5rem',
      flexWrap: 'wrap'
    }}>
      {/* Left side: Back button, Trace ID, Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: '1 1 auto' }}>
        <button
          onClick={() => router.back()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0.75rem',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '0.875rem',
            color: '#374151',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f9fafb'
            e.currentTarget.style.borderColor = '#d1d5db'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'white'
            e.currentTarget.style.borderColor = '#e5e7eb'
          }}
        >
          <ChevronLeft size={16} />
          Voltar
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Trace ID
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <code style={{
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                color: '#111827',
                backgroundColor: '#f3f4f6',
                padding: '0.25rem 0.5rem',
                borderRadius: '4px'
              }}>
                {traceId.substring(0, 8)}...
              </code>
              <button
                onClick={copyTraceId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.25rem',
                  border: 'none',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  color: '#6b7280',
                  transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#111827'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#6b7280'}
                title="Copiar Trace ID"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          <div style={{
            height: '2rem',
            width: '1px',
            backgroundColor: '#e5e7eb'
          }} />

          <div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Status
            </div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '500',
              backgroundColor: `${getStatusColor(status)}20`,
              color: getStatusColor(status)
            }}>
              {status}
            </div>
          </div>
        </div>
      </div>

      {/* Right side: Timestamps, Duration, LangSmith link, Sidebar toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
        {traceData?.start_time && (
          <div style={{ fontSize: '0.875rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Iniciado
            </div>
            <div style={{ color: '#111827', fontWeight: '500' }}>
              {formatDate(traceData.start_time)}
            </div>
          </div>
        )}

        {duration && (
          <div style={{ fontSize: '0.875rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Duração
            </div>
            <div style={{ color: '#111827', fontWeight: '500' }}>
              {duration}
            </div>
          </div>
        )}

        {traceData?.run_count !== undefined && (
          <div style={{ fontSize: '0.875rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
              Runs
            </div>
            <div style={{ color: '#111827', fontWeight: '500' }}>
              {traceData.run_count}
            </div>
          </div>
        )}

        {traceData?.langsmith_url && (
          <a
            href={traceData.langsmith_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              backgroundColor: 'white',
              textDecoration: 'none',
              color: '#374151',
              fontSize: '0.875rem',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb'
              e.currentTarget.style.borderColor = '#3b82f6'
              e.currentTarget.style.color = '#3b82f6'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white'
              e.currentTarget.style.borderColor = '#e5e7eb'
              e.currentTarget.style.color = '#374151'
            }}
          >
            <ExternalLink size={14} />
            LangSmith
          </a>
        )}

        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0.5rem',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              backgroundColor: 'white',
              cursor: 'pointer',
              color: '#374151',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f9fafb'
              e.currentTarget.style.borderColor = '#d1d5db'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white'
              e.currentTarget.style.borderColor = '#e5e7eb'
            }}
            title={sidebarOpen ? 'Ocultar sidebar' : 'Mostrar sidebar'}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        )}
      </div>
    </div>
  )
}
