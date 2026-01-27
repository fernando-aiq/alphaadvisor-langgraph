"""
Script simples para testar endpoints LangGraph após deploy
"""
import requests
import json

BASE_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"

print("=" * 60)
print("Testando Endpoints LangGraph após Deploy")
print("=" * 60)

# Teste 1: Health check
print("\n[1] Testando /langgraph/health...")
try:
    response = requests.get(f"{BASE_URL}/langgraph/health", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print("   [OK] Health check OK")
    else:
        print(f"   ❌ Erro: {response.text}")
except Exception as e:
    print(f"   ❌ Erro ao conectar: {e}")

# Teste 2: List assistants
print("\n[2] Testando /langgraph/assistants...")
try:
    response = requests.get(f"{BASE_URL}/langgraph/assistants", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        assistants = data.get("assistants", [])
        if assistants:
            print(f"   [OK] Encontrados {len(assistants)} assistente(s)")
        else:
            print("   [AVISO] Nenhum assistente encontrado")
    else:
        print(f"   ❌ Erro: {response.text}")
except Exception as e:
    print(f"   ❌ Erro ao conectar: {e}")

# Teste 3: Health check geral da API
print("\n[3] Testando /api/health (endpoint geral)...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print("   [OK] API geral OK")
    else:
        print(f"   ❌ Erro: {response.text}")
except Exception as e:
    print(f"   ❌ Erro ao conectar: {e}")

print("\n" + "=" * 60)
print("Testes concluídos!")
print("=" * 60)
print(f"\nURL para conectar no LangSmith Studio:")
print(f"{BASE_URL}")
