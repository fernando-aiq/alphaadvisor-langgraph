'use client'

import { useRouter } from 'next/navigation'
import { useProfile } from './contexts/ProfileContext'
import { useEffect } from 'react'
import './globals.css'

export default function Home() {
  const router = useRouter()
  const { setProfile } = useProfile()

  useEffect(() => {
    setProfile('cliente')
    router.replace('/dashboard')
  }, [router, setProfile])

  return null
}

