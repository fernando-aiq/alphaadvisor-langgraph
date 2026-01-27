"""
Script completo para testar LangGraph Server localmente com LangSmith Studio.

Este script:
1. Verifica se o servidor está rodando
2. Testa todos os endpoints
3. Verifica CORS
4. Fornece instruções para conectar no Studio
"""
import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"
ALT_URL = "http://localhost:8000"

def check_server_running():
    """Verifica se o servidor está rodando"""
    print("=" * 70)
    print("Verificando se o servidor está rodando...")
    print("=" * 70)
    
    for url in [BASE_URL, ALT_URL]:
        try:
            response = requests.get(f"{url}/api/health", timeout=2)
            if response.status_code == 200:
                print(f"\n[OK] Servidor encontrado em: {url}")
                return url
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            continue
    
    print(f"\n[ERRO] Servidor não está rodando em {BASE_URL} ou {ALT_URL}")
    print("\nPara iniciar o servidor, execute:")
    print("  cd backend")
    print("  python application.py")
    return None

def test_endpoints(base_url):
    """Testa todos os endpoints LangGraph Server"""
    print("\n" + "=" * 70)
    print("Testando Endpoints LangGraph Server")
    print("=" * 70)
    
    results = {}
    
    # Teste 1: GET /assistants
    print("\n[1] GET /assistants...")
    try:
        response = requests.get(f"{base_url}/assistants", timeout=10)
        results['assistants_get'] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Status {response.status_code}, {len(data.get('assistants', []))} assistente(s)")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['assistants_get'] = False
    
    # Teste 2: POST /assistants/search
    print("\n[2] POST /assistants/search...")
    try:
        response = requests.post(
            f"{base_url}/assistants/search",
            json={"limit": 10, "offset": 0},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        results['assistants_search'] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Status {response.status_code}, {len(data) if isinstance(data, list) else 0} resultado(s)")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['assistants_search'] = False
    
    # Teste 3: GET /threads
    print("\n[3] GET /threads...")
    try:
        response = requests.get(f"{base_url}/threads", timeout=10)
        results['threads_get'] = response.status_code == 200
        if response.status_code == 200:
            print(f"   [OK] Status {response.status_code}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['threads_get'] = False
    
    # Teste 4: POST /threads
    print("\n[4] POST /threads (criar thread)...")
    try:
        payload = {
            "assistant_id": "agent",
            "input": {
                "messages": [{"role": "user", "content": "ola"}]
            }
        }
        response = requests.post(
            f"{base_url}/threads",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        results['threads_post'] = response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            thread_id = data.get("thread_id", "N/A")
            print(f"   [OK] Status {response.status_code}, Thread ID: {thread_id}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['threads_post'] = False
    
    # Teste 5: GET /health
    print("\n[5] GET /health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        results['health'] = response.status_code == 200
        if response.status_code == 200:
            print(f"   [OK] Status {response.status_code}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['health'] = False
    
    # Teste 6: GET /docs
    print("\n[6] GET /docs...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        results['docs'] = response.status_code == 200
        if response.status_code == 200:
            print(f"   [OK] Status {response.status_code}")
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERRO] {e}")
        results['docs'] = False
    
    return results

def test_cors(base_url):
    """Testa CORS como o LangSmith Studio faria"""
    print("\n" + "=" * 70)
    print("Testando CORS (como LangSmith Studio)")
    print("=" * 70)
    
    # Teste OPTIONS (preflight)
    print("\n[1] OPTIONS /assistants (preflight)...")
    try:
        response = requests.options(
            f"{base_url}/assistants",
            headers={
                "Origin": "https://smith.langchain.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NÃO ENCONTRADO')
        cors_methods = response.headers.get('Access-Control-Allow-Methods', 'NÃO ENCONTRADO')
        
        if response.status_code == 200 and cors_origin:
            print(f"   [OK] Status {response.status_code}")
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
            print(f"   Access-Control-Allow-Methods: {cors_methods}")
            return True
        else:
            print(f"   [ERRO] CORS não configurado corretamente")
            return False
    except Exception as e:
        print(f"   [ERRO] {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("Teste Completo - LangGraph Server Local")
    print("=" * 70)
    
    # Verificar se servidor está rodando
    base_url = check_server_running()
    if not base_url:
        sys.exit(1)
    
    # Testar endpoints
    results = test_endpoints(base_url)
    
    # Testar CORS
    cors_ok = test_cors(base_url)
    
    # Resumo
    print("\n" + "=" * 70)
    print("Resumo dos Testes")
    print("=" * 70)
    
    all_ok = all(results.values()) and cors_ok
    
    for test, passed in results.items():
        status = "[OK]" if passed else "[ERRO]"
        print(f"{status} {test}")
    
    print(f"{'[OK]' if cors_ok else '[ERRO]'} CORS")
    
    if all_ok:
        print("\n" + "=" * 70)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print(f"\nPara conectar no LangSmith Studio:")
        print(f"1. Acesse: https://smith.langchain.com/")
        print(f"2. Vá em Studio > Connect Studio to local agent")
        print(f"3. Use a Base URL: {base_url}")
        print(f"4. Em Advanced Settings > Allowed Origins, adicione:")
        print(f"   - {base_url}")
        print(f"   - http://127.0.0.1:8000")
        print(f"   - http://localhost:8000")
        print(f"5. Clique em Connect")
        print("\nNota: Se usar Chrome e der erro, tente:")
        print("  - Usar http://127.0.0.1:8000 em vez de http://localhost:8000")
        print("  - Ou desabilitar: chrome://flags/#block-insecure-private-network-requests")
    else:
        print("\n" + "=" * 70)
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        print("\nVerifique:")
        print("1. Se o servidor está rodando corretamente")
        print("2. Se OPENAI_API_KEY está configurada no .env")
        print("3. Se há erros nos logs do servidor")
        sys.exit(1)

if __name__ == "__main__":
    main()
