'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { getUserIdFromToken } from '../utils/jwt'
import '../globals.css'
import { FiPlus, FiTrash2, FiEdit, FiCheckCircle, FiXCircle, FiLink, FiDollarSign, FiRefreshCw, FiInfo } from 'react-icons/fi'

// Função para obter URL da API
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    return url.trim().replace(/\r\n/g, '').replace(/\n/g, '')
  }
  
  if (process.env.NEXT_PUBLIC_API_URL) {
    const url = process.env.NEXT_PUBLIC_API_URL
    return url.trim().replace(/\r\n/g, '').replace(/\n/g, '')
  }
  
  const isVercel = window.location.hostname.includes('vercel.app') || 
                   window.location.hostname.includes('vercel.com')
  
  if (isVercel) {
    return 'http://localhost:8000'
  }
  
  return 'http://localhost:8000'
}

interface Conexao {
  id: string
  nome: string
  tipo: string
  status: string
  configuracao?: Record<string, any>
  created_at: string
  updated_at: string
}

export default function Conexoes() {
  const [conexoes, setConexoes] = useState<Conexao[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    nome: '',
    tipo: 'open_finance',
    status: 'ativo'
  })

  // Carregar conexões
  useEffect(() => {
    loadConexoes()
  }, [])

  const loadConexoes = async () => {
    setLoading(true)
    try {
      const apiUrl = getApiUrl()
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      
      const response = await axios.get(`${apiUrl}/api/conexoes`, {
        params: { user_id: userId || 'default' },
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 10000
      })

      setConexoes(response.data?.conexoes || [])
    } catch (error: any) {
      console.error('[Conexões] Erro ao carregar conexões:', error)
      setMessage({ type: 'error', text: 'Erro ao carregar conexões. Tente novamente.' })
      setTimeout(() => setMessage(null), 5000)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    
    try {
      const apiUrl = getApiUrl()
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      
      await axios.post(
        `${apiUrl}/api/conexoes`,
        formData,
        {
          params: { user_id: userId || 'default' },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 10000
        }
      )

      setMessage({ type: 'success', text: 'Conexão criada com sucesso!' })
      setShowForm(false)
      setFormData({ nome: '', tipo: 'open_finance', status: 'ativo' })
      loadConexoes()
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      console.error('[Conexões] Erro ao criar conexão:', error)
      setMessage({ type: 'error', text: 'Erro ao criar conexão. Tente novamente.' })
      setTimeout(() => setMessage(null), 5000)
    } finally {
      setSaving(false)
    }
  }

  const handleToggleStatus = async (conexao: Conexao) => {
    try {
      const apiUrl = getApiUrl()
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      
      const novoStatus = conexao.status === 'ativo' ? 'inativo' : 'ativo'
      
      await axios.put(
        `${apiUrl}/api/conexoes/${conexao.id}`,
        { status: novoStatus },
        {
          params: { user_id: userId || 'default' },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 10000
        }
      )

      setMessage({ type: 'success', text: `Conexão ${novoStatus === 'ativo' ? 'ativada' : 'desativada'} com sucesso!` })
      loadConexoes()
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      console.error('[Conexões] Erro ao atualizar conexão:', error)
      setMessage({ type: 'error', text: 'Erro ao atualizar conexão. Tente novamente.' })
      setTimeout(() => setMessage(null), 5000)
    }
  }

  const handleDelete = async (conexaoId: string) => {
    if (!confirm('Tem certeza que deseja remover esta conexão?')) {
      return
    }

    try {
      const apiUrl = getApiUrl()
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      
      await axios.delete(
        `${apiUrl}/api/conexoes/${conexaoId}`,
        {
          params: { user_id: userId || 'default' },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 10000
        }
      )

      setMessage({ type: 'success', text: 'Conexão removida com sucesso!' })
      loadConexoes()
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      console.error('[Conexões] Erro ao remover conexão:', error)
      setMessage({ type: 'error', text: 'Erro ao remover conexão. Tente novamente.' })
      setTimeout(() => setMessage(null), 5000)
    }
  }

  const getTipoLabel = (tipo: string) => {
    const tipos: Record<string, string> = {
      'open_finance': 'Open Finance',
      'api_externa': 'API Externa',
      'banco_dados': 'Banco de Dados',
      'arquivo': 'Arquivo',
      'outro': 'Outro'
    }
    return tipos[tipo] || tipo
  }

  if (loading) {
    return (
      <div className="configuracoes-page">
        <h2>Conexões</h2>
        <p>Carregando conexões...</p>
      </div>
    )
  }

  return (
    <div className="configuracoes-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2>Conexões</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Conecte suas contas e instituições via Open Finance para o AlphaAdvisor acessar seus dados de forma segura.
          </p>
        </div>
        <button 
          className="btn" 
          onClick={() => setShowForm(!showForm)}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <FiPlus />
          {showForm ? 'Cancelar' : 'Conectar via Open Finance'}
        </button>
      </div>

      {message && (
        <div 
          className="card" 
          style={{ 
            marginBottom: '1.5rem',
            backgroundColor: message.type === 'success' ? '#e8f5e9' : '#ffebee',
            border: `1px solid ${message.type === 'success' ? '#4caf50' : '#f44336'}`
          }}
        >
          <p style={{ 
            color: message.type === 'success' ? '#2e7d32' : '#c62828',
            margin: 0 
          }}>
            {message.text}
          </p>
        </div>
      )}

      {/* Seção informativa sobre Open Finance */}
      <section className="config-section">
        <div className="card" style={{ 
          backgroundColor: '#e3f2fd', 
          border: '2px solid #2196F3',
          padding: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'start', gap: '1rem' }}>
            <FiInfo size={24} color="#2196F3" style={{ marginTop: '0.25rem', flexShrink: 0 }} />
            <div>
              <h4 style={{ margin: '0 0 0.5rem 0', color: '#1976D2', fontSize: '1.1rem' }}>
                O que é Open Finance?
              </h4>
              <p style={{ color: '#424242', margin: 0, lineHeight: '1.6', fontSize: '0.95rem' }}>
                Você se conecta via Open Finance. O Open Finance permite que você compartilhe seus dados financeiros de forma segura entre instituições autorizadas. 
                Conecte suas contas bancárias para que o AlphaAdvisor tenha acesso às suas informações financeiras e possa oferecer 
                recomendações mais personalizadas e precisas.
              </p>
            </div>
          </div>
        </div>
      </section>

      {showForm && (
        <section className="config-section">
          <h3>Conectar via Open Finance</h3>
          <div className="card">
            <form onSubmit={handleSubmit}>
              <div className="config-item" style={{ marginBottom: '1rem' }}>
                <label>Nome da Conexão:</label>
                <input
                  type="text"
                  className="input"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  placeholder="Ex: Banco do Brasil"
                  required
                />
              </div>

              <div className="config-item" style={{ marginBottom: '1.5rem' }}>
                <label>Status:</label>
                <select
                  className="input"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="ativo">Ativo</option>
                  <option value="inativo">Inativo</option>
                </select>
              </div>

              <div className="config-actions">
                <button type="submit" className="btn" disabled={saving}>
                  {saving ? 'Salvando...' : 'Conectar via Open Finance'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => {
                    setShowForm(false)
                    setFormData({ nome: '', tipo: 'open_finance', status: 'ativo' })
                  }}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </section>
      )}

      <section className="config-section">
        <h3>Conexões Open Finance ({conexoes.length})</h3>
        {conexoes.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <FiLink size={48} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
            <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Conecte suas contas bancárias via Open Finance para começar.
            </p>
            <button className="btn" onClick={() => setShowForm(true)}>
              Conectar via Open Finance
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {conexoes.map((conexao) => {
              const isOpenFinance = conexao.tipo === 'open_finance'
              const contaInfo = conexao.configuracao || {}
              
              return (
                <div 
                  key={conexao.id} 
                  className="card"
                  style={{
                    border: isOpenFinance ? '2px solid #2196F3' : '1px solid var(--border)',
                    backgroundColor: isOpenFinance ? '#f5f9ff' : 'var(--bg-secondary)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: isOpenFinance ? '1rem' : '0' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                        <h4 style={{ margin: 0, fontSize: '1.1rem', color: isOpenFinance ? '#1976D2' : 'var(--text-primary)' }}>
                          {conexao.nome}
                        </h4>
                        {isOpenFinance && (
                          <span style={{
                            backgroundColor: '#2196F3',
                            color: 'white',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                          }}>
                            Open Finance
                          </span>
                        )}
                        {conexao.status === 'ativo' ? (
                          <FiCheckCircle size={20} color="#10b981" title="Ativo" />
                        ) : (
                          <FiXCircle size={20} color="#ef4444" title="Inativo" />
                        )}
                      </div>
                      {!isOpenFinance && (
                        <>
                          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                            Tipo: {getTipoLabel(conexao.tipo)}
                          </p>
                          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                            Criado em: {new Date(conexao.created_at).toLocaleDateString('pt-BR')}
                          </p>
                        </>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleToggleStatus(conexao)}
                        style={{ 
                          padding: '0.5rem 1rem', 
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                        title={conexao.status === 'ativo' ? 'Desativar' : 'Ativar'}
                      >
                        {conexao.status === 'ativo' ? 'Desativar' : 'Ativar'}
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleDelete(conexao.id)}
                        style={{ 
                          padding: '0.5rem 1rem', 
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                        title="Remover"
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>

                  {/* Detalhes da conta Open Finance */}
                  {isOpenFinance && contaInfo.banco && (
                    <div style={{
                      marginTop: '1rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid #e0e0e0',
                      backgroundColor: 'white',
                      borderRadius: '8px',
                      padding: '1rem'
                    }}>
                      <h5 style={{ margin: '0 0 1rem 0', fontSize: '1rem', color: '#1976D2', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <FiDollarSign />
                        Conta Conectada
                      </h5>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                        <div>
                          <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                            Banco
                          </p>
                          <p style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary)', fontWeight: '500' }}>
                            {contaInfo.banco}
                          </p>
                        </div>
                        <div>
                          <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                            Agência
                          </p>
                          <p style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary)', fontWeight: '500' }}>
                            {contaInfo.agencia}
                          </p>
                        </div>
                        <div>
                          <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                            Conta
                          </p>
                          <p style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary)', fontWeight: '500' }}>
                            {contaInfo.conta}
                          </p>
                        </div>
                        <div>
                          <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                            Tipo
                          </p>
                          <p style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary)', fontWeight: '500' }}>
                            {contaInfo.tipo_conta}
                          </p>
                        </div>
                        {contaInfo.saldo_disponivel !== undefined && (
                          <div>
                            <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                              Saldo Disponível
                            </p>
                            <p style={{ margin: 0, fontSize: '1rem', color: '#10b981', fontWeight: '600' }}>
                              R$ {contaInfo.saldo_disponivel.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                          </div>
                        )}
                        {contaInfo.ultima_sincronizacao && (
                          <div>
                            <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <FiRefreshCw size={14} />
                              Última Sincronização
                            </p>
                            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                              {new Date(contaInfo.ultima_sincronizacao).toLocaleString('pt-BR', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

