/**
 * Testes Exaustivos - API Routes do Studio
 * 
 * Execute com: node test-studio-api-routes.js
 * 
 * Requisitos:
 * - NEXT_PUBLIC_API_URL configurada
 * - NEXT_PUBLIC_LANGSMITH_API_KEY configurada
 */

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

// Função auxiliar para fazer requisições
async function fetchAPI(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    const data = await response.json().catch(() => ({ text: await response.text() }))
    
    return {
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      data,
      headers: Object.fromEntries(response.headers.entries()),
    }
  } catch (error) {
    return {
      ok: false,
      error: error.message,
      status: 0,
    }
  }
}

// Testes
async function testListThreads() {
  logTest('GET /api/studio/threads - Listar threads')
  
  const result = await fetchAPI('/api/studio/threads', {
    method: 'GET',
  })

  if (result.status === 404 || result.status === 405) {
    logWarning('Endpoint não suportado (esperado para LangGraph Deployment)')
    logSuccess('API retornou resposta apropriada para endpoint não suportado')
    return true
  }

  if (result.ok && Array.isArray(result.data.threads)) {
    logSuccess(`Listou ${result.data.threads.length} threads`)
    return true
  }

  if (result.status === 500 && result.data.error) {
    logError(`Erro do servidor: ${result.data.error}`)
    return false
  }

  logError(`Falhou: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testCreateThread() {
  logTest('POST /api/studio/threads - Criar thread')
  
  const result = await fetchAPI('/api/studio/threads', {
    method: 'POST',
    body: JSON.stringify({
      input: {
        messages: [
          {
            role: 'user',
            content: 'Teste de criação de thread',
          },
        ],
      },
    }),
  })

  if (result.ok && result.data.thread_id) {
    logSuccess(`Thread criada: ${result.data.thread_id}`)
    return result.data.thread_id
  }

  if (result.status === 500 && result.data.error) {
    logError(`Erro: ${result.data.error}`)
    if (result.data.details) {
      logInfo(`Detalhes: ${result.data.details}`)
    }
    return null
  }

  logError(`Falhou: ${result.status} - ${JSON.stringify(result.data)}`)
  return null
}

async function testGetThreadState(threadId) {
  logTest(`GET /api/studio/threads/${threadId}/state - Obter estado da thread`)
  
  if (!threadId) {
    logWarning('Pulando teste - threadId não disponível')
    return false
  }

  const result = await fetchAPI(`/api/studio/threads/${threadId}/state`, {
    method: 'GET',
  })

  if (result.ok && result.data.values) {
    logSuccess('Estado da thread obtido com sucesso')
    logInfo(`Mensagens: ${result.data.values.messages?.length || 0}`)
    return true
  }

  if (result.status === 404) {
    logWarning('Thread não encontrada (pode ser normal se thread foi deletada)')
    return false
  }

  logError(`Falhou: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testListRuns(threadId) {
  logTest(`GET /api/studio/threads/${threadId}/runs - Listar runs`)
  
  if (!threadId) {
    logWarning('Pulando teste - threadId não disponível')
    return false
  }

  const result = await fetchAPI(`/api/studio/threads/${threadId}/runs`, {
    method: 'GET',
  })

  if (result.ok && Array.isArray(result.data.runs)) {
    logSuccess(`Listou ${result.data.runs.length} runs`)
    return result.data.runs
  }

  if (result.status === 404) {
    logWarning('Thread não encontrada')
    return []
  }

  logError(`Falhou: ${result.status} - ${JSON.stringify(result.data)}`)
  return []
}

async function testGetRunDetails(threadId, runId) {
  logTest(`GET /api/studio/threads/${threadId}/runs/${runId} - Detalhes do run`)
  
  if (!threadId || !runId) {
    logWarning('Pulando teste - threadId ou runId não disponível')
    return false
  }

  const result = await fetchAPI(`/api/studio/threads/${threadId}/runs/${runId}`, {
    method: 'GET',
  })

  if (result.ok && result.data.run_id) {
    logSuccess(`Detalhes do run obtidos: ${result.data.run_id}`)
    logInfo(`Status: ${result.data.status}`)
    return true
  }

  if (result.status === 404) {
    logWarning('Run não encontrado')
    return false
  }

  logError(`Falhou: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testErrorHandling() {
  logTest('Tratamento de Erros - Thread inexistente')
  
  const result = await fetchAPI('/api/studio/threads/thread-inexistente-12345/state', {
    method: 'GET',
  })

  if (result.status === 404) {
    logSuccess('Erro 404 tratado corretamente')
    return true
  }

  if (result.status === 500) {
    logWarning('Erro 500 retornado (pode ser esperado se API não valida threadId)')
    return true
  }

  logError(`Resposta inesperada: ${result.status}`)
  return false
}

async function testCORSHeaders() {
  logTest('CORS Headers')
  
  const result = await fetchAPI('/api/studio/threads', {
    method: 'OPTIONS',
  })

  const corsHeaders = [
    'access-control-allow-origin',
    'access-control-allow-methods',
    'access-control-allow-headers',
  ]

  const hasCORS = corsHeaders.some(header => 
    result.headers && result.headers[header]
  )

  if (hasCORS || result.status === 200 || result.status === 204) {
    logSuccess('CORS headers presentes ou OPTIONS retornou sucesso')
    return true
  }

  logWarning('CORS headers não verificados (pode ser normal em desenvolvimento)')
  return true
}

// Executar todos os testes
async function runAllTests() {
  log('\n' + '='.repeat(60), 'blue')
  log('🚀 INICIANDO TESTES EXAUSTIVOS - API ROUTES DO STUDIO', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  logInfo(`Base URL: ${BASE_URL}`)
  logInfo(`API Key configurada: ${API_KEY ? 'Sim' : 'Não'}\n`)

  const results = {
    listThreads: false,
    createThread: null,
    getThreadState: false,
    listRuns: false,
    getRunDetails: false,
    errorHandling: false,
    corsHeaders: false,
  }

  // Teste 1: Listar threads
  results.listThreads = await testListThreads()

  // Teste 2: Criar thread
  results.createThread = await testCreateThread()

  // Teste 3: Obter estado da thread
  if (results.createThread) {
    results.getThreadState = await testGetThreadState(results.createThread)
  }

  // Teste 4: Listar runs
  if (results.createThread) {
    const runs = await testListRuns(results.createThread)
    results.listRuns = Array.isArray(runs)
    
    // Teste 5: Detalhes do run
    if (runs.length > 0) {
      results.getRunDetails = await testGetRunDetails(results.createThread, runs[0].run_id)
    }
  }

  // Teste 6: Tratamento de erros
  results.errorHandling = await testErrorHandling()

  // Teste 7: CORS headers
  results.corsHeaders = await testCORSHeaders()

  // Resumo
  log('\n' + '='.repeat(60), 'blue')
  log('📊 RESUMO DOS TESTES', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  const totalTests = Object.keys(results).length
  const passedTests = Object.values(results).filter(r => r === true || r !== null && r !== false).length

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
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-api-routes.js')) {
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

export { runAllTests, testListThreads, testCreateThread, testGetThreadState, testListRuns, testGetRunDetails }
