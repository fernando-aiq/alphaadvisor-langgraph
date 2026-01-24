'use client'

import { useProfile } from '../contexts/ProfileContext'
import Sidebar from './Sidebar'
import '../globals.css'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { profile } = useProfile()

  // Se não há perfil selecionado, mostrar apenas o conteúdo (página de seleção)
  if (!profile) {
    return <>{children}</>
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <header className="main-header">
          <div className="header-content">
            <h1>Assessor Virtual</h1>
          </div>
        </header>
        <div className="content-area">
          {children}
        </div>
      </main>
    </div>
  )
}




