"""
Script de teste para validar o webhook de cálculos.
Certifique-se de que o servidor webhook sample está rodando antes de executar.
"""

import requests
import json
import time

WEBHOOK_URL = "http://localhost:8888/webhook/calculation"
HISTORY_URL = "http://localhost:8888/webhook/calculation/history"

def test_webhook():
    """Testa o webhook enviando um payload de exemplo"""
    print("=" * 60)
    print("Teste de Webhook - Cálculo")
    print("=" * 60)
    print()
    
    # Payload de exemplo
    payload = {
        "event": "calculation_executed",
        "timestamp": "2026-01-22T19:30:45.123456Z",
        "data": {
            "num1": 8.0,
            "operator": "*",
            "num2": 7.0,
            "result": 56.0,
            "user_message": "8 por 7",
            "expression": "8.0 * 7.0 = 56.0"
        }
    }
    
    print("Enviando webhook...")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        if response.status_code == 200:
            print("[OK] Webhook recebido com sucesso!")
        else:
            print(f"[ERRO] Webhook retornou status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERRO] Não foi possível conectar ao servidor webhook.")
        print("Certifique-se de que o servidor está rodando:")
        print("  python webhook_sample_server.py")
    except Exception as e:
        print(f"[ERRO] Erro ao enviar webhook: {e}")


def check_history():
    """Verifica o histórico de cálculos recebidos"""
    print()
    print("=" * 60)
    print("Verificando Histórico")
    print("=" * 60)
    print()
    
    try:
        response = requests.get(HISTORY_URL, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total de cálculos recebidos: {data.get('total', 0)}")
            print()
            
            if data.get('calculations'):
                print("Últimos cálculos:")
                for i, calc in enumerate(data['calculations'][-5:], 1):  # Mostrar últimos 5
                    print(f"\n{i}. {calc.get('calculation', {}).get('expression', 'N/A')}")
                    print(f"   Recebido em: {calc.get('received_at', 'N/A')}")
            else:
                print("Nenhum cálculo no histórico ainda.")
        else:
            print(f"[ERRO] Status {response.status_code}")
            
    except Exception as e:
        print(f"[ERRO] Erro ao verificar histórico: {e}")


def main():
    """Executa testes"""
    print()
    print("Certifique-se de que o servidor webhook está rodando:")
    print("  python webhook_sample_server.py")
    print()
    input("Pressione Enter para continuar...")
    print()
    
    test_webhook()
    time.sleep(1)  # Aguardar um pouco
    check_history()
    
    print()
    print("=" * 60)
    print("Teste concluído!")
    print("=" * 60)


if __name__ == "__main__":
    main()
