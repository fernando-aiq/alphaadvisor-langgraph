"""
Script para testar LangGraph Server na porta 8555
Verifica todos os endpoints necessários para conexão com LangSmith Studio
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8555"

def test_endpoint(method, path, data=None, headers=None, description=""):
    """Testa um endpoint e retorna o resultado"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers or {}, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data or {}, headers=headers or {}, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers or {}, timeout=10)
        else:
            return False, f"Método {method} não suportado"
        
        return response.status_code == 200, {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:200] if response.text else ""
        }
    except requests.exceptions.ConnectionError:
        return False, "Servidor não está rodando"
    except Exception as e:
        return False, str(e)

def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("Teste LangGraph Server - Porta 8555")
    print("=" * 70)
    
    results = {}
    
    # Teste 1: GET / (endpoint raiz)
    print("\n[1] Testando GET / (endpoint raiz)...")
    success, info = test_endpoint("GET", "/", description="Endpoint raiz")
    results["GET /"] = success
    if success:
        print(f"   [OK] Status {info['status']}")
    else:
        print(f"   [ERRO] {info}")
    
    # Teste 2: POST /assistants/search
    print("\n[2] Testando POST /assistants/search...")
    success, info = test_endpoint(
        "POST", 
        "/assistants/search",
        data={"limit": 10, "offset": 0},
        headers={"Content-Type": "application/json"},
        description="Busca assistentes"
    )
    results["POST /assistants/search"] = success
    if success:
        print(f"   [OK] Status {info['status']}")
        try:
            data = json.loads(info['body'])
            print(f"   Assistentes encontrados: {len(data) if isinstance(data, list) else 0}")
        except:
            pass
    else:
        print(f"   [ERRO] {info}")
    
    # Teste 3: GET /assistants
    print("\n[3] Testando GET /assistants...")
    success, info = test_endpoint("GET", "/assistants", description="Lista assistentes")
    results["GET /assistants"] = success
    if success:
        print(f"   [OK] Status {info['status']}")
    else:
        print(f"   [ERRO] {info}")
    
    # Teste 4: GET /threads
    print("\n[4] Testando GET /threads...")
    success, info = test_endpoint("GET", "/threads", description="Lista threads")
    results["GET /threads"] = success
    if success:
        print(f"   [OK] Status {info['status']}")
    else:
        print(f"   [ERRO] {info}")
    
    # Teste 5: OPTIONS /assistants (CORS preflight)
    print("\n[5] Testando OPTIONS /assistants (CORS preflight)...")
    success, info = test_endpoint(
        "OPTIONS",
        "/assistants",
        headers={
            "Origin": "https://smith.langchain.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        },
        description="CORS preflight"
    )
    results["OPTIONS /assistants"] = success
    if success:
        cors_origin = info['headers'].get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
        cors_methods = info['headers'].get('Access-Control-Allow-Methods', 'NÃO ENCONTRADO')
        print(f"   [OK] Status {info['status']}")
        print(f"   Access-Control-Allow-Origin: {cors_origin}")
        print(f"   Access-Control-Allow-Methods: {cors_methods}")
    else:
        print(f"   [ERRO] {info}")
    
    # Teste 6: POST /assistants/search com Origin (como Studio faria)
    print("\n[6] Testando POST /assistants/search com Origin header...")
    success, info = test_endpoint(
        "POST",
        "/assistants/search",
        data={"limit": 10},
        headers={
            "Content-Type": "application/json",
            "Origin": "https://smith.langchain.com"
        },
        description="Busca com Origin header"
    )
    results["POST /assistants/search (com Origin)"] = success
    if success:
        cors_origin = info['headers'].get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
        print(f"   [OK] Status {info['status']}")
        print(f"   Access-Control-Allow-Origin: {cors_origin}")
    else:
        print(f"   [ERRO] {info}")
    
    # Resumo
    print("\n" + "=" * 70)
    print("Resumo dos Testes")
    print("=" * 70)
    
    all_ok = all(results.values())
    
    for endpoint, passed in results.items():
        status = "[OK]" if passed else "[ERRO]"
        print(f"{status} {endpoint}")
    
    if all_ok:
        print("\n" + "=" * 70)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print(f"\nServidor está pronto para conectar no LangSmith Studio:")
        print(f"1. Base URL: {BASE_URL}")
        print(f"2. Em Advanced Settings > Allowed Origins, adicione:")
        print(f"   - {BASE_URL}")
        print(f"   - http://localhost:8555")
    else:
        print("\n" + "=" * 70)
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        print("\nVerifique:")
        print("1. Se o servidor está rodando: langgraph dev --port 8555")
        print("2. Se há erros nos logs do servidor")
        print("3. Se a porta 8555 está livre")
        sys.exit(1)

if __name__ == "__main__":
    main()
