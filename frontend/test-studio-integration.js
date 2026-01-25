/**
 * Teste de Integração Completo - Studio
 * 
 * Testa o fluxo completo: criar thread → visualizar → ver detalhes
 * 
 * Execute com: node test-studio-integration.js
 * 
 * Requisitos:
 * - Servidor Next.js rodando (npm run dev)
 * - NEXT_PUBLIC_API_URL configurada apontando para LangGraph Deployment
 * - NEXT_PUBLIC_LANGSMITH_API_KEY configurada
 */

import fetch from 'node-fetch'
global.fetch = fetch

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
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

function logStep(step, message) {
  log(`\n${step}. ${message}`, 'magenta')
}

function logSuccess(message) {
  log(`   ✅ ${message}`, 'green')
}

function logError(message) {
  log(`   ❌ ${message}`, 'red')
}

function logInfo(message) {
  log(`   ℹ️  ${message}`, 'blue')
}

function logWarning(message) {
  log(`   ⚠️  ${message}`, 'yellow')
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

// Aguardar um pouco
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Teste de integração completo
async function testFullIntegration() {
  log('\n' + '='.repeat(70), 'cyan')
  log('🚀 TESTE DE INTEGRAÇÃO COMPLETO - STUDIO', 'cyan')
  log('='.repeat(70) + '\n', 'cyan')

  logInfo(`Base URL: ${BASE_URL}`)
  logInfo(`Assistant ID: ${ASSISTANT_ID}`)
  logInfo(`API Key configurada: ${API_KEY ? 'Sim' : 'Não'}\n`)

  let threadId = null
  let runId = null
  const errors = []

  try {
    // Passo 1: Criar thread via API route
    logStep(1, 'Criar thread via POST /api/studio/threads')
    
    const createResult = await fetchAPI('/api/studio/threads', {
      method: 'POST',
      body: JSON.stringify({
        input: {
          messages: [
            {
              role: 'user',
              content: 'Teste de integração completo do Studio',
            },
          ],
        },
      }),
    })

    if (!createResult.ok || !createResult.data.thread_id) {
      throw new Error(`Falha ao criar thread: ${JSON.stringify(createResult.data)}`)
    }

    threadId = createResult.data.thread_id
    logSuccess(`Thread criada: ${threadId}`)

    // Passo 2: Aguardar processamento
    logStep(2, 'Aguardar processamento inicial')
    await sleep(2000)
    logSuccess('Aguardou 2 segundos')

    // Passo 3: Obter estado da thread
    logStep(3, 'Obter estado da thread via GET /api/studio/threads/[threadId]/state')
    
    const stateResult = await fetchAPI(`/api/studio/threads/${threadId}/state`)
    
    if (!stateResult.ok) {
      throw new Error(`Falha ao obter estado: ${JSON.stringify(stateResult.data)}`)
    }

    const messages = stateResult.data.values?.messages || []
    logSuccess(`Estado obtido com ${messages.length} mensagens`)
    
    if (messages.length > 0) {
      logInfo(`Última mensagem tipo: ${messages[messages.length - 1].type}`)
    }

    // Passo 4: Criar run (se necessário)
    logStep(4, 'Criar run via POST /api/studio/threads/[threadId]/runs')
    
    const runResult = await fetchAPI(`/api/studio/threads/${threadId}/runs`, {
      method: 'POST',
      body: JSON.stringify({
        assistant_id: ASSISTANT_ID,
        input: {
          messages: [
            {
              role: 'user',
              content: 'Teste de integração completo do Studio',
            },
          ],
        },
      }),
    })

    if (runResult.ok && runResult.data.run_id) {
      runId = runResult.data.run_id
      logSuccess(`Run criado: ${runId}`)
    } else {
      logWarning(`Run não criado ou resposta diferente: ${JSON.stringify(runResult.data)}`)
    }

    // Passo 5: Aguardar processamento do run
    if (runId) {
      logStep(5, 'Aguardar processamento do run')
      await sleep(3000)
      logSuccess('Aguardou 3 segundos')
    }

    // Passo 6: Listar runs
    logStep(6, 'Listar runs via GET /api/studio/threads/[threadId]/runs')
    
    const runsResult = await fetchAPI(`/api/studio/threads/${threadId}/runs`)
    
    if (!runsResult.ok) {
      throw new Error(`Falha ao listar runs: ${JSON.stringify(runsResult.data)}`)
    }

    const runs = runsResult.data.runs || []
    logSuccess(`Listou ${runs.length} runs`)

    // Passo 7: Obter detalhes do run (se houver)
    if (runs.length > 0) {
      const firstRun = runs[0]
      logStep(7, `Obter detalhes do run ${firstRun.run_id}`)
      
      const runDetailsResult = await fetchAPI(
        `/api/studio/threads/${threadId}/runs/${firstRun.run_id}`
      )

      if (runDetailsResult.ok) {
        logSuccess(`Detalhes obtidos: status=${runDetailsResult.data.status}`)
        logInfo(`Run ID: ${runDetailsResult.data.run_id}`)
        logInfo(`Assistant ID: ${runDetailsResult.data.assistant_id}`)
      } else {
        logWarning(`Não foi possível obter detalhes: ${JSON.stringify(runDetailsResult.data)}`)
      }
    } else {
      logWarning('Nenhum run encontrado para obter detalhes')
    }

    // Passo 8: Verificar comunicação com API de produção
    logStep(8, 'Verificar comunicação com API de produção')
    
    if (BASE_URL.includes('langgraph.app') || BASE_URL.includes('langsmith')) {
      logSuccess('Conectado à API de produção do LangGraph Deployment')
    } else {
      logWarning(`URL não parece ser de produção: ${BASE_URL}`)
    }

    // Resumo final
    log('\n' + '='.repeat(70), 'green')
    log('✅ TESTE DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO!', 'green')
    log('='.repeat(70) + '\n', 'green')

    logInfo(`Thread ID: ${threadId}`)
    if (runId) {
      logInfo(`Run ID: ${runId}`)
    }
    logInfo(`Total de mensagens: ${messages.length}`)
    logInfo(`Total de runs: ${runs.length}`)

    return true

  } catch (error) {
    logError(`Erro durante integração: ${error.message}`)
    console.error(error)
    
    log('\n' + '='.repeat(70), 'red')
    log('❌ TESTE DE INTEGRAÇÃO FALHOU', 'red')
    log('='.repeat(70) + '\n', 'red')

    if (threadId) {
      logInfo(`Thread ID criado: ${threadId}`)
    }

    return false
  }
}

// Executar teste
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-integration.js')) {
  testFullIntegration()
    .then(success => {
      process.exit(success ? 0 : 1)
    })
    .catch(error => {
      logError(`Erro fatal: ${error.message}`)
      console.error(error)
      process.exit(1)
    })
}

export { testFullIntegration }
