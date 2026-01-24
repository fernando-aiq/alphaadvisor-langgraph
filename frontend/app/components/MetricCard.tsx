import { IconType } from 'react-icons'
import '../globals.css'

interface MetricCardProps {
  change: string
  value: string
  amount: string
  icon: IconType
  color: string
}

export default function MetricCard({ change, value, amount, icon: Icon, color }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <div className="metric-icon" style={{ background: `${color}20`, color }}>
          <Icon size={24} />
        </div>
        <span className="metric-change" style={{ color }}>
          {change}
        </span>
      </div>
      <div className="metric-content">
        <h3 className="metric-value">{value}</h3>
        <p className="metric-amount">{amount}</p>
      </div>
    </div>
  )
}




