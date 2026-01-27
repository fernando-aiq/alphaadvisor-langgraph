"""
Testa conexão local como o LangSmith Studio faria
Simula as requisições que o Studio faz na conexão inicial
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8123"

print("=" * 70)
print("Testando Conexão Local como LangSmith Studio")
print("=" * 70)

# Teste 1: OPTIONS preflight (CORS) - /assistants
print("\n[1] Testando OPTIONS /assistants (preflight CORS)...")
try:
    response = requests.options(
        f"{BASE_URL}/assistants",
        headers={
            "Origin": "https://smith.langchain.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Headers CORS:")
    for header in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
        value = response.headers.get(header, 'NÃO ENCONTRADO')
        print(f"     {header}: {value}")
    if response.status_code == 200:
        print("   [OK] OPTIONS funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 2: GET /assistants (com Origin header)
print("\n[2] Testando GET /assistants (com Origin do Studio)...")
try:
    response = requests.get(
        f"{BASE_URL}/assistants",
        headers={
            "Origin": "https://smith.langchain.com",
            "Content-Type": "application/json"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')}")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] GET /assistants funcionando")
        print(f"   Assistentes encontrados: {len(data.get('assistants', []))}")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 3: GET / (endpoint raiz)
print("\n[3] Testando GET / (endpoint raiz)...")
try:
    response = requests.get(
        f"{BASE_URL}/",
        headers={
            "Origin": "https://smith.langchain.com"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] GET / funcionando")
        print(f"   Service: {data.get('service', 'N/A')}")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 4: POST /assistants/search
print("\n[4] Testando POST /assistants/search...")
try:
    response = requests.post(
        f"{BASE_URL}/assistants/search",
        json={"limit": 10, "offset": 0},
        headers={
            "Origin": "https://smith.langchain.com",
            "Content-Type": "application/json"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] POST /assistants/search funcionando")
        print(f"   Resultados: {len(data) if isinstance(data, list) else 0}")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 5: Verificar se o endpoint /health está acessível
print("\n[5] Testando GET /health...")
try:
    response = requests.get(
        f"{BASE_URL}/health",
        headers={
            "Origin": "https://smith.langchain.com"
        },
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   [OK] GET /health funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   [ERRO] {e}")

print("\n" + "=" * 70)
print("INSTRUÇÕES PARA O LANGGRAPH STUDIO")
print("=" * 70)
print("\n1. Base URL: http://127.0.0.1:8123")
print("\n2. Em Advanced Settings > Allowed Origins, adicione EXATAMENTE:")
print("   http://127.0.0.1:8123")
print("   http://localhost:8123")
print("\n3. NÃO use apenas 'localhost' ou '127.0.0.1' sem a porta!")
print("   O Studio precisa da URL completa com porta.")
print("\n4. Se ainda não funcionar, verifique:")
print("   - Se o servidor está rodando (python application.py)")
print("   - Se há erros no console do navegador (F12)")
print("   - Se o Chrome está bloqueando (tente desabilitar PNA)")
