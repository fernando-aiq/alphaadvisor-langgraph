#!/usr/bin/env node
/**
 * Script de Execução Rápida dos Testes
 * 
 * Executa todos os testes do Studio de forma simplificada
 * 
 * Uso: node executar-testes.js [tipo]
 * 
 * Tipos disponíveis:
 * - all: Todos os testes (padrão)
 * - api: Apenas testes de API routes
 * - client: Apenas testes do cliente
 * - components: Apenas testes de componentes
 * - integration: Apenas teste de integração
 * - navigation: Apenas testes de navegação
 * - production: Apenas teste de produção
 */

import { runAllTests as testAPI } from './test-studio-api-routes.js'
import { runAllTests as testClient } from './test-studio-client.js'
import { runAllTests as testComponents } from './test-studio-components.js'
import { testFullIntegration } from './test-studio-integration.js'
import { runAllTests as testNavigation } from './test-studio-navigation.js'
import { runAllTests as testProduction } from './test-studio-production-api.js'

const testType = process.argv[2] || 'all'

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

async function main() {
  log('\n' + '='.repeat(70), 'magenta')
  log('🧪 EXECUTANDO TESTES DO STUDIO', 'magenta')
  log('='.repeat(70) + '\n', 'magenta')

  log(`Tipo de teste: ${testType}\n`, 'cyan')

  let success = false

  try {
    switch (testType) {
      case 'api':
        success = await testAPI()
        break
      case 'client':
        success = await testClient()
        break
      case 'components':
        success = await testComponents()
        break
      case 'integration':
        success = await testFullIntegration()
        break
      case 'navigation':
        success = await testNavigation()
        break
      case 'production':
        success = await testProduction()
        break
      case 'all':
      default:
        // Executar todos
        const results = {
          api: await testAPI(),
          client: await testClient(),
          components: await testComponents(),
          integration: await testFullIntegration(),
          navigation: await testNavigation(),
          production: await testProduction(),
        }
        success = Object.values(results).every(r => r === true)
        break
    }

    log('\n' + '='.repeat(70), 'magenta')
    if (success) {
      log('✅ TESTES CONCLUÍDOS COM SUCESSO!', 'green')
    } else {
      log('⚠️  ALGUNS TESTES FALHARAM', 'yellow')
    }
    log('='.repeat(70) + '\n', 'magenta')

    process.exit(success ? 0 : 1)
  } catch (error) {
    log(`\n❌ Erro fatal: ${error.message}`, 'red')
    console.error(error)
    process.exit(1)
  }
}

main()
