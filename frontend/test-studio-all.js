/**
 * Script Master - Executa Todos os Testes do Studio
 * 
 * Execute com: node test-studio-all.js
 * 
 * Requisitos:
 * - Servidor Next.js rodando (npm run dev) para testes de API
 * - Variáveis de ambiente configuradas
 */

import { runAllTests as testAPI } from './test-studio-api-routes.js'
import { runAllTests as testClient } from './test-studio-client.js'
import { runAllTests as testComponents } from './test-studio-components.js'
import { testFullIntegration } from './test-studio-integration.js'

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

async function runAllTests() {
  log('\n' + '='.repeat(70), 'magenta')
  log('🚀 EXECUTANDO TODOS OS TESTES EXAUSTIVOS DO STUDIO', 'magenta')
  log('='.repeat(70) + '\n', 'magenta')

  const results = {
    apiRoutes: false,
    client: false,
    components: false,
    integration: false,
  }

  try {
    // Teste 1: API Routes
    log('\n📡 TESTE 1: API Routes', 'cyan')
    log('─'.repeat(70), 'cyan')
    results.apiRoutes = await testAPI()

    // Teste 2: Cliente LangSmith
    log('\n📦 TESTE 2: Cliente LangSmith', 'cyan')
    log('─'.repeat(70), 'cyan')
    results.client = await testClient()

    // Teste 3: Componentes React
    log('\n⚛️  TESTE 3: Componentes React', 'cyan')
    log('─'.repeat(70), 'cyan')
    results.components = await testComponents()

    // Teste 4: Integração Completa
    log('\n🔗 TESTE 4: Integração Completa', 'cyan')
    log('─'.repeat(70), 'cyan')
    results.integration = await testFullIntegration()

  } catch (error) {
    log(`\n❌ Erro fatal durante execução dos testes: ${error.message}`, 'red')
    console.error(error)
  }

  // Resumo Final
  log('\n' + '='.repeat(70), 'magenta')
  log('📊 RESUMO FINAL DE TODOS OS TESTES', 'magenta')
  log('='.repeat(70) + '\n', 'magenta')

  const totalTests = Object.keys(results).length
  const passedTests = Object.values(results).filter(r => r === true).length

  log(`Total de suites de teste: ${totalTests}`)
  log(`Passou completamente: ${passedTests}`, passedTests === totalTests ? 'green' : 'yellow')
  log(`Falhou ou parcial: ${totalTests - passedTests}`, passedTests === totalTests ? 'green' : 'red')

  log('\nDetalhes por suite:', 'blue')
  Object.entries(results).forEach(([suite, result]) => {
    const status = result ? '✅' : '❌'
    const name = {
      apiRoutes: 'API Routes',
      client: 'Cliente LangSmith',
      components: 'Componentes React',
      integration: 'Integração Completa',
    }[suite] || suite

    log(`${status} ${name}: ${result ? 'PASSOU' : 'FALHOU'}`)
  })

  log('\n' + '='.repeat(70) + '\n', 'magenta')

  if (passedTests === totalTests) {
    log('🎉 TODOS OS TESTES PASSARAM!', 'green')
    return true
  } else {
    log('⚠️  ALGUNS TESTES FALHARAM. Verifique os logs acima.', 'yellow')
    return false
  }
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-all.js')) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1)
    })
    .catch(error => {
      log(`Erro fatal: ${error.message}`, 'red')
      console.error(error)
      process.exit(1)
    })
}

export { runAllTests }
