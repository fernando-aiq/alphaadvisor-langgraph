'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import Toggle from '../components/Toggle'
import { getUserIdFromToken } from '../utils/jwt'
import '../globals.css'

// Configurações padrão de autonomia
const AUTONOMIA_PADRAO = {
  nivel: 'assistido',
  acoes: {
    executar_ordens: false,
    simular: true,
    enviar_mensagens_externas: false,
    criar_alertas: true,
    modificar_carteira: false
  },
  respostas: {
    falar_sobre_precos: true,
    falar_sobre_risco: true,
    recomendar_produtos: true,
    fornecer_projecoes: true,
    comparar_produtos: true
  },
  regras_redirecionamento: [
    'Solicitação de valores acima de R$ 100.000',
    'Reclamações ou insatisfação',
    'Solicitação de cancelamento de conta',
    'Questões legais ou regulatórias'
  ]
}

export default function Autonomia() {
  const [config, setConfig] = useState(AUTONOMIA_PADRAO)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Carregar configurações do backend
  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      // Sempre mesma origem (proxy para Flask) — evita 403 do LangGraph
      const baseURL = typeof window !== 'undefined' ? window.location.origin : ''
      const response = await axios.get(`${baseURL}/api/configuracoes`, {
        params: { user_id: userId || 'default' },
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 10000
      })

      if (response.data?.autonomia) {
        setConfig(response.data.autonomia)
      }
    } catch (error: any) {
      console.error('[Autonomia] Erro ao carregar configurações:', error)
      // Usar padrão em caso de erro
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const userId = getUserIdFromToken()
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
      const baseURL = typeof window !== 'undefined' ? window.location.origin : ''
      await axios.post(
        `${baseURL}/api/configuracoes`,
        { autonomia: config },
        {
          params: { user_id: userId || 'default' },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 10000
        }
      )

      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      console.error('[Autonomia] Erro ao salvar configurações:', error)
      setMessage({ type: 'error', text: 'Erro ao salvar configurações. Tente novamente.' })
      setTimeout(() => setMessage(null), 5000)
    } finally {
      setSaving(false)
    }
  }

  const resetConfig = async () => {
    if (!confirm('Tem certeza que deseja resetar as configurações para os valores padrão?')) {
      return
    }

    setConfig(AUTONOMIA_PADRAO)
    setMessage({ type: 'success', text: 'Configurações resetadas para padrão. Clique em Salvar para aplicar.' })
    setTimeout(() => setMessage(null), 3000)
  }

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  const updateAcoes = (key: string, value: boolean) => {
    setConfig(prev => ({
      ...prev,
      acoes: { ...prev.acoes, [key]: value }
    }))
  }

  const updateRespostas = (key: string, value: boolean) => {
    setConfig(prev => ({
      ...prev,
      respostas: { ...prev.respostas, [key]: value }
    }))
  }

  const updateRegraRedirecionamento = (index: number, value: string) => {
    setConfig(prev => ({
      ...prev,
      regras_redirecionamento: prev.regras_redirecionamento.map((regra, i) => 
        i === index ? value : regra
      )
    }))
  }

  const adicionarRegraRedirecionamento = () => {
    setConfig(prev => ({
      ...prev,
      regras_redirecionamento: [...prev.regras_redirecionamento, '']
    }))
  }

  const removerRegraRedirecionamento = (index: number) => {
    setConfig(prev => ({
      ...prev,
      regras_redirecionamento: prev.regras_redirecionamento.filter((_, i) => i !== index)
    }))
  }

  if (loading) {
    return (
      <div className="configuracoes-page">
        <h2>Autonomia</h2>
        <p>Carregando configurações...</p>
      </div>
    )
  }

  return (
    <div className="configuracoes-page">
      <h2>Autonomia</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Configure o nível de autonomia do agente e defina quais ações e respostas ele pode executar.
      </p>

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

      <section className="config-section">
        <h3>Nível de Autonomia</h3>
        <div className="card">
          <div className="config-item">
            <label>Nível de Autonomia:</label>
            <select
              className="input"
              value={config.nivel}
              onChange={(e) => updateConfig('nivel', e.target.value)}
            >
              <option value="somente_leitura">Somente Leitura</option>
              <option value="assistido">Assistido (Recomendado)</option>
              <option value="autonomo">Autônomo</option>
            </select>
            <p style={{ 
              fontSize: '0.875rem', 
              color: 'var(--text-secondary)', 
              marginTop: '0.5rem' 
            }}>
              {config.nivel === 'somente_leitura' && 
                'O agente apenas responde e recomenda, sem executar ações.'}
              {config.nivel === 'assistido' && 
                'O agente pede confirmação antes de executar ações importantes.'}
              {config.nivel === 'autonomo' && 
                'O agente executa ações automaticamente sem confirmação prévia.'}
            </p>
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Ações Permitidas</h3>
        <div className="card">
          <p style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            marginBottom: '1rem' 
          }}>
            Defina quais ações o agente pode executar:
          </p>
          
          <div className="config-item">
            <Toggle
              checked={config.acoes.executar_ordens}
              onChange={(checked) => updateAcoes('executar_ordens', checked)}
              label="Executar ordens de compra/venda"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.acoes.simular}
              onChange={(checked) => updateAcoes('simular', checked)}
              label="Simular investimentos"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.acoes.enviar_mensagens_externas}
              onChange={(checked) => updateAcoes('enviar_mensagens_externas', checked)}
              label="Enviar mensagens externas (email, SMS)"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.acoes.criar_alertas}
              onChange={(checked) => updateAcoes('criar_alertas', checked)}
              label="Criar alertas automáticos"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.acoes.modificar_carteira}
              onChange={(checked) => updateAcoes('modificar_carteira', checked)}
              label="Modificar composição da carteira"
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Respostas Permitidas</h3>
        <div className="card">
          <p style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            marginBottom: '1rem' 
          }}>
            Defina sobre quais tópicos o agente pode falar:
          </p>
          
          <div className="config-item">
            <Toggle
              checked={config.respostas.falar_sobre_precos}
              onChange={(checked) => updateRespostas('falar_sobre_precos', checked)}
              label="Falar sobre preços e cotações"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.respostas.falar_sobre_risco}
              onChange={(checked) => updateRespostas('falar_sobre_risco', checked)}
              label="Falar sobre riscos de investimentos"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.respostas.recomendar_produtos}
              onChange={(checked) => updateRespostas('recomendar_produtos', checked)}
              label="Recomendar produtos de investimento"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.respostas.fornecer_projecoes}
              onChange={(checked) => updateRespostas('fornecer_projecoes', checked)}
              label="Fornecer projeções financeiras"
            />
          </div>

          <div className="config-item">
            <Toggle
              checked={config.respostas.comparar_produtos}
              onChange={(checked) => updateRespostas('comparar_produtos', checked)}
              label="Comparar produtos e ativos"
            />
          </div>
        </div>
      </section>

      <section className="config-section">
        <h3>Regras de Redirecionamento</h3>
        <div className="card">
          <p style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            marginBottom: '1rem' 
          }}>
            Defina condições em que o agente deve redirecionar para um humano:
          </p>
          
          {config.regras_redirecionamento.map((regra, index) => (
            <div key={index} className="config-item" style={{ 
              display: 'flex', 
              gap: '0.5rem', 
              alignItems: 'center',
              marginBottom: '0.75rem'
            }}>
              <input
                type="text"
                className="input"
                value={regra}
                onChange={(e) => updateRegraRedirecionamento(index, e.target.value)}
                placeholder="Ex: Solicitação de valores acima de R$ 100.000"
                style={{ flex: 1 }}
              />
              <button
                className="btn btn-secondary"
                onClick={() => removerRegraRedirecionamento(index)}
                style={{ padding: '0.5rem 1rem' }}
              >
                Remover
              </button>
            </div>
          ))}
          
          <button
            className="btn btn-secondary"
            onClick={adicionarRegraRedirecionamento}
            style={{ marginTop: '0.5rem' }}
          >
            + Adicionar Regra
          </button>
        </div>
      </section>

      <section className="config-section">
        <div className="card">
          <div className="config-actions">
            <button 
              className="btn" 
              onClick={saveConfig}
              disabled={saving}
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={resetConfig}
            >
              Resetar
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

