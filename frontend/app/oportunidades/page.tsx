'use client'

import ProductCard from '../components/ProductCard'
import '../globals.css'

const oportunidadesDestaque = [
  {
    name: 'CDB XP 110% CDI',
    rentabilidade: '110% CDI',
    liquidez: 'Diária',
    valorMinimo: 'R$ 1.000',
    prazo: '2 anos',
    icon: '💰',
    highlight: true
  },
  {
    name: 'Tesouro Selic 2029',
    rentabilidade: 'SELIC + 0,1%',
    liquidez: 'Governo Federal',
    valorMinimo: 'R$ 100',
    prazo: '01/01/2029',
    icon: '🏛️',
    highlight: false
  },
  {
    name: 'LCI XP 95% CDI',
    rentabilidade: '95% CDI',
    liquidez: 'Isenção: IR e IOF',
    valorMinimo: 'R$ 5.000',
    prazo: '3 anos',
    icon: '🏦',
    highlight: false
  },
  {
    name: 'Fundo XP Dividendos',
    rentabilidade: 'IPCA + 4,5%',
    liquidez: 'Multimercado',
    valorMinimo: 'R$ 500',
    prazo: 'D+1',
    icon: '📈',
    highlight: false
  }
]

const recomendacoes = [
  {
    title: 'Diversificação Inteligente',
    description: 'Com base no seu perfil conservador, recomendamos alocar 60% em renda fixa e 40% em fundos multimercado.',
    action: 'Ver Detalhes'
  },
  {
    title: 'Plano de Aposentadoria',
    description: 'Considere investir em Tesouro IPCA+ para proteger seu poder de compra a longo prazo.',
    action: 'Ver Detalhes'
  }
]

export default function Oportunidades() {
  return (
    <div className="oportunidades-page">
      <h2>Oportunidades de Investimento</h2>

      <section className="oportunidades-section">
        <h3>Oportunidades Personalizadas</h3>
        <div className="oportunidades-grid">
          {oportunidadesDestaque.map((op, idx) => (
            <div key={idx} className={`oportunidade-card ${op.highlight ? 'highlight' : ''}`}>
              {op.highlight && <span className="destaque-badge">DESTAQUE</span>}
              <div className="oportunidade-header">
                <span className="oportunidade-icon">{op.icon}</span>
                <h4>{op.name}</h4>
              </div>
              <div className="oportunidade-details">
                <div className="detail-item">
                  <span className="detail-label">Rentabilidade:</span>
                  <span className="detail-value">{op.rentabilidade}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Liquidez:</span>
                  <span className="detail-value">{op.liquidez}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Valor Mínimo:</span>
                  <span className="detail-value">{op.valorMinimo}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Prazo:</span>
                  <span className="detail-value">{op.prazo}</span>
                </div>
              </div>
              <div className="oportunidade-actions">
                <button className="btn">Investir</button>
                <button className="btn btn-secondary">Simular</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="recomendacoes-section">
        <h3>Recomendações para Você</h3>
        <div className="recomendacoes-grid">
          {recomendacoes.map((rec, idx) => (
            <div key={idx} className="card recomendacao-card">
              <h4>{rec.title}</h4>
              <p>{rec.description}</p>
              <button className="btn" style={{ marginTop: '1rem' }}>
                {rec.action}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}




