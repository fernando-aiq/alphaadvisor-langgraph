'use client'

import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'

export default function ClientesPage() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(false)
  }, [])

  if (loading) {
    return <div>Carregando...</div>
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '20px' }}>
        <h1>Clientes</h1>
        <p>Página de gerenciamento de clientes em desenvolvimento.</p>
      </main>
    </div>
  )
}

