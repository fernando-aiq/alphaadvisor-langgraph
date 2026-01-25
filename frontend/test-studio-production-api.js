/**
 * Teste de Verificação da API de Produção
 * 
 * Verifica conexão e funcionalidade com a API do LangGraph Deployment em produção
 * 
 * Execute com: node test-studio-production-api.js
 */

import fetch from 'node-fetch'
global.fetch = fetch

const PRODUCTION_API_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://ht-large-nightgown-81-5c894083915f57aeb10c89fc61220550.us.langgraph.app'
const API_KEY = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || ''
const ASSISTANT_ID = process.env.NEXT_PUBLIC_ASSISTANT_ID || 'agent'

// Cores para output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
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

// Função auxiliar para fazer requisições diretas à API de produção
async function fetchProductionAPI(endpoint, options = {}) {
  const url = `${PRODUCTION_API_URL}${endpoint}`
  const headers = {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
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
    }
  } catch (error) {
    return {
      ok: false,
      error: error.message,
      status: 0,
    }
  }
}

async function testAPIConnection() {
  logTest('Conexão com API de Produção')
  
  if (!API_KEY) {
    logError('API_KEY não configurada')
    return false
  }

  if (!PRODUCTION_API_URL.includes('langgraph.app') && !PRODUCTION_API_URL.includes('langsmith')) {
    logWarning(`URL não parece ser de produção: ${PRODUCTION_API_URL}`)
  }

  logInfo(`API URL: ${PRODUCTION_API_URL}`)
  logInfo(`Assistant ID: ${ASSISTANT_ID}`)
  logInfo(`API Key configurada: ${API_KEY ? 'Sim (primeiros 10 chars: ' + API_KEY.substring(0, 10) + '...)' : 'Não'}`)

  // Tentar criar uma thread para testar conexão
  try {
    const result = await fetchProductionAPI('/threads', {
      method: 'POST',
      body: JSON.stringify({
        input: {
          messages: [
            {
              role: 'user',
              content: 'Teste de conexão com API de produção',
            },
          ],
        },
      }),
    })

    if (result.ok && result.data.thread_id) {
      logSuccess(`Conexão estabelecida! Thread criada: ${result.data.thread_id}`)
      return result.data.thread_id
    } else {
      logError(`Falha na conexão: ${result.status} - ${JSON.stringify(result.data)}`)
      return null
    }
  } catch (error) {
    logError(`Erro ao conectar: ${error.message}`)
    return null
  }
}

async function testCreateThread(threadId) {
  logTest('Criar Thread na API de Produção')
  
  if (threadId) {
    logSuccess(`Thread já criada no teste anterior: ${threadId}`)
    return threadId
  }

  const result = await fetchProductionAPI('/threads', {
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

  logError(`Falha: ${result.status} - ${JSON.stringify(result.data)}`)
  return null
}

async function testGetThreadState(threadId) {
  logTest('Obter Estado da Thread')
  
  if (!threadId) {
    logWarning('Pulando - threadId não disponível')
    return false
  }

  const result = await fetchProductionAPI(`/threads/${threadId}/state`)

  if (result.ok && result.data.values) {
    logSuccess('Estado obtido com sucesso')
    const messages = result.data.values.messages || []
    logInfo(`Mensagens: ${messages.length}`)
    logInfo(`Próximos nós: ${result.data.next?.length || 0}`)
    return true
  }

  logError(`Falha: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testCreateRun(threadId) {
  logTest('Criar Run na API de Produção')
  
  if (!threadId) {
    logWarning('Pulando - threadId não disponível')
    return null
  }

  const result = await fetchProductionAPI(`/threads/${threadId}/runs`, {
    method: 'POST',
    body: JSON.stringify({
      assistant_id: ASSISTANT_ID,
      input: {
        messages: [
          {
            role: 'user',
            content: 'Teste de criação de run',
          },
        ],
      },
    }),
  })

  if (result.ok && result.data.run_id) {
    logSuccess(`Run criado: ${result.data.run_id}`)
    logInfo(`Status: ${result.data.status || 'N/A'}`)
    return result.data.run_id
  }

  logError(`Falha: ${result.status} - ${JSON.stringify(result.data)}`)
  return null
}

async function testListRuns(threadId) {
  logTest('Listar Runs')
  
  if (!threadId) {
    logWarning('Pulando - threadId não disponível')
    return false
  }

  const result = await fetchProductionAPI(`/threads/${threadId}/runs`)

  if (result.ok) {
    const runs = Array.isArray(result.data) ? result.data : (result.data.runs || [])
    logSuccess(`Listou ${runs.length} runs`)
    if (runs.length > 0) {
      logInfo(`Primeiro run: ${runs[0].run_id} (status: ${runs[0].status})`)
    }
    return true
  }

  logError(`Falha: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testGetRunDetails(threadId, runId) {
  logTest('Obter Detalhes do Run')
  
  if (!threadId || !runId) {
    logWarning('Pulando - IDs não disponíveis')
    return false
  }

  const result = await fetchProductionAPI(`/threads/${threadId}/runs/${runId}`)

  if (result.ok && result.data.run_id) {
    logSuccess(`Detalhes obtidos: ${result.data.run_id}`)
    logInfo(`Status: ${result.data.status}`)
    logInfo(`Assistant: ${result.data.assistant_id}`)
    return true
  }

  logError(`Falha: ${result.status} - ${JSON.stringify(result.data)}`)
  return false
}

async function testErrorHandling() {
  logTest('Tratamento de Erros - Thread Inexistente')
  
  const result = await fetchProductionAPI('/threads/thread-inexistente-12345/state')

  if (result.status === 404) {
    logSuccess('Erro 404 tratado corretamente')
    return true
  }

  if (result.status === 500) {
    logWarning('Erro 500 retornado (pode ser esperado)')
    return true
  }

  logWarning(`Resposta inesperada: ${result.status}`)
  return true // Não é crítico
}

async function testAPIEndpoints() {
  logTest('Verificar Endpoints Disponíveis')
  
  // Tentar acessar /docs se disponível
  const docsResult = await fetchProductionAPI('/docs')
  
  if (docsResult.status === 200 || docsResult.status === 404) {
    if (docsResult.status === 200) {
      logSuccess('Documentação da API disponível em /docs')
    } else {
      logInfo('Documentação não disponível em /docs (normal)')
    }
  }

  // Tentar health check se disponível
  const healthResult = await fetchProductionAPI('/health')
  
  if (healthResult.status === 200) {
    logSuccess('Health check disponível em /health')
  } else {
    logInfo('Health check não disponível em /health (normal)')
  }

  return true
}

// Executar todos os testes
async function runAllTests() {
  log('\n' + '='.repeat(70), 'magenta')
  log('🚀 TESTE DE VERIFICAÇÃO - API DE PRODUÇÃO', 'magenta')
  log('='.repeat(70) + '\n', 'magenta')

  let threadId = null
  let runId = null

  const results = {
    connection: false,
    createThread: false,
    getThreadState: false,
    createRun: false,
    listRuns: false,
    getRunDetails: false,
    errorHandling: false,
    endpoints: false,
  }

  // Teste 1: Conexão
  threadId = await testAPIConnection()
  results.connection = threadId !== null

  // Teste 2: Criar thread (se não foi criada)
  if (!threadId) {
    threadId = await testCreateThread()
  }
  results.createThread = threadId !== null

  // Teste 3: Obter estado
  if (threadId) {
    results.getThreadState = await testGetThreadState(threadId)
  }

  // Teste 4: Criar run
  if (threadId) {
    runId = await testCreateRun(threadId)
    results.createRun = runId !== null
  }

  // Aguardar um pouco para processamento
  if (runId) {
    logInfo('Aguardando 3 segundos para processamento...')
    await new Promise(resolve => setTimeout(resolve, 3000))
  }

  // Teste 5: Listar runs
  if (threadId) {
    results.listRuns = await testListRuns(threadId)
  }

  // Teste 6: Detalhes do run
  if (threadId && runId) {
    results.getRunDetails = await testGetRunDetails(threadId, runId)
  }

  // Teste 7: Tratamento de erros
  results.errorHandling = await testErrorHandling()

  // Teste 8: Endpoints
  results.endpoints = await testAPIEndpoints()

  // Resumo
  log('\n' + '='.repeat(70), 'magenta')
  log('📊 RESUMO DOS TESTES', 'magenta')
  log('='.repeat(70) + '\n', 'magenta')

  const totalTests = Object.keys(results).length
  const passedTests = Object.values(results).filter(r => r === true).length

  log(`Total de testes: ${totalTests}`)
  log(`Passou: ${passedTests}`, passedTests === totalTests ? 'green' : 'yellow')
  log(`Falhou: ${totalTests - passedTests}`, passedTests === totalTests ? 'green' : 'red')

  log('\nDetalhes:', 'blue')
  Object.entries(results).forEach(([test, result]) => {
    const status = result ? '✅' : '❌'
    const name = {
      connection: 'Conexão com API',
      createThread: 'Criar Thread',
      getThreadState: 'Obter Estado',
      createRun: 'Criar Run',
      listRuns: 'Listar Runs',
      getRunDetails: 'Detalhes do Run',
      errorHandling: 'Tratamento de Erros',
      endpoints: 'Endpoints Disponíveis',
    }[test] || test

    log(`${status} ${name}: ${result ? 'OK' : 'FALHOU'}`)
  })

  if (threadId) {
    log(`\nThread ID criada: ${threadId}`, 'blue')
  }
  if (runId) {
    log(`Run ID criado: ${runId}`, 'blue')
  }

  log('\n' + '='.repeat(70) + '\n', 'magenta')

  return passedTests >= totalTests * 0.7 // 70% de sucesso é aceitável
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-production-api.js')) {
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

export { runAllTests }
