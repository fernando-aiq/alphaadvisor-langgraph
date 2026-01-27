"""
Script para testar e investigar o erro 500 em POST /assistants/search
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_assistants_search():
    """Testa o endpoint POST /assistants/search"""
    print("=" * 70)
    print("Testando POST /assistants/search")
    print("=" * 70)
    
    try:
        # Teste 1: Requisição básica
        print("\n[1] Testando requisição básica...")
        response = requests.post(
            f"{BASE_URL}/assistants/search",
            json={"limit": 10, "offset": 0},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Resposta: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}")
        else:
            print(f"   [ERRO] Status {response.status_code}")
            print(f"   Resposta: {response.text[:500]}")
            return False
        
        # Teste 2: Com Origin header (como Studio faria)
        print("\n[2] Testando com Origin header (como LangSmith Studio)...")
        response = requests.post(
            f"{BASE_URL}/assistants/search",
            json={"limit": 10, "offset": 0},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://smith.langchain.com"
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   [OK] Funcionando com Origin header")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
            return False
        
        # Teste 3: OPTIONS preflight
        print("\n[3] Testando OPTIONS (preflight CORS)...")
        response = requests.options(
            f"{BASE_URL}/assistants/search",
            headers={
                "Origin": "https://smith.langchain.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        print(f"   CORS Headers: {cors_headers}")
        if response.status_code == 200:
            print(f"   [OK] OPTIONS funcionando")
        else:
            print(f"   [ERRO] Status {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n[ERRO] Servidor não está rodando em {BASE_URL}")
        print("Inicie o servidor com: cd backend && python application.py")
        return False
    except Exception as e:
        print(f"\n[ERRO] Exceção: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_assistants_search()
    if success:
        print("\n" + "=" * 70)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        sys.exit(1)
