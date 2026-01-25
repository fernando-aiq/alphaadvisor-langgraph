/**
 * Teste de Navegação e Rotas - Studio
 * 
 * Valida que todas as rotas estão configuradas corretamente
 * 
 * Execute com: node test-studio-navigation.js
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

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

function checkRouteExists(routePath, description) {
  const fullPath = path.join(__dirname, routePath)
  
  if (fs.existsSync(fullPath)) {
    logSuccess(`${description} existe: ${routePath}`)
    return true
  } else {
    logError(`${description} não encontrado: ${routePath}`)
    return false
  }
}

function checkRouteContent(routePath, requiredContent) {
  const fullPath = path.join(__dirname, routePath)
  
  if (!fs.existsSync(fullPath)) {
    return false
  }

  const content = fs.readFileSync(fullPath, 'utf-8')
  const missing = []

  requiredContent.forEach(item => {
    if (!content.includes(item)) {
      missing.push(item)
    }
  })

  if (missing.length === 0) {
    logSuccess(`Conteúdo de ${routePath} está correto`)
    return true
  } else {
    logError(`${routePath} está faltando: ${missing.join(', ')}`)
    return false
  }
}

async function testFrontendRoutes() {
  logTest('Rotas do Frontend (/studio/*)')
  
  const routes = [
    {
      path: 'app/studio/page.tsx',
      name: 'Página principal /studio',
      required: ['export default', 'Studio'],
    },
    {
      path: 'app/studio/runs/page.tsx',
      name: 'Página de runs /studio/runs',
      required: ['RunsList', 'export default'],
    },
    {
      path: 'app/studio/runs/[threadId]/page.tsx',
      name: 'Página de detalhes /studio/runs/[threadId]',
      required: ['RunDetails', 'threadId', 'export default'],
    },
  ]

  let allExist = true
  let allContent = true

  routes.forEach(route => {
    const exists = checkRouteExists(route.path, route.name)
    if (!exists) allExist = false

    if (exists) {
      const content = checkRouteContent(route.path, route.required)
      if (!content) allContent = false
    }
  })

  return allExist && allContent
}

async function testAPIRoutes() {
  logTest('Rotas da API (/api/studio/*)')
  
  const routes = [
    {
      path: 'app/api/studio/threads/route.ts',
      name: 'API /api/studio/threads',
      required: ['GET', 'POST', 'getLangSmithConfig'],
    },
    {
      path: 'app/api/studio/threads/[threadId]/state/route.ts',
      name: 'API /api/studio/threads/[threadId]/state',
      required: ['GET', 'getLangSmithConfig'],
    },
    {
      path: 'app/api/studio/threads/[threadId]/runs/route.ts',
      name: 'API /api/studio/threads/[threadId]/runs',
      required: ['GET', 'POST', 'getLangSmithConfig'],
    },
    {
      path: 'app/api/studio/threads/[threadId]/runs/[runId]/route.ts',
      name: 'API /api/studio/threads/[threadId]/runs/[runId]',
      required: ['GET', 'getLangSmithConfig'],
    },
  ]

  let allExist = true
  let allContent = true

  routes.forEach(route => {
    const exists = checkRouteExists(route.path, route.name)
    if (!exists) allExist = false

    if (exists) {
      const content = checkRouteContent(route.path, route.required)
      if (!content) allContent = false
    }
  })

  return allExist && allContent
}

async function testSidebarNavigation() {
  logTest('Navegação no Sidebar')
  
  const sidebarPath = path.join(__dirname, '..', 'app/components/Sidebar.tsx')
  
  if (!fs.existsSync(sidebarPath)) {
    logError('Sidebar.tsx não encontrado')
    return false
  }

  const content = fs.readFileSync(sidebarPath, 'utf-8')

  const checks = {
    hasStudioRoute: content.includes("href: '/studio'") || content.includes("'/studio'"),
    hasStudioLabel: content.includes("label: 'Studio'") || content.includes('label: "Studio"'),
    hasFiCodeImport: content.includes('FiCode'),
    hasStudioInMenu: content.includes('Studio'),
  }

  const allPassed = Object.values(checks).every(v => v)

  if (allPassed) {
    logSuccess('Studio está integrado no Sidebar corretamente')
    Object.entries(checks).forEach(([check, passed]) => {
      if (passed) logInfo(`  ✓ ${check}`)
    })
  } else {
    logError('Studio não está completamente integrado no Sidebar')
    Object.entries(checks).forEach(([check, passed]) => {
      if (!passed) logError(`  ✗ ${check}`)
    })
  }

  return allPassed
}

async function testClientLibrary() {
  logTest('Biblioteca do Cliente')
  
  const clientPath = path.join(__dirname, 'app/lib/studio/langsmith-client.ts')
  
  if (!fs.existsSync(clientPath)) {
    logError('langsmith-client.ts não encontrado')
    return false
  }

  const content = fs.readFileSync(clientPath, 'utf-8')

  const requiredMethods = [
    'listThreads',
    'getThreadState',
    'listRuns',
    'getRunDetails',
    'createThread',
    'createRun',
  ]

  const allMethodsPresent = requiredMethods.every(method => content.includes(method))

  if (allMethodsPresent) {
    logSuccess('Cliente tem todos os métodos necessários')
    requiredMethods.forEach(method => logInfo(`  ✓ ${method}()`))
  } else {
    logError('Cliente está faltando métodos')
    requiredMethods.forEach(method => {
      if (!content.includes(method)) {
        logError(`  ✗ ${method}() não encontrado`)
      }
    })
  }

  return allMethodsPresent
}

async function testComponentsStructure() {
  logTest('Estrutura dos Componentes')
  
  const components = [
    {
      path: 'app/components/studio/RunsList.tsx',
      name: 'RunsList',
      required: ['export default', 'RunsList', 'useState', 'langSmithClient'],
    },
    {
      path: 'app/components/studio/RunDetails.tsx',
      name: 'RunDetails',
      required: ['export default', 'RunDetails', 'threadId', 'useState', 'langSmithClient'],
    },
  ]

  let allExist = true
  let allContent = true

  components.forEach(component => {
    const exists = checkRouteExists(component.path, component.name)
    if (!exists) allExist = false

    if (exists) {
      const content = checkRouteContent(component.path, component.required)
      if (!content) allContent = false
    }
  })

  return allExist && allContent
}

// Executar todos os testes
async function runAllTests() {
  log('\n' + '='.repeat(60), 'blue')
  log('🚀 INICIANDO TESTES DE NAVEGAÇÃO E ROTAS - STUDIO', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  const results = {
    frontendRoutes: false,
    apiRoutes: false,
    sidebar: false,
    client: false,
    components: false,
  }

  results.frontendRoutes = await testFrontendRoutes()
  results.apiRoutes = await testAPIRoutes()
  results.sidebar = await testSidebarNavigation()
  results.client = await testClientLibrary()
  results.components = await testComponentsStructure()

  // Resumo
  log('\n' + '='.repeat(60), 'blue')
  log('📊 RESUMO DOS TESTES', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  const totalTests = Object.keys(results).length
  const passedTests = Object.values(results).filter(r => r === true).length

  log(`Total de testes: ${totalTests}`)
  log(`Passou: ${passedTests}`, passedTests === totalTests ? 'green' : 'yellow')
  log(`Falhou: ${totalTests - passedTests}`, passedTests === totalTests ? 'green' : 'red')

  log('\nDetalhes:', 'blue')
  Object.entries(results).forEach(([test, result]) => {
    const status = result ? '✅' : '❌'
    const name = {
      frontendRoutes: 'Rotas do Frontend',
      apiRoutes: 'Rotas da API',
      sidebar: 'Navegação no Sidebar',
      client: 'Biblioteca do Cliente',
      components: 'Estrutura dos Componentes',
    }[test] || test

    log(`${status} ${name}: ${result ? 'OK' : 'FALHOU'}`)
  })

  log('\n' + '='.repeat(60) + '\n', 'blue')

  return passedTests === totalTests
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-navigation.js')) {
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
