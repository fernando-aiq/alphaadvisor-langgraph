'use client'

import { useState } from 'react'
import '../globals.css'
import { FiMessageCircle, FiCode, FiKey, FiCopy, FiCheck } from 'react-icons/fi'

export default function DeployPage() {
  const [copied, setCopied] = useState<string | null>(null)

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const deployOptions = [
    {
      id: 'whatsapp',
      title: 'WhatsApp',
      icon: FiMessageCircle,
      description: 'Conecte seu agente ao WhatsApp para interagir com seus clientes através de mensagens. Configure um número e comece a receber mensagens automaticamente.',
      color: '#25D366',
      action: {
        label: 'Conectar WhatsApp',
        onClick: () => {
          // TODO: Implementar integração com WhatsApp
          alert('Funcionalidade de conexão com WhatsApp em desenvolvimento')
        }
      },
      features: [
        'Respostas automáticas',
        'Suporte a mídia',
        'Integração com número próprio'
      ]
    },
    {
      id: 'web-embed',
      title: 'Web Embed',
      icon: FiCode,
      description: 'Integre o agente diretamente no seu site com um simples código. Basta copiar o script e colar no seu HTML para ter o chat disponível.',
      color: '#667eea',
      action: {
        label: 'Gerar Script',
        onClick: () => {
          // TODO: Implementar geração de script
          const script = `<script src="https://api.alphaadvisor.com/embed.js" data-agent-id="YOUR_AGENT_ID"></script>`
          handleCopy(script, 'web-embed')
        }
      },
      features: [
        'Fácil integração',
        'Customizável',
        'Responsivo'
      ]
    },
    {
      id: 'api-sdk',
      title: 'API / SDK',
      icon: FiKey,
      description: 'Use nossa API REST ou SDK para integrar o agente em suas aplicações. Acesso completo com autenticação via token.',
      color: '#764ba2',
      action: {
        label: 'Ver Credenciais',
        onClick: () => {
          // TODO: Implementar exibição de credenciais
          const apiKey = 'sk_live_xxxxxxxxxxxxxxxxxxxxx'
          const endpoint = 'https://api.alphaadvisor.com/v1/chat'
          handleCopy(apiKey, 'api-key')
        }
      },
      features: [
        'REST API completa',
        'SDK disponível',
        'Documentação detalhada'
      ]
    }
  ]

  return (
    <div className="deploy-page">
      <div className="deploy-header">
        <h2>Deploy do Agente</h2>
        <p className="deploy-subtitle">
          Escolha como deseja disponibilizar seu agente para seus clientes
        </p>
      </div>

      <div className="deploy-grid">
        {deployOptions.map((option) => {
          const Icon = option.icon
          return (
            <div key={option.id} className="deploy-card">
              <div className="deploy-card-header">
                <div 
                  className="deploy-icon-wrapper"
                  style={{ backgroundColor: `${option.color}20` }}
                >
                  <Icon size={32} color={option.color} />
                </div>
                <h3>{option.title}</h3>
              </div>
              
              <p className="deploy-description">{option.description}</p>
              
              <div className="deploy-features">
                {option.features.map((feature, idx) => (
                  <div key={idx} className="deploy-feature">
                    <span className="deploy-feature-check">✓</span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              
              <button
                className="btn deploy-action-btn"
                style={{ backgroundColor: option.color }}
                onClick={option.action.onClick}
              >
                {option.action.label}
              </button>
            </div>
          )
        })}
      </div>

      {copied && (
        <div className="deploy-copy-notification">
          <FiCheck size={16} />
          <span>Copiado para a área de transferência!</span>
        </div>
      )}
    </div>
  )
}

