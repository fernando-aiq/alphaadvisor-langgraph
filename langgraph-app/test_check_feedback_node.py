"""
Script de teste para validar o nó check_feedback no grafo.
"""
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph_chat import calculation_node, check_feedback_node, should_call_webhook
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import MessagesState

def test_check_feedback_node():
    """Testa o nó check_feedback"""
    print("=" * 60)
    print("Teste: Nó check_feedback")
    print("=" * 60)
    print()
    
    # Simular estado após cálculo com feedback positivo
    calc_message = AIMessage(
        content="O resultado de 8 × 7 é 56.\n\nVocê gostou do resultado?",
        additional_kwargs={
            "calculation_data": {
                "num1": 8.0,
                "operator": "*",
                "num2": 7.0,
                "result": 56.0
            }
        }
    )
    
    state_positive: MessagesState = {
        "messages": [
            HumanMessage(content="8 por 7"),
            calc_message,
            HumanMessage(content="sim")
        ]
    }
    
    print("1. Estado com feedback positivo:")
    print("   Mensagens: cálculo + 'sim'")
    
    result = check_feedback_node(state_positive)
    messages = result.get("messages", [])
    
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'additional_kwargs') and last_msg.additional_kwargs:
            feedback_eval = last_msg.additional_kwargs.get("feedback_evaluated")
            feedback_pos = last_msg.additional_kwargs.get("feedback_positive")
            
            if feedback_eval:
                print(f"[OK] Feedback avaliado: {feedback_pos}")
                if feedback_pos:
                    print("[OK] Feedback positivo detectado corretamente")
                else:
                    print("[ERRO] Feedback deveria ser positivo")
                    return False
            else:
                print("[ERRO] Metadados de avaliação não encontrados")
                return False
    
    # Testar roteamento após check_feedback
    print()
    print("2. Testando roteamento após check_feedback:")
    route = should_call_webhook(result)
    if route == "webhook":
        print("[OK] Roteamento para webhook (feedback positivo)")
    else:
        print(f"[ERRO] Roteamento incorreto: {route} (esperado: webhook)")
        return False
    
    # Teste com feedback negativo
    print()
    print("3. Estado com feedback negativo:")
    state_negative: MessagesState = {
        "messages": [
            HumanMessage(content="8 por 7"),
            calc_message,
            HumanMessage(content="não")
        ]
    }
    
    result_neg = check_feedback_node(state_negative)
    route_neg = should_call_webhook(result_neg)
    if route_neg == "end":
        print("[OK] Roteamento para end (feedback negativo)")
    else:
        print(f"[ERRO] Roteamento incorreto: {route_neg} (esperado: end)")
        return False
    
    print()
    print("=" * 60)
    print("[OK] Nó check_feedback funcionando corretamente!")
    print("=" * 60)
    return True


def main():
    """Executa testes"""
    print()
    print("=" * 60)
    print("Testes do Nó check_feedback")
    print("=" * 60)
    print()
    
    test1 = test_check_feedback_node()
    
    print()
    print("=" * 60)
    if test1:
        print("[OK] TODOS OS TESTES PASSARAM!")
    else:
        print("[ERRO] ALGUNS TESTES FALHARAM")
    print("=" * 60)
    print()
    print("O nó check_feedback agora aparece como nó separado no grafo:")
    print("  calculation -> check_feedback -> [webhook/end]")


if __name__ == "__main__":
    main()
