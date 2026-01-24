'use client'

import { useRouter } from 'next/navigation'
import { useProfile } from './contexts/ProfileContext'
import { FiUser } from 'react-icons/fi'
import './globals.css'

export default function Home() {
  const router = useRouter()
  const { setProfile } = useProfile()

  const handleProfileSelect = () => {
    setProfile('cliente')
    router.push('/dashboard')
  }

  return (
    <div className="profile-selection">
      <div className="profile-selection-card">
        <div className="profile-selection-header">
          <h1>Assessor Virtual</h1>
          <p>Escolha seu perfil de uso</p>
        </div>
        
        <p className="profile-selection-subtitle">
          Bem-vindo ao Assessor Virtual
        </p>

        <div className="profile-options">
          <button
            className="profile-option"
            onClick={handleProfileSelect}
          >
            <div className="profile-option-icon">
              <FiUser size={48} />
            </div>
            <h3>Cliente</h3>
            <p>Respostas diretas sobre seus investimentos pessoais</p>
          </button>
        </div>
      </div>
    </div>
  )
}

