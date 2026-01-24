'use client'

import { useState, useEffect, useCallback } from 'react'
import AgentGraphViewer from '../components/visao-sistema/AgentGraphViewer'
import VisaoSistemaChat from '../components/visao-sistema/VisaoSistemaChat'

interface Structure {
  nodes?: { id: string; label?: string; description?: string; position?: { x: number; y: number }; tools_used?: string[]; is_entry_point?: boolean; is_final?: boolean }[]
  edges?: { id: string; source: string; target: string; type?: string; label?: string; condition?: string }[]
  entry_point?: string
  conditional_edges?: { source: string; function?: string; function_description?: string; conditions?: Record<string, { target: string; description?: string; condition_logic?: string }> }[]
}

interface TraceGraph {
  trace_id?: string
  nodes?: { id: string; label?: string; timestamp?: string; duration_ms?: number; data?: unknown }[]
  edges?: { id: string; source: string; target: string; label?: string; timestamp?: string }[]
  route?: string
  intent?: string
  status?: string
  handoff?: { occurred?: boolean; reason?: string; rule?: string; at_node?: string } | null
}

export default function VisaoSistemaPage() {
  const [structure, setStructure] = useState<Structure | null>(null)
  const [traceGraph, setTraceGraph] = useState<TraceGraph | null>(null)
  const [loadingStructure, setLoadingStructure] = useState(true)
  const [structureError, setStructureError] = useState<string | null>(null)
  const [traceError, setTraceError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoadingStructure(true)
    setStructureError(null)
    fetch('/api/proxy/graph/current')
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? 'Grafo não encontrado' : `Erro ${r.status}`)
        return r.json()
      })
      .then((data) => {
        if (!cancelled) setStructure(data)
      })
      .catch((e) => {
        if (!cancelled) {
          setStructureError(e?.message || 'Falha ao carregar estrutura do grafo.')
          setStructure(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingStructure(false)
      })
    return () => { cancelled = true }
  }, [])

  const onTraceId = useCallback((traceId: string) => {
    setTraceError(null)
    fetch(`/api/trace/${traceId}/graph`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? 'Trace não encontrado' : `Erro ${r.status}`)
        return r.json()
      })
      .then((data) => setTraceGraph(data))
      .catch((e) => {
        setTraceError(e?.message || 'Falha ao carregar trace.')
        setTraceGraph(null)
      })
  }, [])

  return (
    <div className="visao-sistema-page" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1.5rem' }}>
      <header style={{ marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Visão do Sistema
        </h1>
        <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
          Visualize o fluxo do agente e teste pelo chat para ver o caminho da última execução no grafo.
        </p>
      </header>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {/* Grafo ~55% */}
        <div style={{ flex: '0 0 55%', minHeight: 280, display: 'flex', flexDirection: 'column', marginBottom: '1rem' }}>
          {loadingStructure && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Carregando estrutura do grafo...
            </div>
          )}
          {structureError && (
            <div style={{ padding: '1.5rem', background: '#ffebee', borderRadius: 8, color: '#c62828' }}>
              {structureError}
            </div>
          )}
          {!loadingStructure && !structureError && (
            <AgentGraphViewer structure={structure} traceGraph={traceGraph} />
          )}
        </div>

        {/* Chat ~45% */}
        <div
          style={{
            flex: '0 0 45%',
            minHeight: 200,
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-secondary)',
            borderRadius: 12,
            overflow: 'hidden',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          {traceError && (
            <div style={{ padding: '0.5rem 1rem', background: '#fff3e0', fontSize: '0.85rem', color: '#e65100' }}>
              {traceError}
            </div>
          )}
          <VisaoSistemaChat onTraceId={onTraceId} />
        </div>
      </div>
    </div>
  )
}
