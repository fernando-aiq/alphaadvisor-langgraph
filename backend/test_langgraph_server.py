"""
Script de teste para endpoints LangGraph Server.

Testa os endpoints criados para compatibilidade com LangSmith Studio.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_assistants():
    """Testa endpoint GET /langgraph/assistants"""
    print("\n=== Testando GET /langgraph/assistants ===")
    try:
        response = requests.get(f"{BASE_URL}/langgraph/assistants")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_create_thread():
    """Testa endpoint POST /langgraph/threads"""
    print("\n=== Testando POST /langgraph/threads ===")
    try:
        payload = {
            "assistant_id": "agent",
            "input": {
                "messages": [
                    {"role": "user", "content": "qual é minha carteira?"}
                ]
            }
        }
        response = requests.post(
            f"{BASE_URL}/langgraph/threads",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            thread_id = result.get("thread_id")
            print(f"\nThread ID criado: {thread_id}")
            return thread_id
        return None
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_health():
    """Testa endpoint GET /langgraph/health"""
    print("\n=== Testando GET /langgraph/health ===")
    try:
        response = requests.get(f"{BASE_URL}/langgraph/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_list_threads():
    """Testa endpoint GET /langgraph/threads"""
    print("\n=== Testando GET /langgraph/threads ===")
    try:
        response = requests.get(f"{BASE_URL}/langgraph/threads")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("Testes dos Endpoints LangGraph Server")
    print("=" * 60)
    
    # Teste 1: Health check
    health_ok = test_health()
    
    # Teste 2: List assistants
    assistants_ok = test_assistants()
    
    # Teste 3: List threads (deve retornar vazio por enquanto)
    threads_ok = test_list_threads()
    
    # Teste 4: Create thread (teste principal)
    thread_id = test_create_thread()
    
    print("\n" + "=" * 60)
    print("Resumo dos Testes")
    print("=" * 60)
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"List Assistants: {'✅' if assistants_ok else '❌'}")
    print(f"List Threads: {'✅' if threads_ok else '❌'}")
    print(f"Create Thread: {'✅' if thread_id else '❌'}")
    
    if thread_id:
        print(f"\n✅ Thread criado com sucesso: {thread_id}")
        print(f"\nPara testar no LangSmith Studio:")
        print(f"1. Acesse: https://smith.langchain.com/")
        print(f"2. Vá em Studio > Connect")
        print(f"3. Use a URL: {BASE_URL}")
        print(f"4. Ou use a URL do Elastic Beanstalk após deploy")
    else:
        print("\n❌ Falha ao criar thread. Verifique os logs do servidor.")

if __name__ == "__main__":
    main()
