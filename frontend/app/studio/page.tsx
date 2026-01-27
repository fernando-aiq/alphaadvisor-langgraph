'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { FiPlay, FiBarChart2, FiLayers, FiList, FiLoader } from 'react-icons/fi'
import Card from '@/app/components/Card'
import { langSmithClient, type GraphStructure } from '@/app/lib/studio/langsmith-client'
import StudioGraphViewer from '@/app/components/studio/StudioGraphViewer'

export default function StudioPage() {
  const [graphStructure, setGraphStructure] = useState<GraphStructure | null>(null)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [graphError, setGraphError] = useState<string | null>(null)

  useEffect(() => {
    const loadGraphStructure = async () => {
      // Obter assistantId da variável de ambiente ou usar fallback
      const assistantId = typeof window !== 'undefined' 
        ? (process.env.NEXT_PUBLIC_ASSISTANT_ID?.trim() || 'agent')
        : 'agent'
      
      try {
        setLoadingGraph(true)
        setGraphError(null)
        const structure = await langSmithClient.getGraphStructure(assistantId)
        setGraphStructure(structure)
      } catch (err: any) {
        console.error('Erro ao carregar estrutura do grafo:', err)
        setGraphError(err.message || 'Erro ao carregar estrutura do grafo')
      } finally {
        setLoadingGraph(false)
      }
    }

    loadGraphStructure()
  }, [])

  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Studio</h1>
        <p style={{ color: '#666' }}>Visualize, analise e gerencie execuções do agente</p>
      </div>

      {/* Cards de navegação */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <Link href="/studio/runs" style={{ textDecoration: 'none', color: 'inherit' }}>
          <Card style={{ padding: '2rem', cursor: 'pointer', transition: 'all 0.2s', height: '100%' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <FiList style={{ fontSize: '2rem', color: '#2196F3' }} />
              <h3 style={{ margin: 0 }}>Execuções</h3>
            </div>
            <p style={{ color: '#666', margin: 0 }}>
              Visualize todas as threads e runs executadas pelo agente
            </p>
          </Card>
        </Link>

        <Card style={{ padding: '2rem', opacity: 0.6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <FiBarChart2 style={{ fontSize: '2rem', color: '#10b981' }} />
            <h3 style={{ margin: 0 }}>Métricas</h3>
          </div>
          <p style={{ color: '#666', margin: 0 }}>
            Dashboard de métricas e analytics (em breve)
          </p>
        </Card>

        <Card style={{ padding: '2rem', opacity: 0.6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <FiLayers style={{ fontSize: '2rem', color: '#f59e0b' }} />
            <h3 style={{ margin: 0 }}>Comparar</h3>
          </div>
          <p style={{ color: '#666', margin: 0 }}>
            Compare execuções lado a lado (em breve)
          </p>
        </Card>
      </div>

      {/* Visualização do Grafo */}
      <Card style={{ padding: '0', marginBottom: '2rem', minHeight: '600px' }}>
        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #e0e0e0' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiLayers />
            Estrutura do Grafo
          </h3>
          <p style={{ margin: '0.5rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>
            Visualização da estrutura do agente
          </p>
        </div>
        {loadingGraph ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <FiLoader className="animate-spin" style={{ fontSize: '2rem', margin: '0 auto' }} />
            <div style={{ marginTop: '1rem' }}>Carregando estrutura do grafo...</div>
          </div>
        ) : graphError ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#F44336' }}>
            <div style={{ marginBottom: '0.5rem' }}>Erro ao carregar grafo</div>
            <div style={{ fontSize: '0.9rem', color: '#666' }}>{graphError}</div>
          </div>
        ) : graphStructure ? (
          <StudioGraphViewer
            graphStructure={graphStructure}
            threadState={undefined}
            runs={[]}
          />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
            Não foi possível carregar a estrutura do grafo.
          </div>
        )}
      </Card>

      {/* Informações */}
      <Card style={{ padding: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>Sobre o Studio</h3>
        <p style={{ color: '#666', lineHeight: '1.6' }}>
          O Studio permite visualizar e analisar todas as execuções do agente em produção.
          Você pode ver o estado completo de cada thread, mensagens trocadas, tool calls executadas
          e o fluxo de execução do agente.
        </p>
        <div style={{ marginTop: '1rem', padding: '1rem', background: '#e3f2fd', borderRadius: '4px' }}>
          <strong>API:</strong> {process.env.NEXT_PUBLIC_API_URL || 'Não configurada'}
        </div>
      </Card>
    </div>
  )
}
