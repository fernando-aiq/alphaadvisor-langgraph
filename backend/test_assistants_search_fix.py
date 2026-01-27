"""
Teste para verificar se o endpoint /assistants/search está funcionando
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_search_assistants():
    """Testa o endpoint POST /assistants/search"""
    print("=" * 70)
    print("Teste: POST /assistants/search")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/assistants/search",
            json={"limit": 10},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("\n✅ Endpoint funcionando corretamente!")
            return True
        else:
            print(f"Erro: {response.text}")
            print("\n❌ Endpoint retornou erro")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando")
        print("Execute: cd backend && python application.py")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_search_assistants()
    exit(0 if success else 1)
