'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useProfile } from '../contexts/ProfileContext'
import axios from 'axios'
import '../globals.css'

// Função para obter URL da API no runtime (não no build time)
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    // No servidor, usar variável de ambiente
    return process.env.API_URL || 'http://localhost:8000'
  }
  
  // No cliente, verificar no runtime
  const isVercel = window.location.hostname.includes('vercel.app') || 
                   window.location.hostname.includes('vercel.com')
  
  // Se estiver no Vercel, usar rewrite do Next.js (URL relativa)
  // Isso evita Mixed Content fazendo proxy server-side
  if (isVercel) {
    return '' // URL relativa usa o rewrite
  }
  
  // Em desenvolvimento local, usar variável ou padrão
  // NEXT_PUBLIC_* variáveis são injetadas no build, mas podemos verificar
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  trace_id?: string
}

export default function Chat() {
  const { profile } = useProfile()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, typing])

  useEffect(() => {
    // Focar no input quando componente monta
    inputRef.current?.focus()
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || loading) {
      console.log('[Chat] Envio bloqueado:', { input: input.trim(), loading })
      return
    }

    const currentInput = input
    console.log('[Chat] Iniciando envio de mensagem:', currentInput)
    
    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setTyping(true)

    try {
      // Obter URL da API no runtime
      const apiUrl = getApiUrl()
      const apiEndpoint = apiUrl ? `${apiUrl}/api/chat` : '/api/chat'
      
      console.log('[Chat] Enviando para:', apiEndpoint, 'Mensagem:', currentInput)
      
      // Preparar contexto: histórico de mensagens anteriores (user e assistant)
      const context = messages.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }))

      const response = await axios.post(
        apiEndpoint,
        { 
          message: currentInput,
          context: context
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 30000, // 30 segundos
        }
      )
      
      console.log('[Chat] Resposta recebida:', response.status)
      console.log('[Chat] Headers:', JSON.stringify(response.headers, null, 2))
      console.log('[Chat] Data completa:', JSON.stringify(response.data, null, 2))
      console.log('[Chat] Tipo de data:', typeof response.data)
      console.log('[Chat] Data é vazia?', !response.data || (typeof response.data === 'object' && Object.keys(response.data).length === 0))
      console.log('[Chat] Response text:', response.request?.responseText)
      console.log('[Chat] Response status text:', response.statusText)
      console.log('[Chat] Response config:', response.config)

      setTyping(false)
      
      // Verificar se a resposta está realmente vazia
      const isEmpty = !response.data || 
                     (typeof response.data === 'string' && response.data.trim() === '') ||
                     (typeof response.data === 'object' && Object.keys(response.data).length === 0)
      
      if (isEmpty) {
        console.error('[Chat] ERRO: Resposta da API está vazia ou inválida')
        console.error('[Chat] Status:', response.status)
        console.error('[Chat] Headers:', JSON.stringify(response.headers, null, 2))
        console.error('[Chat] URL chamada:', apiEndpoint)
        console.error('[Chat] Response request:', response.request)
        
        // Tentar obter resposta alternativa do request
        const responseText = response.request?.responseText || response.data || ''
        console.error('[Chat] Response text alternativo:', responseText)
        
        const errorMessage: Message = {
          role: 'assistant',
          content: 'Erro: A API retornou uma resposta vazia. Isso pode indicar que o backend não está configurado corretamente ou não está acessível. Verifique se a variável API_URL está configurada no Vercel e se o backend está rodando.',
        }
        setMessages((prev) => [...prev, errorMessage])
        return
      }
      
      // Debug: log da resposta para verificar o formato
      console.log('[Chat] Resposta completa da API:', response.data)
      console.log('[Chat] Trace ID recebido:', response.data?.trace_id)
      
      // Extrair resposta da API - tentar múltiplos campos
      let responseText = response.data?.response || 
                        response.data?.message || 
                        response.data?.content ||
                        (typeof response.data === 'string' ? response.data : null)
      
      // Se ainda não tiver resposta, usar fallback
      if (!responseText || responseText.trim() === '') {
        responseText = 'Desculpe, não consegui processar sua mensagem. A resposta da API está vazia. Por favor, verifique se o backend está configurado corretamente.'
        console.error('Resposta vazia ou inválida da API:', {
          data: response.data,
          status: response.status,
          headers: response.headers,
          url: apiEndpoint
        })
      }
      
      const traceId = response.data?.trace_id || response.data?.traceId || null
      console.log('[Chat] Trace ID extraído:', traceId)
      console.log('[Chat] Trace ID existe?', !!traceId)
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: responseText,
        trace_id: traceId
      }
      
      console.log('[Chat] Mensagem criada com trace_id:', assistantMessage.trace_id)
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      setTyping(false)
      console.error('[Chat] Erro ao enviar mensagem:', err)
      console.error('[Chat] Detalhes do erro:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        url: err.config?.url
      })
      
      const errorMessage: Message = {
        role: 'assistant',
        content: err.response?.data?.message || 
                err.response?.data?.error ||
                `Erro ao enviar mensagem: ${err.message}. Por favor, tente novamente.`,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
    // Ctrl+K para nova conversa
    if (e.key === 'k' && e.ctrlKey) {
      e.preventDefault()
      setMessages([])
    }
  }

  const startNewConversation = () => {
    setMessages([])
    inputRef.current?.focus()
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div>
          <h2>Olá {profile === 'assessor' ? 'Assessor' : 'Cliente'}!</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Assessor Virtual está pronto para ajudar
          </p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={startNewConversation}
          style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
        >
          Nova Conversa
        </button>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Comece uma conversa digitando uma mensagem abaixo</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                Pressione Enter para enviar • Shift+Enter para nova linha • Ctrl+K para nova conversa
              </p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className="chat-message-content">
                {msg.content}
              </div>
              {msg.role === 'assistant' && msg.trace_id && (
                <div style={{ marginTop: '0.5rem' }}>
                  <button
                    onClick={() => router.push(`/trace/${msg.trace_id}`)}
                    style={{
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.75rem',
                      border: '1px solid #2196F3',
                      borderRadius: '4px',
                      backgroundColor: 'transparent',
                      color: '#2196F3',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#2196F3'
                      e.currentTarget.style.color = 'white'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent'
                      e.currentTarget.style.color = '#2196F3'
                    }}
                  >
                    🔍 Ver Fluxo de Raciocínio
                  </button>
                </div>
              )}
            </div>
          ))}
          {typing && (
            <div className="chat-message assistant">
              <div className="chat-message-content typing-indicator">
                <span>Assessor Virtual está digitando</span>
                <span className="typing-dots">
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Digite sua mensagem..."
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            className="btn chat-send-btn"
            disabled={loading || !input.trim()}
          >
            Enviar
          </button>
        </div>
        <div className="chat-hints">
          <span>Enter para enviar</span>
          <span>•</span>
          <span>Shift+Enter para nova linha</span>
          <span>•</span>
          <span>Ctrl+K para nova conversa</span>
        </div>
      </div>
    </div>
  )
}

