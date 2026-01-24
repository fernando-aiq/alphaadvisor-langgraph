import '../globals.css'

interface AlertCardProps {
  type: 'vencimento' | 'queda' | 'oportunidade' | 'recomendacao' | 'mercado'
  title: string
  time: string
  message: string
  actions: string[]
}

const typeColors: Record<string, string> = {
  vencimento: '#f59e0b',
  queda: '#ef4444',
  oportunidade: '#10b981',
  recomendacao: '#3b82f6',
  mercado: '#8b5cf6'
}

export default function AlertCard({ type, title, time, message, actions }: AlertCardProps) {
  const color = typeColors[type] || '#667eea'

  return (
    <div className="alert-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="alert-header">
        <h4>{title}</h4>
        <span className="alert-time">{time}</span>
      </div>
      <p className="alert-message">{message}</p>
      <div className="alert-actions">
        {actions.map((action, idx) => (
          <button
            key={idx}
            className="btn"
            style={{
              fontSize: '0.85rem',
              padding: '0.5rem 1rem',
              background: idx === 0 ? color : 'transparent',
              color: idx === 0 ? 'white' : color,
              border: idx > 0 ? `1px solid ${color}` : 'none'
            }}
          >
            {action}
          </button>
        ))}
      </div>
    </div>
  )
}




