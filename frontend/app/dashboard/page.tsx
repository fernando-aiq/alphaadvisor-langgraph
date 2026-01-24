'use client'

import { useState, useEffect } from 'react'
import { useProfile } from '../contexts/ProfileContext'
import MetricCard from '../components/MetricCard'
import ProductCard from '../components/ProductCard'
import '../globals.css'
import { FiTrendingUp, FiBell, FiClock, FiDollarSign, FiPieChart, FiTarget, FiAlertCircle } from 'react-icons/fi'
import axios from 'axios'

// Função para obter URL da API no runtime
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    return process.env.API_URL || 'http://localhost:8000'
  }
  
  const isVercel = window.location.hostname.includes('vercel.app') || 
                   window.location.hostname.includes('vercel.com')
  
  if (isVercel) {
    return '' // URL relativa usa o rewrite
  }
  
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

// Dados mockados para assessor
const metrics = {
  ofertas: {
    change: '+12%',
    value: '156 ofertas',
    amount: 'R$ 8.7M em vendas',
    icon: FiTrendingUp,
    color: '#10b981'
  },
  alertas: {
    change: '+8%',
    value: '89 alertas',
    amount: '57.1% taxa de conversão',
    icon: FiBell,
    color: '#f59e0b'
  },
  tempo: {
    change: '+15%',
    value: '22h economizadas',
    amount: '55 clientes a mais atendidos',
    icon: FiClock,
    color: '#3b82f6'
  }
}

const topProducts = [
  {
    name: 'CDB XP',
    amount: 'R$ 2.3M vendas',
    icon: '🏦'
  },
  {
    name: 'Tesouro Selic',
    amount: 'R$ 1.8M vendas',
    icon: '💰'
  },
  {
    name: 'LCI XP',
    amount: 'R$ 1.2M vendas',
    icon: '🏢'
  }
]

interface CarteiraData {
  total: number
  dinheiroParado: number
  aporteMensal: number
  objetivo: {
    valor: number
    prazo: number
    unidade: string
    descricao: string
  }
  distribuicaoPercentual: {
    rendaFixa: number
    rendaVariavel: number
    liquidez: number
  }
  investimentos: Array<{
    id: number
    nome: string
    tipo: string
    valor: number
    rentabilidade: string
    vencimento: string
    classe: string
  }>
  adequacaoPerfil: {
    scoreAdequacao: number
    alertas: Array<{
      tipo: string
      severidade: string
      mensagem: string
    }>
  }
}

interface Vencimento {
  id: number
  nome: string
  valor: number
  dias: number
  tipo: string
  vencimento: string
}

export default function Dashboard() {
  const { profile } = useProfile()
  const [carteira, setCarteira] = useState<CarteiraData | null>(null)
  const [vencimentos, setVencimentos] = useState<Vencimento[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (profile === 'cliente') {
      fetchCarteiraData()
    } else {
      setLoading(false)
    }
  }, [profile])

  const fetchCarteiraData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const apiUrl = getApiUrl()
      
      // Buscar carteira e vencimentos em paralelo
      const [carteiraResponse, vencimentosResponse] = await Promise.all([
        axios.get(`${apiUrl}/api/cliente/carteira`),
        axios.get(`${apiUrl}/api/cliente/vencimentos`)
      ])
      
      setCarteira(carteiraResponse.data)
      setVencimentos(vencimentosResponse.data.vencimentos || [])
    } catch (err: any) {
      console.error('Erro ao buscar dados da carteira:', err)
      setError('Erro ao carregar dados da carteira. Por favor, tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // Dashboard para Cliente - apenas carteira
  if (profile === 'cliente') {
    if (loading) {
      return (
        <div className="dashboard">
          <div className="dashboard-header">
            <h2>Minha Carteira</h2>
          </div>
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <p>Carregando informações da carteira...</p>
          </div>
        </div>
      )
    }

    if (error) {
      return (
        <div className="dashboard">
          <div className="dashboard-header">
            <h2>Minha Carteira</h2>
          </div>
          <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p style={{ color: 'var(--error)', marginBottom: '1rem' }}>{error}</p>
            <button className="btn btn-primary" onClick={fetchCarteiraData}>
              Tentar Novamente
            </button>
          </div>
        </div>
      )
    }

    if (!carteira) {
      return (
        <div className="dashboard">
          <div className="dashboard-header">
            <h2>Minha Carteira</h2>
          </div>
          <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p style={{ color: 'var(--text-muted)' }}>Nenhum dado disponível</p>
          </div>
        </div>
      )
    }

    const totalGeral = carteira.total + carteira.dinheiroParado

    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h2>Minha Carteira</h2>
        </div>

        {/* Cards de Resumo */}
        <div className="metrics-grid">
          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <FiDollarSign size={24} color="#10b981" />
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Total da Carteira</h3>
            </div>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--text-primary)' }}>
              R$ {totalGeral.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
              Investido + Dinheiro Parado
            </p>
          </div>

          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <FiTrendingUp size={24} color="#3b82f6" />
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Patrimônio Investido</h3>
            </div>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--text-primary)' }}>
              R$ {carteira.total.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
              Aplicado em investimentos
            </p>
          </div>

          <div className="card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <FiClock size={24} color="#f59e0b" />
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Dinheiro Parado</h3>
            </div>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--text-primary)' }}>
              R$ {carteira.dinheiroParado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
              Disponível para investir
            </p>
          </div>
        </div>

        <div className="dashboard-grid">
          {/* Distribuição */}
          <div className="dashboard-section">
            <h3>Distribuição do Patrimônio</h3>
            <div className="card">
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span>Renda Fixa</span>
                  <strong>{carteira.distribuicaoPercentual.rendaFixa.toFixed(1)}%</strong>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${carteira.distribuicaoPercentual.rendaFixa}%`, height: '100%', backgroundColor: '#10b981' }} />
                </div>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span>Renda Variável</span>
                  <strong>{carteira.distribuicaoPercentual.rendaVariavel.toFixed(1)}%</strong>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${carteira.distribuicaoPercentual.rendaVariavel}%`, height: '100%', backgroundColor: '#3b82f6' }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span>Liquidez</span>
                  <strong>{carteira.distribuicaoPercentual.liquidez.toFixed(1)}%</strong>
                </div>
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${carteira.distribuicaoPercentual.liquidez}%`, height: '100%', backgroundColor: '#f59e0b' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Objetivo Financeiro */}
          {carteira.objetivo && (
            <div className="dashboard-section">
              <h3>Objetivo Financeiro</h3>
              <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                  <FiTarget size={24} color="#8b5cf6" />
                  <div>
                    <strong style={{ fontSize: '1.2rem' }}>{carteira.objetivo.descricao}</strong>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.25rem 0 0 0' }}>
                      Prazo: {carteira.objetivo.prazo} {carteira.objetivo.unidade}
                    </p>
                  </div>
                </div>
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span>Valor Atual</span>
                    <strong>R$ {totalGeral.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span>Meta</span>
                    <strong>R$ {carteira.objetivo.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                  </div>
                  <div style={{ width: '100%', height: '12px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', overflow: 'hidden', marginTop: '0.5rem' }}>
                    <div 
                      style={{ 
                        width: `${Math.min(100, (totalGeral / carteira.objetivo.valor) * 100)}%`, 
                        height: '100%', 
                        backgroundColor: '#8b5cf6' 
                      }} 
                    />
                  </div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem', textAlign: 'center' }}>
                    {((totalGeral / carteira.objetivo.valor) * 100).toFixed(1)}% do objetivo alcançado
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Investimentos */}
          <div className="dashboard-section">
            <h3>Meus Investimentos</h3>
            <div className="card">
              {carteira.investimentos && carteira.investimentos.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {carteira.investimentos.map((inv) => (
                    <div key={inv.id} style={{ padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '1rem' }}>{inv.nome}</h4>
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.25rem 0 0 0' }}>
                            {inv.tipo} • {inv.rentabilidade}
                          </p>
                        </div>
                        <strong style={{ fontSize: '1.1rem' }}>
                          R$ {inv.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </strong>
                      </div>
                      {inv.vencimento && (
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
                          Vencimento: {new Date(inv.vencimento).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                  Nenhum investimento cadastrado
                </p>
              )}
            </div>
          </div>

          {/* Vencimentos Próximos */}
          <div className="dashboard-section">
            <h3>Vencimentos Próximos</h3>
            <div className="card">
              {vencimentos.length > 0 ? (
                <div className="vencimentos-list">
                  {vencimentos.map((venc) => (
                    <div key={venc.id} className="vencimento-item">
                      <div className="vencimento-info">
                        <h4>{venc.nome}</h4>
                        <p>R$ {venc.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                      </div>
                      <div className="vencimento-days">
                        <span className="days-badge">{venc.dias} dias</span>
                        <span className="type-badge">{venc.tipo}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
                  Nenhum vencimento próximo
                </p>
              )}
            </div>
          </div>

          {/* Alertas */}
          {carteira.adequacaoPerfil && carteira.adequacaoPerfil.alertas && carteira.adequacaoPerfil.alertas.length > 0 && (
            <div className="dashboard-section">
              <h3>Alertas de Adequação</h3>
              <div className="card">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {carteira.adequacaoPerfil.alertas.map((alerta, idx) => (
                    <div key={idx} style={{ 
                      padding: '1rem', 
                      backgroundColor: alerta.severidade === 'alta' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                      borderRadius: '8px',
                      borderLeft: `4px solid ${alerta.severidade === 'alta' ? '#ef4444' : '#f59e0b'}`
                    }}>
                      <div style={{ display: 'flex', alignItems: 'start', gap: '0.5rem' }}>
                        <FiAlertCircle size={20} color={alerta.severidade === 'alta' ? '#ef4444' : '#f59e0b'} />
                        <p style={{ margin: 0, fontSize: '0.9rem' }}>{alerta.mensagem}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0, textAlign: 'center' }}>
                    Score de Adequação: <strong>{carteira.adequacaoPerfil.scoreAdequacao}/100</strong>
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Dashboard para Assessor - manter tudo como está
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Performance e Avaliação</h2>
        <div className="period-selector">
          <select className="input" style={{ width: 'auto', padding: '0.5rem 1rem' }}>
            <option>Hoje</option>
            <option>7 dias</option>
            <option>30 dias</option>
            <option>90 dias</option>
            <option>Ano</option>
            <option>Personalizado</option>
          </select>
        </div>
      </div>

      <div className="metrics-grid">
        <MetricCard {...metrics.ofertas} />
        <MetricCard {...metrics.alertas} />
        <MetricCard {...metrics.tempo} />
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h3>Top Produtos</h3>
          <div className="products-list">
            {topProducts.map((product, idx) => (
              <ProductCard key={idx} {...product} />
            ))}
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Você vs Equipe</h3>
          <div className="card">
            <div className="comparison-item">
              <span>Conversão</span>
              <div className="comparison-bar">
                <div className="comparison-bar-fill" style={{ width: '85%' }}>
                  <span>Você 85%</span>
                </div>
                <div className="comparison-bar-fill team" style={{ width: '65%' }}>
                  <span>Equipe 65%</span>
                </div>
              </div>
              <span className="comparison-badge">+33% acima da média</span>
            </div>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Vencimentos Próximos</h3>
          <div className="card">
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              Você tem vencimentos próximos!
            </p>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Seletor de Clientes</h3>
          <div className="card">
            <div className="client-selector">
              <div className="client-info">
                <span className="client-icon">👤</span>
                <div>
                  <strong>João Silva</strong>
                  <p>***.***.***-12</p>
                </div>
              </div>
              <span className="status-badge active">Ativo</span>
            </div>
            <div className="quick-actions">
              <button className="btn btn-secondary" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
                Saldo Cliente
              </button>
              <button className="btn btn-secondary" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
                Carteira Cliente
              </button>
              <button className="btn btn-secondary" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
                Evolução
              </button>
              <button className="btn btn-secondary" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
                Dossiê
              </button>
            </div>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Contas Conectadas</h3>
          <div className="card">
            <div className="account-item">
              <span className="account-icon">📈</span>
              <div>
                <strong>XP Investimentos</strong>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Conectada</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
