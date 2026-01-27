'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useProfile } from '../contexts/ProfileContext'
import { useState, useEffect } from 'react'
import { useMediaQuery } from '../hooks/useMediaQuery'
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
  FiChevronLeft,
  FiX
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

interface SidebarProps {
  isMobileOpen?: boolean
  onMobileClose?: () => void
}

export default function Sidebar({ isMobileOpen = false, onMobileClose }: SidebarProps) {
  const pathname = usePathname()
  const [isMinimized, setIsMinimized] = useState(false)
  const isMobile = useMediaQuery('(max-width: 768px)')
  
  useEffect(() => {
    if (typeof window !== 'undefined' && !isMobile) {
      const saved = localStorage.getItem('sidebarMinimized')
      setIsMinimized(saved === 'true')
    }
  }, [isMobile])

  useEffect(() => {
    if (typeof window !== 'undefined' && !isMobile) {
      const root = document.documentElement
      if (isMinimized) {
        root.style.setProperty('--sidebar-width', '64px')
      } else {
        root.style.setProperty('--sidebar-width', '260px')
      }
    }
  }, [isMinimized, isMobile])
  
  // Não mostrar sidebar na página inicial
  if (pathname === '/') {
    return null
  }

  const toggleMinimize = () => {
    if (isMobile) return
    const newState = !isMinimized
    setIsMinimized(newState)
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarMinimized', String(newState))
    }
  }

  const handleLinkClick = () => {
    if (isMobile && onMobileClose) {
      onMobileClose()
    }
  }

  return (
    <aside className={`sidebar ${isMinimized ? 'minimized' : ''} ${isMobileOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        {!isMinimized && <h2>AlphaAdvisor</h2>}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isMobile ? (
            <button
              onClick={onMobileClose}
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
              title="Fechar menu"
            >
              <FiX size={20} />
            </button>
          ) : (
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
          )}
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
              onClick={handleLinkClick}
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




