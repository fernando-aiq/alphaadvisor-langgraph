/**
 * Testes de Componentes React - Studio
 * 
 * Valida estrutura e lógica dos componentes sem renderização real
 * 
 * Execute com: node test-studio-components.js
 */

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

// Verificar se arquivos existem e têm estrutura correta
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function checkFileExists(filePath, description) {
  const fullPath = path.join(__dirname, filePath)
  
  if (fs.existsSync(fullPath)) {
    logSuccess(`${description} existe: ${filePath}`)
    return true
  } else {
    logError(`${description} não encontrado: ${filePath}`)
    return false
  }
}

function checkFileContent(filePath, requiredExports, requiredImports = []) {
  const fullPath = path.join(__dirname, filePath)
  
  if (!fs.existsSync(fullPath)) {
    return false
  }

  const content = fs.readFileSync(fullPath, 'utf-8')
  const errors = []

  // Verificar exports
  requiredExports.forEach(exportName => {
    if (!content.includes(`export ${exportName}`) && 
        !content.includes(`export default ${exportName}`) &&
        !content.includes(`export function ${exportName}`) &&
        !content.includes(`export const ${exportName}`)) {
      errors.push(`Export '${exportName}' não encontrado`)
    }
  })

  // Verificar imports
  requiredImports.forEach(importName => {
    if (!content.includes(`import`) || !content.includes(importName)) {
      // Não é crítico, apenas avisar
    }
  })

  if (errors.length === 0) {
    logSuccess(`Estrutura de ${filePath} está correta`)
    return true
  } else {
    errors.forEach(err => logError(`${filePath}: ${err}`))
    return false
  }
}

function checkReactComponent(filePath, componentName) {
  const fullPath = path.join(__dirname, filePath)
  
  if (!fs.existsSync(fullPath)) {
    return false
  }

  const content = fs.readFileSync(fullPath, 'utf-8')
  const checks = {
    hasClientDirective: content.includes("'use client'"),
    hasComponent: content.includes(`function ${componentName}`) || 
                  content.includes(`const ${componentName}`) ||
                  content.includes(`export default function ${componentName}`),
    hasReactImport: content.includes('from "react"') || content.includes("from 'react'"),
    hasHooks: content.includes('useState') || content.includes('useEffect') || content.includes('useRouter'),
  }

  const allPassed = Object.values(checks).every(v => v)
  
  if (allPassed) {
    logSuccess(`Componente ${componentName} tem estrutura correta`)
    Object.entries(checks).forEach(([check, passed]) => {
      if (passed) {
        logInfo(`  ✓ ${check}`)
      }
    })
    return true
  } else {
    logError(`Componente ${componentName} tem problemas de estrutura`)
    Object.entries(checks).forEach(([check, passed]) => {
      if (!passed) {
        logError(`  ✗ ${check}`)
      } else {
        logInfo(`  ✓ ${check}`)
      }
    })
    return false
  }
}

// Testes
async function testRunsListComponent() {
  logTest('Componente RunsList')
  
  const exists = checkFileExists(
    'app/components/studio/RunsList.tsx',
    'RunsList.tsx'
  )

  if (!exists) return false

  const structure = checkReactComponent(
    'app/components/studio/RunsList.tsx',
    'RunsList'
  )

  // Verificar funcionalidades específicas
  const fullPath = path.join(__dirname, 'app/components/studio/RunsList.tsx')
  const content = fs.readFileSync(fullPath, 'utf-8')

  const features = {
    hasThreadIdInput: content.includes('threadIdInput'),
    hasRecentThreads: content.includes('recentThreads'),
    hasLocalStorage: content.includes('localStorage'),
    hasCreateThread: content.includes('createThread') || content.includes('handleCreateThread'),
    hasViewThread: content.includes('handleViewThread') || content.includes('viewThread'),
    hasRouter: content.includes('useRouter'),
    hasLangSmithClient: content.includes('langSmithClient'),
  }

  const allFeatures = Object.values(features).every(v => v)
  
  if (allFeatures) {
    logSuccess('RunsList tem todas as funcionalidades esperadas')
    Object.entries(features).forEach(([feature, present]) => {
      if (present) logInfo(`  ✓ ${feature}`)
    })
  } else {
    logWarning('RunsList pode estar faltando algumas funcionalidades')
    Object.entries(features).forEach(([feature, present]) => {
      if (!present) logWarning(`  ⚠ ${feature} não encontrado`)
    })
  }

  return structure
}

async function testRunDetailsComponent() {
  logTest('Componente RunDetails')
  
  const exists = checkFileExists(
    'app/components/studio/RunDetails.tsx',
    'RunDetails.tsx'
  )

  if (!exists) return false

  const structure = checkReactComponent(
    'app/components/studio/RunDetails.tsx',
    'RunDetails'
  )

  // Verificar funcionalidades específicas
  const fullPath = path.join(__dirname, 'app/components/studio/RunDetails.tsx')
  const content = fs.readFileSync(fullPath, 'utf-8')

  const features = {
    hasThreadIdProp: content.includes('threadId'),
    hasThreadState: content.includes('threadState') || content.includes('getThreadState'),
    hasRuns: content.includes('runs') || content.includes('listRuns'),
    hasLoading: content.includes('loading'),
    hasError: content.includes('error'),
    hasRefresh: content.includes('refresh') || content.includes('loadData'),
    hasMessages: content.includes('messages'),
  }

  const allFeatures = Object.values(features).every(v => v)
  
  if (allFeatures) {
    logSuccess('RunDetails tem todas as funcionalidades esperadas')
    Object.entries(features).forEach(([feature, present]) => {
      if (present) logInfo(`  ✓ ${feature}`)
    })
  } else {
    logWarning('RunDetails pode estar faltando algumas funcionalidades')
    Object.entries(features).forEach(([feature, present]) => {
      if (!present) logWarning(`  ⚠ ${feature} não encontrado`)
    })
  }

  return structure
}

async function testLangSmithClient() {
  logTest('Cliente LangSmith')
  
  const exists = checkFileExists(
    'app/lib/studio/langsmith-client.ts',
    'langsmith-client.ts'
  )

  if (!exists) return false

  const fullPath = path.join(__dirname, 'app/lib/studio/langsmith-client.ts')
  const content = fs.readFileSync(fullPath, 'utf-8')

  const methods = [
    'listThreads',
    'getThreadState',
    'listRuns',
    'getRunDetails',
    'createThread',
    'createRun',
  ]

  const allMethodsPresent = methods.every(method => content.includes(method))

  if (allMethodsPresent) {
    logSuccess('Cliente tem todos os métodos esperados')
    methods.forEach(method => logInfo(`  ✓ ${method}()`))
  } else {
    logError('Cliente está faltando métodos')
    methods.forEach(method => {
      if (!content.includes(method)) {
        logError(`  ✗ ${method}() não encontrado`)
      } else {
        logInfo(`  ✓ ${method}()`)
      }
    })
  }

  // Verificar exports
  const hasExport = content.includes('export const langSmithClient') || 
                     content.includes('export { langSmithClient }')

  if (hasExport) {
    logSuccess('Cliente exportado corretamente')
  } else {
    logError('Cliente não está exportado')
  }

  return allMethodsPresent && hasExport
}

async function testPages() {
  logTest('Páginas do Studio')
  
  const pages = [
    { path: 'app/studio/page.tsx', name: 'Página principal' },
    { path: 'app/studio/runs/page.tsx', name: 'Página de runs' },
    { path: 'app/studio/runs/[threadId]/page.tsx', name: 'Página de detalhes' },
  ]

  let allExist = true

  pages.forEach(page => {
    const exists = checkFileExists(page.path, page.name)
    if (!exists) allExist = false
  })

  return allExist
}

async function testSidebarIntegration() {
  logTest('Integração no Sidebar')
  
  const sidebarPath = path.join(__dirname, 'app/components/Sidebar.tsx')
  
  if (!fs.existsSync(sidebarPath)) {
    logError('Sidebar.tsx não encontrado')
    return false
  }

  const content = fs.readFileSync(sidebarPath, 'utf-8')

  const checks = {
    hasStudioLink: content.includes('/studio') || content.includes("href: '/studio'"),
    hasFiCode: content.includes('FiCode'),
    hasStudioLabel: content.includes('Studio') || content.includes('label: \'Studio\''),
  }

  const allPassed = Object.values(checks).every(v => v)

  if (allPassed) {
    logSuccess('Studio integrado no Sidebar')
    Object.entries(checks).forEach(([check, passed]) => {
      if (passed) logInfo(`  ✓ ${check}`)
    })
  } else {
    logError('Studio não está integrado no Sidebar')
    Object.entries(checks).forEach(([check, passed]) => {
      if (!passed) logError(`  ✗ ${check}`)
    })
  }

  return allPassed
}

// Executar todos os testes
async function runAllTests() {
  log('\n' + '='.repeat(60), 'blue')
  log('🚀 INICIANDO TESTES DE COMPONENTES - STUDIO', 'blue')
  log('='.repeat(60) + '\n', 'blue')

  const results = {
    runsList: false,
    runDetails: false,
    langSmithClient: false,
    pages: false,
    sidebar: false,
  }

  results.runsList = await testRunsListComponent()
  results.runDetails = await testRunDetailsComponent()
  results.langSmithClient = await testLangSmithClient()
  results.pages = await testPages()
  results.sidebar = await testSidebarIntegration()

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
    log(`${status} ${test}: ${result ? 'OK' : 'FALHOU'}`)
  })

  log('\n' + '='.repeat(60) + '\n', 'blue')

  return passedTests === totalTests
}

// Executar se chamado diretamente
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('test-studio-components.js')) {
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
