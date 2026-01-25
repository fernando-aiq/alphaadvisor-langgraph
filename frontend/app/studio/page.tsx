'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FiPlay, FiBarChart2, FiLayers, FiList } from 'react-icons/fi'
import Card from '@/app/components/Card'

export default function StudioPage() {
  return (
    <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>LangSmith Studio</h1>
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

      {/* Informações */}
      <Card style={{ padding: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>Sobre o Studio</h3>
        <p style={{ color: '#666', lineHeight: '1.6' }}>
          O Studio permite visualizar e analisar todas as execuções do agente LangGraph em produção.
          Você pode ver o estado completo de cada thread, mensagens trocadas, tool calls executadas
          e o fluxo de execução do grafo.
        </p>
        <div style={{ marginTop: '1rem', padding: '1rem', background: '#e3f2fd', borderRadius: '4px' }}>
          <strong>API:</strong> {process.env.NEXT_PUBLIC_API_URL || 'Não configurada'}
        </div>
      </Card>
    </div>
  )
}
