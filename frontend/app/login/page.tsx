'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import Link from 'next/link'
import '../globals.css'

// URL da API - usar rewrite do Next.js em produção ou variável de ambiente
const getApiUrl = () => {
  // Em produção (Vercel), usar rewrite do Next.js (URL relativa)
  // O rewrite em next.config.js faz proxy server-side, evitando Mixed Content
  if (typeof window !== 'undefined') {
    // No cliente, usar URL relativa se estiver em produção (Vercel)
    // Isso usa o rewrite do Next.js que faz proxy server-side
    const isProduction = window.location.hostname.includes('vercel.app') || 
                         window.location.hostname.includes('vercel.com') ||
                         process.env.NODE_ENV === 'production'
    
    if (isProduction && !process.env.NEXT_PUBLIC_API_URL) {
      // Usar rewrite do Next.js (URL relativa)
      return ''
    }
    
    // Em desenvolvimento ou se NEXT_PUBLIC_API_URL estiver definido, usar variável
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
  // No servidor, usar variável de ambiente ou padrão
  return process.env.API_URL || 'http://localhost:8000'
}

const API_URL = getApiUrl()

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Usar URL relativa em produção (usa rewrite do Next.js) ou absoluta em desenvolvimento
      const apiEndpoint = API_URL ? `${API_URL}/api/auth/login` : '/api/auth/login'
      const response = await axios.post(apiEndpoint, {
        email,
        password,
      })
      
      if (response.data.token) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', response.data.token)
        }
        router.push('/chat')
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: '400px', margin: '4rem auto' }}>
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Login</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
              Email
            </label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
              Senha
            </label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          {error && (
            <div style={{ color: 'red', marginBottom: '1rem', textAlign: 'center' }}>
              {error}
            </div>
          )}
          <button 
            type="submit" 
            className="btn" 
            style={{ width: '100%' }}
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <Link href="/" style={{ color: '#667eea', textDecoration: 'none' }}>
            Voltar para home
          </Link>
        </div>
      </div>
    </div>
  )
}


