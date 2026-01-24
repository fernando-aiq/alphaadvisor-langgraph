// Script para testar endpoints do proxy
const https = require('https');

const BASE_URL = 'https://alphaadvisor-i8noqf1qr-aiqgen.vercel.app';

function testEndpoint(path, method = 'GET') {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Origin': 'https://smith.langchain.com',
        'Accept': 'application/json',
      }
    };

    console.log(`\n[TEST] ${method} ${path}`);
    console.log(`[TEST] URL: ${url.toString()}`);
    
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        const corsHeaders = {
          'Access-Control-Allow-Origin': res.headers['access-control-allow-origin'],
          'Access-Control-Allow-Methods': res.headers['access-control-allow-methods'],
          'Access-Control-Allow-Headers': res.headers['access-control-allow-headers'],
          'Access-Control-Allow-Credentials': res.headers['access-control-allow-credentials'],
        };
        
        console.log(`[TEST] Status: ${res.statusCode} ${res.statusMessage}`);
        console.log(`[TEST] CORS Headers:`, corsHeaders);
        
        if (res.statusCode === 200) {
          try {
            const json = JSON.parse(data);
            console.log(`[TEST] Response:`, JSON.stringify(json, null, 2));
          } catch (e) {
            console.log(`[TEST] Response (text):`, data.substring(0, 200));
          }
        } else {
          console.log(`[TEST] Error Response:`, data.substring(0, 200));
        }
        
        resolve({
          status: res.statusCode,
          headers: res.headers,
          corsHeaders,
          body: data
        });
      });
    });
    
    req.on('error', (error) => {
      console.error(`[TEST] Request error:`, error.message);
      reject(error);
    });
    
    req.end();
  });
}

async function runTests() {
  console.log('='.repeat(60));
  console.log('TESTANDO ENDPOINTS DO PROXY');
  console.log('='.repeat(60));
  
  try {
    // Teste 1: /info (via middleware)
    await testEndpoint('/info');
    
    // Teste 2: /api/info (via rota API)
    await testEndpoint('/api/info');
    
    // Teste 3: /api/langgraph/info (via proxy langgraph)
    await testEndpoint('/api/langgraph/info');
    
    // Teste 4: OPTIONS preflight
    await testEndpoint('/info', 'OPTIONS');
    
    console.log('\n' + '='.repeat(60));
    console.log('TESTES CONCLUÍDOS');
    console.log('='.repeat(60));
  } catch (error) {
    console.error('Erro durante testes:', error);
  }
}

runTests();
