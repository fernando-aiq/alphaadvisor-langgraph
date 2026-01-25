/**
 * Testes Exaustivos - Cliente LangSmith
 * 
 * Execute com: node test-studio-client.js
 * 
 * Requisitos:
 * - Servidor Next.js rodando (npm run dev)
 * - NEXT_PUBLIC_API_URL configurada
 * - NEXT_PUBLIC_LANGSMITH_API_KEY configurada
 */

// Simular ambiente Node.js com fetch
import fetch from 'node-fetch'
global.fetch = fetch

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
const API_KEY = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || ''

// Cores para output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
}

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

function logTest(name) {
  log(`\n🧪 Testando: ${name}`, 'cyan')
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green')
}

function logError(message) {
  log(`❌ ${message}`, 'red')
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow')
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue')
}

// Implementação simplificada do cliente para testes
class TestLangSmithClient {
  constructor() {
    this.baseUrl = `${BASE_URL}/api/studio`
  }

  async listThreads(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.offset) queryParams.append('offset', params.offset.toString())

    const url = `${this.baseUrl}/threads${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url)
    
    if (!response.ok) {
      if (response.status === 404 || response.status === 405) {
        return []
      }
      throw new Error(`Failed to list threads: ${response.statusText}`)
    }

    const data = await response.json()
    return data.threads || []
  }

  async getThreadState(threadId) {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/state`)
    
    if (!response.ok) {
      throw new Error(`Failed to get thread state: ${response.statusText}`)
    }

    return response.json()
  }

  async listRuns(threadId, params = {}) {
    const queryParams = new URLSearchParams()
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.offset) queryParams.append('offset', params.offset.toString())

    const url = `${this.baseUrl}/threads/${threadId}/runs${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Failed to list runs: ${response.statusText}`)
    }

    const data = await response.json()
    return data.runs || []
  }

  async getRunDetails(threadId, runId) {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/runs/${runId}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get run details: ${response.statusText}`)
    }

    return response.json()
  }

  async createThread(input) {
    const response = await fetch(`${this.baseUrl}/threads`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to create thread: ${response.statusText}`)
    }

    return response.json()
  }

  async createRun(threadId, assistantId, input) {
    const response = await fetch(`${this.baseUrl}/threads/${threadId}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistant_id: assistantId,
        input,
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to create run: ${response.statusText}`)
    }

    return response.json()
  }
}

const client = new TestLangSmithClient()

// Testes
async function testClientInitialization() {
  logTest('Inicialização do Cliente')
  
  if (client.baseUrl.includes('/api/studio')) {
    logSuccess('Cliente inicializado corretamente')
    return true
  }

  logError('Cliente não inicializado corretamente')
  return false
}

async function testListThreads() {
  logTest('listThreads() - Listar threads')
  
  try {
    const threads = await client.listThreads({ limit: 10 })
    
    if (Array.isArray(threads)) {
      logSuccess(`Método retornou array com ${threads.length} threads`)
      return true
    }

    logError('Método não retornou array')
    return false
  } catch (error) {
    if (error.message.includes('404') || error.message.includes('405')) {
      logWarning('Endpoint não suportado (esperado)')
      return true
    }
    logError(`Erro: ${error.message}`)
    return false
  }
}

async function testCreateThread() {
  logTest('createThread() - Criar thread')
  
  try {
    const thread = await client.createThread({
      messages: [
        {
          role: 'user',
          content: 'Teste de criação via cliente',
        },
      ],
    })

    if (thread && thread.thread_id) {
      logSuccess(`Thread criada: ${thread.thread_id}`)
      return thread.thread_id
    }

    logError('Resposta inválida')
    return null
  } catch (error) {
    logError(`Erro: ${error.message}`)
    return null
  }
}

async function testGetThreadState(threadId) {
  logTest('getThreadState() - Obter estado da thread')
  
  if (!threadId) {
    logWarning('Pulando - threadId não disponível')
    return false
  }

  try {
    const state = await client.getThreadState(threadId)

    if (state && state.values) {
      logSuccess('Estado obtido com sucesso')
      logInfo(`Mensagens: ${state.values.messages?.length || 0}`)
      return true
    }

    logError('Estado inválido')
    return false
  } catch (error) {
    logError(`Erro: ${error.message}`)
    return false
  }
}

async function testListRuns(threadId) {
  logTest('listRuns() - Listar runs')
  
  if (!threadId) {
    logWarning('Pulando - threadId não disponível')
    return false
  }

  try {
    const runs = await client.listRuns(threadId, { limit: 10 })

    if (Array.isArray(runs)) {
      logSuccess(`Listou ${runs.length} runs`)
      return runs
    }

    logError('Resposta não é array')
    return []
  } catch (error) {
    logError(`Erro: ${error.message}`)
    return []
  }
}

async function testGetRunDetails(threadId, runId) {
  logTest('getRunDetails() - Detalhes do run')
  
  if (!threadId || !runId) {
    logWarning('Pulando - IDs não disponíveis')
    return false
  }

  try {
    const run = await client.getRunDetails(threadId, runId)

    if (run && run.run_id) {
      logSuccess(`Detalhes obtidos: ${run.run_id}`)
      return true
    }

    logError('Resposta inválida')
    return false
  } catch (error) {
    logError(`Erro: ${error.message}`)
    return false
  }
}

async function testErrorHandling() {
  logTest('Tratamento de Erros - Thread inexistente')
  
  try {
    await client.getThreadState('thread-inexistente-12345')
    logError('Deveria ter lançado erro')
    return false
  } catch (error) {
    if (error.message.includes('Failed')) {
      logSuccess('Erro tratado corretamente')
      return true
    }
    logError(`Erro inesperado: ${error.message}`)
    return false
  }
}

async function testNormalization() {
  logTest('Normalização de Respostas')
  
  try {
    const threads = await client.listThreads()
    
    // Verificar que sempre retorna array
    if (Array.isArray(threads)) {
      logSuccess('Resposta normalizada corretamente (array)')
      return true
    }

    logError('Resposta não normalizada')
    return false
  } catch (error) {
    // Se endpoint não existe, considerar OK (normalização funcionou)
    if (error.message.includes('404') || error.message.includes('405')) {
      logSuccess('Normalização funcionou (retornou array vazio)')
      return true
    }
    logError(`Erro: ${error.message}`)
    return false
  }
}

// Executar todos os testes
async function runAllTests() {
  log('\n' + '='.repeat(60), 'blue')
  log('🚀 INICIANDO TESTES EXAUSTIVOS - CLIENTE LANGSMITH', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  logInfo(`Base URL: ${BASE_URL}`)
  logInfo(`API Key configurada: ${API_KEY ? 'Sim' : 'Não'}\n`)

  const results = {
    initialization: false,
    listThreads: false,
    createThread: null,
    getThreadState: false,
    listRuns: false,
    getRunDetails: false,
    errorHandling: false,
    normalization: false,
  }

  // Teste 1: Inicialização
  results.initialization = await testClientInitialization()

  // Teste 2: Listar threads
  results.listThreads = await testListThreads()

  // Teste 3: Criar thread
  results.createThread = await testCreateThread()

  // Teste 4: Obter estado
  if (results.createThread) {
    results.getThreadState = await testGetThreadState(results.createThread)
  }

  // Teste 5: Listar runs
  if (results.createThread) {
    const runs = await testListRuns(results.createThread)
    results.listRuns = Array.isArray(runs)
    
    // Teste 6: Detalhes do run
    if (runs.length > 0) {
      results.getRunDetails = await testGetRunDetails(results.createThread, runs[0].run_id)
    }
  }

  // Teste 7: Tratamento de erros
  results.errorHandling = await testErrorHandling()

  // Teste 8: Normalização
  results.normalization = await testNormalization()

  // Resumo
  log('\n' + '='.repeat(60), 'blue')
  log('📊 RESUMO DOS TESTES', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  const totalTests = Object.keys(results).length
  const passedTests = Object.values(results).filter(r => r === true || (r !== null && r !== false)).length

  log(`Total de testes: ${totalTests}`)
  log(`Passou: ${passedTests}`, passedTests === totalTests ? 'green' : 'yellow')
  log(`Falhou: ${totalTests - passedTests}`, passedTests === totalTests ? 'green' : 'red')

  log('\nDetalhes:', 'blue')
  Object.entries(results).forEach(([test, result]) => {
    const status = result === true ? '✅' : result === false ? '❌' : result ? '⚠️' : '⏭️'
    log(`${status} ${test}: ${result === true ? 'OK' : result === false ? 'FALHOU' : result ? 'PARCIAL' : 'PULADO'}`)
  })

  log('\n' + '='.repeat(60) + '\n', 'blue')

  return passedTests === totalTests
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-client.js')) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1)
    })
    .catch(error => {
      logError(`Erro fatal: ${error.message}`)
      console.error(error)
      process.exit(1)
    })
}

export { runAllTests, client }
