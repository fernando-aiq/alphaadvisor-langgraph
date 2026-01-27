"""
Script para testar o endpoint POST /assistants/search após deploy.
Este script testa o endpoint no Elastic Beanstalk e verifica se está funcionando corretamente.
"""
import requests
import json
import sys

# URL do Elastic Beanstalk
EB_URL = "http://Alphaadvisor-v6-env.eba-2mpu5bfe.us-east-2.elasticbeanstalk.com"

def test_search_assistants():
    """Testa o endpoint POST /assistants/search"""
    print("=" * 70)
    print("Teste: POST /assistants/search no Elastic Beanstalk")
    print("=" * 70)
    print(f"URL: {EB_URL}")
    print()
    
    try:
        # Teste 1: Requisição básica
        print("[1] Testando requisição básica...")
        response = requests.post(
            f"{EB_URL}/assistants/search",
            json={"limit": 10, "offset": 0},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("\n✅ Endpoint funcionando corretamente!")
            return True
        else:
            print(f"   Erro: {response.text}")
            print(f"\n❌ Endpoint retornou erro {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - servidor não respondeu em 30 segundos")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - servidor não está acessível")
        print(f"   Verifique se a URL está correta: {EB_URL}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_debug_routes():
    """Testa o endpoint de debug /debug/routes"""
    print("\n" + "=" * 70)
    print("Teste: GET /debug/routes")
    print("=" * 70)
    
    try:
        response = requests.get(
            f"{EB_URL}/debug/routes",
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total de rotas: {data.get('all_routes_count', 0)}")
            print(f"Rotas LangGraph: {len(data.get('langgraph_routes', []))}")
            print("\nRotas LangGraph encontradas:")
            for route in data.get('langgraph_routes', []):
                print(f"  {route['rule']} [{', '.join(route['methods'])}]")
            return True
        else:
            print(f"Erro: {response.text}")
            return False
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    print("Testando endpoints após deploy...")
    print()
    
    success_search = test_search_assistants()
    success_debug = test_debug_routes()
    
    print("\n" + "=" * 70)
    print("Resumo dos Testes")
    print("=" * 70)
    print(f"POST /assistants/search: {'✅ PASSOU' if success_search else '❌ FALHOU'}")
    print(f"GET /debug/routes: {'✅ PASSOU' if success_debug else '❌ FALHOU'}")
    print()
    
    if success_search and success_debug:
        print("✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("❌ Alguns testes falharam. Verifique os logs acima.")
        sys.exit(1)
