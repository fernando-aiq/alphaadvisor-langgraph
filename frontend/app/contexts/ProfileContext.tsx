'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'

export type ProfileType = 'cliente' | 'assessor' | null

interface ProfileContextType {
  profile: ProfileType
  setProfile: (profile: ProfileType) => void
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined)

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfileState] = useState<ProfileType>(null)

  useEffect(() => {
    // Forçar perfil para cliente sempre
    if (typeof window !== 'undefined') {
      const savedProfile = localStorage.getItem('profile') as ProfileType
      // Se for assessor ou null, forçar para cliente
      if (savedProfile !== 'cliente') {
        setProfileState('cliente')
        localStorage.setItem('profile', 'cliente')
      } else {
        setProfileState('cliente')
      }
    }
  }, [])

  const setProfile = (newProfile: ProfileType) => {
    // Sempre forçar para cliente, ignorando tentativas de mudar para assessor
    const profileToSet = newProfile === 'assessor' ? 'cliente' : (newProfile || 'cliente')
    setProfileState(profileToSet)
    if (typeof window !== 'undefined') {
      localStorage.setItem('profile', 'cliente')
    }
  }

  return (
    <ProfileContext.Provider value={{ profile, setProfile }}>
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  const context = useContext(ProfileContext)
  if (context === undefined) {
    throw new Error('useProfile must be used within a ProfileProvider')
  }
  return context
}




