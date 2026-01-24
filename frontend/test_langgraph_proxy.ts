/**
 * Script para testar o proxy do LangGraph Server via Vercel
 * Execute: npx tsx test_langgraph_proxy.ts
 */

const VERCEL_URL = process.env.VERCEL_URL || 'https://alphaadvisor.vercel.app'
const PROXY_BASE = `${VERCEL_URL}/api/langgraph`

async function testProxy() {
  console.log('='.repeat(70))
  console.log('Teste: Proxy LangGraph Server via Vercel')
  console.log('='.repeat(70))
  console.log(`URL do Vercel: ${VERCEL_URL}`)
  console.log(`Proxy Base: ${PROXY_BASE}`)
  console.log()

  // Teste 1: Health check
  console.log('[1] Testando GET /health...')
  try {
    const response = await fetch(`${PROXY_BASE}/health`)
    console.log(`   Status: ${response.status}`)
    if (response.ok) {
      const data = await response.json()
      console.log(`   Resposta: ${JSON.stringify(data, null, 2)}`)
      console.log('   ✅ Health check funcionando')
    } else {
      console.log(`   ❌ Erro: ${response.statusText}`)
    }
  } catch (e) {
    console.log(`   ❌ Erro: ${e}`)
  }

  // Teste 2: GET /assistants
  console.log('\n[2] Testando GET /assistants...')
  try {
    const response = await fetch(`${PROXY_BASE}/assistants`)
    console.log(`   Status: ${response.status}`)
    if (response.ok) {
      const data = await response.json()
      console.log(`   Resposta: ${JSON.stringify(data, null, 2)}`)
      console.log('   ✅ GET /assistants funcionando')
    } else {
      const text = await response.text()
      console.log(`   ❌ Erro: ${response.status} - ${text}`)
    }
  } catch (e) {
    console.log(`   ❌ Erro: ${e}`)
  }

  // Teste 3: POST /assistants/search
  console.log('\n[3] Testando POST /assistants/search...')
  try {
    const response = await fetch(`${PROXY_BASE}/assistants/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ limit: 10, offset: 0 }),
    })
    console.log(`   Status: ${response.status}`)
    if (response.ok) {
      const data = await response.json()
      console.log(`   Resposta: ${JSON.stringify(data, null, 2)}`)
      console.log('   ✅ POST /assistants/search funcionando')
    } else {
      const text = await response.text()
      console.log(`   ❌ Erro: ${response.status} - ${text}`)
    }
  } catch (e) {
    console.log(`   ❌ Erro: ${e}`)
  }

  // Teste 4: OPTIONS (CORS preflight)
  console.log('\n[4] Testando OPTIONS (CORS preflight)...')
  try {
    const response = await fetch(`${PROXY_BASE}/assistants/search`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'https://smith.langchain.com',
        'Access-Control-Request-Method': 'POST',
      },
    })
    console.log(`   Status: ${response.status}`)
    console.log(`   CORS Headers:`)
    console.log(`     Access-Control-Allow-Origin: ${response.headers.get('Access-Control-Allow-Origin')}`)
    console.log(`     Access-Control-Allow-Methods: ${response.headers.get('Access-Control-Allow-Methods')}`)
    if (response.ok) {
      console.log('   ✅ OPTIONS funcionando')
    } else {
      console.log(`   ❌ Erro: ${response.statusText}`)
    }
  } catch (e) {
    console.log(`   ❌ Erro: ${e}`)
  }

  console.log('\n' + '='.repeat(70))
  console.log('Testes concluídos!')
  console.log('='.repeat(70))
  console.log('\nPara usar no LangSmith Studio:')
  console.log(`  Base URL: ${PROXY_BASE}`)
  console.log(`  Allowed Origins: ${VERCEL_URL}`)
}

// Executar se chamado diretamente
if (require.main === module) {
  testProxy().catch(console.error)
}

export { testProxy }
