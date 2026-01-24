"""
Script para testar threads no LangGraph Server na porta 8222
"""
import requests
import json

BASE_URL = "http://localhost:8222"

def get_assistant_id():
    """Busca o assistant_id disponível"""
    response = requests.post(f"{BASE_URL}/assistants/search", json={})
    if response.status_code == 200:
        assistants = response.json()
        if assistants:
            assistant_id = assistants[0]["assistant_id"]
            print(f"[OK] Assistant encontrado: {assistant_id}")
            return assistant_id
    print(f"[ERRO] Erro ao buscar assistant: {response.status_code} - {response.text}")
    return None

def create_thread(assistant_id, message="Olá"):
    """Cria uma nova thread com uma mensagem"""
    payload = {
        "assistant_id": assistant_id,
        "input": {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
    }
    
    response = requests.post(f"{BASE_URL}/threads", json=payload)
    if response.status_code == 200:
        thread_data = response.json()
        thread_id = thread_data["thread_id"]
        print(f"[OK] Thread criada: {thread_id}")
        print(f"   Resposta: {json.dumps(thread_data, indent=2, ensure_ascii=False)}")
        return thread_id
    else:
        print(f"[ERRO] Erro ao criar thread: {response.status_code}")
        print(f"   Resposta: {response.text}")
        return None

def update_thread(thread_id, assistant_id, message):
    """Atualiza uma thread existente com nova mensagem (cria um novo run)"""
    payload = {
        "assistant_id": assistant_id,
        "input": {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
    }
    
    # LangGraph CLI usa POST /threads/{thread_id}/runs para criar nova execução
    response = requests.post(f"{BASE_URL}/threads/{thread_id}/runs", json=payload)
    if response.status_code == 200:
        thread_data = response.json()
        print(f"[OK] Thread atualizada: {thread_id}")
        print(f"   Resposta: {json.dumps(thread_data, indent=2, ensure_ascii=False)}")
        return thread_data
    else:
        print(f"[ERRO] Erro ao atualizar thread: {response.status_code}")
        print(f"   Resposta: {response.text}")
        return None

def get_thread(thread_id):
    """Obtém informações de uma thread"""
    response = requests.get(f"{BASE_URL}/threads/{thread_id}")
    if response.status_code == 200:
        thread_data = response.json()
        print(f"[OK] Thread encontrada: {thread_id}")
        print(f"   Dados: {json.dumps(thread_data, indent=2, ensure_ascii=False)}")
        return thread_data
    else:
        print(f"[ERRO] Erro ao buscar thread: {response.status_code}")
        print(f"   Resposta: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Teste de Threads - LangGraph Server (Porta 8222)")
    print("=" * 60)
    print()
    
    # 1. Buscar assistant_id
    print("1. Buscando assistant_id...")
    assistant_id = get_assistant_id()
    if not assistant_id:
        print("[ERRO] Não foi possível obter assistant_id. Abortando.")
        return
    print()
    
    # 2. Criar thread
    print("2. Criando thread com mensagem inicial...")
    thread_id = create_thread(assistant_id, "Olá, preciso de ajuda com investimentos")
    if not thread_id:
        print("[ERRO] Não foi possível criar thread. Abortando.")
        return
    print()
    
    # 3. Obter thread
    print("3. Obtendo informações da thread...")
    get_thread(thread_id)
    print()
    
    # 4. Atualizar thread
    print("4. Atualizando thread com nova mensagem...")
    update_thread(thread_id, assistant_id, "Recomende investimentos para mim")
    print()
    
    # 5. Testar handoff
    print("5. Testando handoff com solicitação de recomendação...")
    update_thread(thread_id, assistant_id, "Onde devo investir meu dinheiro?")
    print()
    
    print("=" * 60)
    print("Teste concluído!")
    print("=" * 60)

if __name__ == "__main__":
    main()
