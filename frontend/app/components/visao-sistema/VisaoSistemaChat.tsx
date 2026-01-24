'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import axios from 'axios'

const getApiUrl = () => {
  if (typeof window === 'undefined') return process.env.API_URL || 'http://localhost:8000'
  const isVercel = window.location.hostname.includes('vercel.app') || window.location.hostname.includes('vercel.com')
  if (isVercel) return ''
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  trace_id?: string | null
}

interface VisaoSistemaChatProps {
  onTraceId: (traceId: string) => void
}

export default function VisaoSistemaChat({ onTraceId }: VisaoSistemaChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  useEffect(() => { scrollToBottom() }, [messages, typing])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = { role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setTyping(true)

    try {
      const apiUrl = getApiUrl()
      const apiEndpoint = apiUrl ? `${apiUrl}/api/chat` : '/api/chat'

      const context = messages.map((m) => ({ role: m.role, content: m.content }))

      const response = await axios.post(
        apiEndpoint,
        { message: userMessage.content, context },
        { headers: { 'Content-Type': 'application/json' }, timeout: 30000 }
      )

      setTyping(false)

      const data = response.data
      if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Erro: resposta vazia da API.' }
        ])
        return
      }

      const text =
        data.response ?? data.message ?? data.content ?? (typeof data === 'string' ? data : null)
      const traceId = data.trace_id ?? data.traceId ?? null

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: text?.trim() || 'Sem resposta.', trace_id: traceId }
      ])

      if (traceId && typeof traceId === 'string') {
        onTraceId(traceId)
      }
    } catch (err: any) {
      setTyping(false)
      const msg =
        err.response?.data?.message ??
        err.response?.data?.error ??
        `Erro: ${err.message || 'tente novamente.'}`
      setMessages((prev) => [...prev, { role: 'assistant', content: msg }])
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="visao-sistema-chat" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        className="chat-messages"
        style={{ flex: 1, overflowY: 'auto', padding: '1rem', minHeight: 120 }}
      >
        {messages.length === 0 && (
          <div className="chat-empty" style={{ padding: '1.5rem' }}>
            <p>Envie uma mensagem para testar. O fluxo da última execução será mostrado no grafo acima.</p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Enter para enviar
            </p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <div className="chat-message-content">{msg.content}</div>
            {msg.role === 'assistant' && msg.trace_id && (
              <div style={{ marginTop: '0.5rem' }}>
                <Link
                  href={`/trace/${msg.trace_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.75rem',
                    border: '1px solid #2196F3',
                    borderRadius: '4px',
                    backgroundColor: 'transparent',
                    color: '#2196F3',
                    textDecoration: 'none',
                    display: 'inline-block',
                  }}
                >
                  Abrir trace em nova aba
                </Link>
              </div>
            )}
          </div>
        ))}
        {typing && (
          <div className="chat-message assistant">
            <div className="chat-message-content typing-indicator">
              <span>Digitando</span>
              <span className="typing-dots"><span>.</span><span>.</span><span>.</span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Digite para testar o agente..."
          disabled={loading}
        />
        <button
          type="button"
          onClick={sendMessage}
          className="btn chat-send-btn"
          disabled={loading || !input.trim()}
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
