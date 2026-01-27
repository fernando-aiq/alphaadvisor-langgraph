'use client'

import { useProfile } from '../contexts/ProfileContext'
import { useState } from 'react'
import { useMediaQuery } from '../hooks/useMediaQuery'
import { FiMenu } from 'react-icons/fi'
import Sidebar from './Sidebar'
import '../globals.css'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { profile } = useProfile()
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const isMobile = useMediaQuery('(max-width: 768px)')

  // Se não há perfil selecionado, mostrar apenas o conteúdo (página de seleção)
  if (!profile) {
    return <>{children}</>
  }

  const toggleMobile = () => {
    setIsMobileOpen(!isMobileOpen)
  }

  const closeMobile = () => {
    setIsMobileOpen(false)
  }

  return (
    <div className="app-layout">
      {isMobile && (
        <>
          <button
            onClick={toggleMobile}
            className="mobile-menu-button"
            aria-label="Abrir menu"
          >
            <FiMenu size={24} />
          </button>
          {isMobileOpen && (
            <div 
              className="sidebar-overlay"
              onClick={closeMobile}
              aria-hidden="true"
            />
          )}
        </>
      )}
      <Sidebar isMobileOpen={isMobileOpen} onMobileClose={closeMobile} />
      <main className="main-content">
        <div className="content-area">
          {children}
        </div>
      </main>
    </div>
  )
}




