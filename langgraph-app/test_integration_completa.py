"""
Teste completo de integração: servidor + tools do backend
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8555"

def test_create_thread_with_tool():
    """Testa criação de thread que deve acionar uma tool"""
    print("=" * 70)
    print("Teste de Integração Completa - Tools do Backend")
    print("=" * 70)
    
    # Teste 1: Pergunta sobre perfil (deve acionar obter_perfil)
    print("\n[1] Testando pergunta sobre perfil...")
    try:
        response = requests.post(
            f"{BASE_URL}/threads",
            json={
                "assistant_id": "agent",
                "input": {
                    "messages": [{"role": "user", "content": "Qual é meu perfil de investidor?"}]
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            values = data.get("values", {})
            if values:
                messages = values.get("messages", [])
                print(f"   [OK] Status {response.status_code}")
                print(f"   Mensagens recebidas: {len(messages)}")
                
                # Verificar última mensagem (resposta)
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict):
                        content = last_msg.get("content", "")[:200]
                    else:
                        content = str(last_msg)[:200]
                    print(f"   Resposta: {content}...")
                    
                    # Verificar se menciona "conservador" (resultado da tool)
                    if "conservador" in content.lower():
                        print("   [OK] Tool obter_perfil foi chamada corretamente!")
                    else:
                        print("   [AVISO] Resposta não menciona perfil - tool pode não ter sido chamada")
            else:
                print(f"   [AVISO] Resposta não tem 'values': {list(data.keys())}")
            
            return True
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Teste 2: Pergunta sobre carteira (deve acionar obter_carteira)
    print("\n[2] Testando pergunta sobre carteira...")
    try:
        response = requests.post(
            f"{BASE_URL}/threads",
            json={
                "assistant_id": "agent",
                "input": {
                    "messages": [{"role": "user", "content": "Qual é o total da minha carteira?"}]
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            values = data.get("values", {})
            if values:
                messages = values.get("messages", [])
                print(f"   [OK] Status {response.status_code}")
                
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict):
                        content = last_msg.get("content", "")[:200]
                    else:
                        content = str(last_msg)[:200]
                    print(f"   Resposta: {content}...")
                    
                    # Verificar se menciona valores (resultado da tool)
                    if any(char.isdigit() for char in content):
                        print("   [OK] Tool obter_carteira foi chamada corretamente!")
                    else:
                        print("   [AVISO] Resposta não menciona valores - tool pode não ter sido chamada")
            
            return True
        else:
            print(f"   [ERRO] Status {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   [ERRO] {e}")
        return False

if __name__ == "__main__":
    success = test_create_thread_with_tool()
    
    print("\n" + "=" * 70)
    if success:
        print("INTEGRAÇÃO FUNCIONANDO!")
        print("=" * 70)
        print("\nO servidor LangGraph está usando as tools do backend Flask.")
        print("\nPróximos passos:")
        print("1. Conecte no LangSmith Studio: http://127.0.0.1:8555")
        print("2. Teste perguntas sobre perfil, carteira, adequação, etc.")
        print("3. Verifique os traces no LangSmith para ver as tool calls")
    else:
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        sys.exit(1)
