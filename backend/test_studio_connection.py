"""
Testa conexão como o LangSmith Studio faria
Simula as requisições que o Studio faz na conexão inicial
"""
import requests
import json

BASE_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"

print("=" * 70)
print("Testando Conexão como LangSmith Studio")
print("=" * 70)

# Teste 1: OPTIONS preflight (CORS)
print("\n[1] Testando OPTIONS (preflight CORS)...")
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
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')}")
        print("   [OK] GET /assistants funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 3: POST /assistants/search (formato LangGraph Server)
print("\n[3] Testando POST /assistants/search...")
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
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("   [OK] POST /assistants/search funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 4: GET / (root endpoint)
print("\n[4] Testando GET / (root)...")
try:
    response = requests.get(
        f"{BASE_URL}/",
        headers={"Origin": "https://smith.langchain.com"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("   [OK] GET / funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] {e}")

# Teste 5: GET /docs
print("\n[5] Testando GET /docs...")
try:
    response = requests.get(
        f"{BASE_URL}/docs",
        headers={"Origin": "https://smith.langchain.com"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [OK] GET /docs funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] {e}")

print("\n" + "=" * 70)
print("Testes concluídos!")
print("=" * 70)
print(f"\nSe todos os testes passaram, o problema pode ser:")
print("1. HTTP vs HTTPS (Studio prefere HTTPS)")
print("2. Allowed Origins não configurado corretamente no Studio")
print("3. Browser bloqueando conexão HTTP de site HTTPS")
