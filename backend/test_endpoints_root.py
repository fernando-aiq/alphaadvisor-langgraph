"""
Testa endpoints na raiz (compatibilidade com LangSmith Studio)
"""
import requests
import json

BASE_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"

print("=" * 60)
print("Testando Endpoints na RAIZ (compatibilidade LangSmith Studio)")
print("=" * 60)

# Teste 1: /assistants (raiz)
print("\n[1] Testando GET /assistants (raiz)...")
try:
    response = requests.get(f"{BASE_URL}/assistants", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        assistants = data.get("assistants", [])
        if assistants:
            print(f"   [OK] Encontrados {len(assistants)} assistente(s) na raiz")
        else:
            print("   [AVISO] Nenhum assistente encontrado")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] Erro ao conectar: {e}")

# Teste 2: /threads (raiz) - GET
print("\n[2] Testando GET /threads (raiz)...")
try:
    response = requests.get(f"{BASE_URL}/threads", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("   [OK] GET /threads funcionando")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] Erro ao conectar: {e}")

# Teste 3: /threads (raiz) - POST
print("\n[3] Testando POST /threads (raiz)...")
try:
    payload = {
        "assistant_id": "agent",
        "input": {
            "messages": [
                {"role": "user", "content": "ola"}
            ]
        }
    }
    response = requests.post(
        f"{BASE_URL}/threads",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        thread_id = data.get("thread_id")
        print(f"   Thread ID: {thread_id}")
        print(f"   Messages: {len(data.get('values', {}).get('messages', []))} mensagens")
        print("   [OK] POST /threads funcionando na raiz")
    else:
        print(f"   [ERRO] Status {response.status_code}: {response.text}")
except Exception as e:
    print(f"   [ERRO] Erro ao conectar: {e}")

print("\n" + "=" * 60)
print("Testes concluidos!")
print("=" * 60)
print(f"\nSe todos os testes passaram, o LangSmith Studio deve conseguir conectar.")
print(f"URL: {BASE_URL}")
