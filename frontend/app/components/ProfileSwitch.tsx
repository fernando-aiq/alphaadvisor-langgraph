'use client'

import React from 'react'
import { useProfile } from '../contexts/ProfileContext'
import { FiUser, FiUserCheck } from 'react-icons/fi'
import '../globals.css'

export default function ProfileSwitch() {
  const { profile, setProfile } = useProfile()

  // Se não houver perfil, não mostrar o switch
  if (!profile) {
    return null
  }

  const handleToggle = () => {
    const newProfile = profile === 'cliente' ? 'assessor' : 'cliente'
    setProfile(newProfile)
  }

  return (
    <div className="profile-switch-container">
      <button
        className="profile-switch"
        onClick={handleToggle}
        aria-label={`Alternar para modo ${profile === 'cliente' ? 'assessor' : 'cliente'}`}
      >
        <div className={`profile-switch-option ${profile === 'cliente' ? 'active' : ''}`}>
          <FiUser size={16} />
          <span>Cliente</span>
        </div>
        <div className={`profile-switch-option ${profile === 'assessor' ? 'active' : ''}`}>
          <FiUserCheck size={16} />
          <span>Assessor</span>
        </div>
        <div 
          className={`profile-switch-slider ${profile === 'assessor' ? 'right' : 'left'}`}
          aria-hidden="true"
        />
      </button>
    </div>
  )
}

