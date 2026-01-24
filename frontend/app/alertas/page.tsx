'use client'

import AlertCard from '../components/AlertCard'
import '../globals.css'

const alertasUrgentes: Array<{
  type: 'vencimento' | 'queda' | 'oportunidade' | 'recomendacao' | 'mercado'
  title: string
  time: string
  message: string
  actions: string[]
}> = [
  {
    type: 'vencimento',
    title: 'Vencimento de CDB em 3 dias',
    time: 'Há 2 horas',
    message: 'Seu CDB XP 110% CDI vence em 3 dias. Considere renovar ou resgatar para não perder a liquidez.',
    actions: ['Renovar', 'Resgatar']
  },
  {
    type: 'queda',
    title: 'Queda significativa na carteira',
    time: 'Há 4 horas',
    message: 'Sua carteira teve uma queda de -2,3% hoje. Considere rebalancear seus investimentos.',
    actions: ['Rebalancear', 'Ver Análise']
  }
]

const oportunidadesDisponiveis: Array<{
  type: 'vencimento' | 'queda' | 'oportunidade' | 'recomendacao' | 'mercado'
  title: string
  time: string
  message: string
  actions: string[]
}> = [
  {
    type: 'oportunidade',
    title: 'Novo CDB com taxa especial',
    time: 'Hoje',
    message: 'CDB XP 115% CDI disponível apenas hoje com taxa promocional. Aproveite!',
    actions: ['Investir Agora', 'Simular']
  },
  {
    type: 'oportunidade',
    title: 'Tesouro Selic com taxa atrativa',
    time: 'Ontem',
    message: 'Tesouro Selic 2029 está oferecendo SELIC + 0,15% acima da média do mercado.',
    actions: ['Investir', 'Comparar']
  }
]

const recomendacoes: Array<{
  type: 'vencimento' | 'queda' | 'oportunidade' | 'recomendacao' | 'mercado'
  title: string
  time: string
  message: string
  actions: string[]
}> = [
  {
    type: 'recomendacao',
    title: 'Diversificação da carteira',
    time: 'Esta semana',
    message: 'Sua carteira está muito concentrada em renda fixa. Considere diversificar com fundos multimercado.',
    actions: ['Ver Sugestões', 'Ignorar']
  },
  {
    type: 'recomendacao',
    title: 'Plano de aposentadoria',
    time: 'Esta semana',
    message: 'Você está no caminho certo! Considere aumentar seus aportes em Tesouro IPCA+ para aposentadoria.',
    actions: ['Aumentar Aporte', 'Simular']
  }
]

const alertasMercado: Array<{
  type: 'vencimento' | 'queda' | 'oportunidade' | 'recomendacao' | 'mercado'
  title: string
  time: string
  message: string
  actions: string[]
}> = [
  {
    type: 'mercado',
    title: 'Selic pode subir na próxima reunião',
    time: 'Há 1 dia',
    message: 'Analistas preveem alta de 0,25% na Selic. CDBs e Tesouro Selic podem ficar mais atrativos.',
    actions: ['Ver Impacto', 'Aguardar']
  },
  {
    type: 'mercado',
    title: 'Dólar em alta - oportunidades',
    time: 'Há 2 dias',
    message: 'Dólar subiu 2% esta semana. Considere fundos cambiais para proteger seu patrimônio.',
    actions: ['Ver Fundos', 'Analisar']
  }
]

export default function Alertas() {
  return (
    <div className="alertas-page">
      <div className="alertas-header">
        <h2>Alertas Inteligentes</h2>
        <div className="alertas-filters">
          <button className="btn btn-secondary" style={{ fontSize: '0.9rem' }}>
            Todos
          </button>
          <button className="btn" style={{ fontSize: '0.9rem', background: 'transparent', color: 'var(--text-secondary)' }}>
            Urgentes
          </button>
          <button className="btn" style={{ fontSize: '0.9rem', background: 'transparent', color: 'var(--text-secondary)' }}>
            Oportunidades
          </button>
          <button className="btn" style={{ fontSize: '0.9rem', background: 'transparent', color: 'var(--text-secondary)' }}>
            Mercado
          </button>
        </div>
      </div>

      <section className="alertas-section">
        <h3>Alertas Urgentes</h3>
        <div className="alertas-list">
          {alertasUrgentes.map((alerta, idx) => (
            <AlertCard key={idx} {...alerta} />
          ))}
        </div>
      </section>

      <section className="alertas-section">
        <h3>Oportunidades Disponíveis</h3>
        <div className="alertas-list">
          {oportunidadesDisponiveis.map((alerta, idx) => (
            <AlertCard key={idx} {...alerta} />
          ))}
        </div>
      </section>

      <section className="alertas-section">
        <h3>Recomendações</h3>
        <div className="alertas-list">
          {recomendacoes.map((alerta, idx) => (
            <AlertCard key={idx} {...alerta} />
          ))}
        </div>
      </section>

      <section className="alertas-section">
        <h3>Alertas de Mercado</h3>
        <div className="alertas-list">
          {alertasMercado.map((alerta, idx) => (
            <AlertCard key={idx} {...alerta} />
          ))}
        </div>
      </section>
    </div>
  )
}

