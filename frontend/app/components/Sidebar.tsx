'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useProfile } from '../contexts/ProfileContext'
import { 
  FiLayout, 
  FiMessageSquare, 
  FiTrendingUp, 
  FiBell, 
  FiEye,
  FiSend,
  FiShield,
  FiActivity,
  FiLink,
  FiZap,
  FiCode
} from 'react-icons/fi'
import '../globals.css'

const clienteMenuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: FiLayout },
  { href: '/chat', label: 'Chat', icon: FiMessageSquare },
  { href: '/chat-agent', label: 'Chat Avançado', icon: FiZap },
  { href: '/studio', label: 'Studio', icon: FiCode, isAdmin: true },
  { href: '/oportunidades', label: 'Oportunidades', icon: FiTrendingUp },
  { href: '/alertas', label: 'Alertas', icon: FiBell },
  { href: '/conexoes', label: 'Conexões (Open Finance)', icon: FiLink },
  { href: '/painel-do-agente', label: 'Painel do Agente', icon: FiActivity, isAdmin: true },
  { href: '/deploy', label: 'Deploy', icon: FiSend, isAdmin: true },
  { href: '/visao-sistema', label: 'Visão do Sistema', icon: FiEye, isAdmin: true },
  { href: '/autonomia', label: 'Autonomia', icon: FiShield, isAdmin: true },
]

export default function Sidebar() {
  const pathname = usePathname()
  
  // Não mostrar sidebar na página inicial
  if (pathname === '/') {
    return null
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>AlphaAdvisor</h2>
        <span className="profile-badge">Cliente</span>
      </div>
      <nav className="sidebar-nav">
        {clienteMenuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-item ${isActive ? 'active' : ''}`}
            >
              <Icon className="sidebar-icon" />
              <span>{item.label}</span>
              {item.isAdmin && <span className="sidebar-badge">Admin</span>}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}




