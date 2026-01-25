'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useProfile } from '../contexts/ProfileContext'
import { useState, useEffect } from 'react'
import { 
  FiLayout, 
  FiMessageSquare, 
  FiTrendingUp, 
  FiBell, 
  FiSend,
  FiShield,
  FiActivity,
  FiLink,
  FiCode,
  FiMenu,
  FiChevronLeft
} from 'react-icons/fi'
import '../globals.css'

const clienteMenuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: FiLayout },
  { href: '/chat-agent', label: 'Chat', icon: FiMessageSquare },
  { href: '/oportunidades', label: 'Oportunidades', icon: FiTrendingUp },
  { href: '/alertas', label: 'Alertas', icon: FiBell },
  { href: '/conexoes', label: 'Conexões (Open Finance)', icon: FiLink },
  { href: '/studio', label: 'Studio', icon: FiCode, isAdmin: true },
  { href: '/painel-do-agente', label: 'Painel do Agente', icon: FiActivity, isAdmin: true },
  { href: '/deploy', label: 'Deploy', icon: FiSend, isAdmin: true },
  { href: '/autonomia', label: 'Autonomia', icon: FiShield, isAdmin: true },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [isMinimized, setIsMinimized] = useState(false)
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebarMinimized')
      setIsMinimized(saved === 'true')
    }
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const root = document.documentElement
      if (isMinimized) {
        root.style.setProperty('--sidebar-width', '64px')
      } else {
        root.style.setProperty('--sidebar-width', '260px')
      }
    }
  }, [isMinimized])
  
  // Não mostrar sidebar na página inicial
  if (pathname === '/') {
    return null
  }

  const toggleMinimize = () => {
    const newState = !isMinimized
    setIsMinimized(newState)
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarMinimized', String(newState))
    }
  }

  return (
    <aside className={`sidebar ${isMinimized ? 'minimized' : ''}`}>
      <div className="sidebar-header">
        {!isMinimized && <h2>AlphaAdvisor</h2>}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {!isMinimized && <span className="profile-badge">Cliente</span>}
          <button
            onClick={toggleMinimize}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              transition: 'color 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)'
            }}
            title={isMinimized ? 'Expandir menu' : 'Minimizar menu'}
          >
            {isMinimized ? <FiMenu size={20} /> : <FiChevronLeft size={20} />}
          </button>
        </div>
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
              title={isMinimized ? item.label : undefined}
            >
              <Icon className="sidebar-icon" />
              <span>{item.label}</span>
              {item.isAdmin && !isMinimized && <span className="sidebar-badge">Admin</span>}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}




