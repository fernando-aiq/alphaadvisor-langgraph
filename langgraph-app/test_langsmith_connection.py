"""
Script para testar conexão como o LangSmith Studio faria
Simula exatamente as requisições que o Studio faz
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8555"

def main():
    """Simula conexão do LangSmith Studio"""
    print("=" * 70)
    print("Teste de Conexão - Simulando LangSmith Studio")
    print("=" * 70)
    
    results = {}
    
    # 1. OPTIONS preflight (CORS)
    print("\n[1] OPTIONS /assistants (preflight CORS)...")
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
        results["OPTIONS preflight"] = response.status_code == 200
        if response.status_code == 200:
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
            print(f"   [OK] Status {response.status_code}")
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
            if cors_origin != 'https://smith.langchain.com':
                print(f"   [AVISO] CORS origin não corresponde ao esperado")
        else:
            print(f"   [ERRO] Status {response.status_code}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results["OPTIONS preflight"] = False
    
    # 2. GET /assistants (com Origin)
    print("\n[2] GET /assistants (com Origin header)...")
    try:
        response = requests.get(
            f"{BASE_URL}/assistants",
            headers={
                "Origin": "https://smith.langchain.com",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        results["GET /assistants"] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            assistants = data.get('assistants', [])
            print(f"   [OK] Status {response.status_code}")
            print(f"   Assistentes encontrados: {len(assistants)}")
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results["GET /assistants"] = False
    
    # 3. POST /assistants/search (endpoint crítico)
    print("\n[3] POST /assistants/search (endpoint crítico)...")
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
        results["POST /assistants/search"] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Status {response.status_code}")
            print(f"   Resultados: {len(data) if isinstance(data, list) else 0}")
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results["POST /assistants/search"] = False
    
    # 4. GET / (endpoint raiz)
    print("\n[4] GET / (endpoint raiz)...")
    try:
        response = requests.get(
            f"{BASE_URL}/",
            headers={"Origin": "https://smith.langchain.com"},
            timeout=10
        )
        results["GET /"] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Status {response.status_code}")
            print(f"   Service: {data.get('service', 'N/A')}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results["GET /"] = False
    
    # Resumo
    print("\n" + "=" * 70)
    print("Resumo")
    print("=" * 70)
    
    all_ok = all(results.values())
    
    for test, passed in results.items():
        status = "[OK]" if passed else "[ERRO]"
        print(f"{status} {test}")
    
    if all_ok:
        print("\n" + "=" * 70)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print("\nO servidor está pronto para conectar no LangSmith Studio.")
        print("\nInstruções:")
        print(f"1. Acesse: https://smith.langchain.com/")
        print("2. Vá em Studio > Connect Studio to local agent")
        print(f"3. Base URL: {BASE_URL}")
        print("4. Em Advanced Settings > Allowed Origins, adicione:")
        print(f"   - {BASE_URL}")
        print(f"   - http://localhost:8555")
        print("5. Clique em Connect")
    else:
        print("\n" + "=" * 70)
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        print("\nVerifique:")
        print("1. Se o servidor está rodando: langgraph dev --port 8555")
        print("2. Se há erros nos logs")
        print("3. Se CORS está configurado corretamente")
        sys.exit(1)

if __name__ == "__main__":
    main()
