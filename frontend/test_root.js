// Testar se a raiz funciona
const https = require('https');

const BASE_URL = 'https://alphaadvisor-i8noqf1qr-aiqgen.vercel.app';

function testEndpoint(path) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    
    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0',
      }
    };

    console.log(`\n[TEST] GET ${path}`);
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        console.log(`[TEST] Status: ${res.statusCode}`);
        console.log(`[TEST] Headers:`, res.headers);
        console.log(`[TEST] Body (first 500 chars):`, data.substring(0, 500));
        resolve({ status: res.statusCode, body: data });
      });
    });
    
    req.on('error', reject);
    req.end();
  });
}

testEndpoint('/').then(() => {
  console.log('\nTeste concluído');
}).catch(console.error);
