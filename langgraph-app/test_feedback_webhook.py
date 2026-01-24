"""
Script de teste para validar o fluxo de feedback condicional para webhook.
"""
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph_chat import calculation_node, detect_positive_feedback, should_call_webhook
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import MessagesState

def test_calculation_with_question():
    """Testa se calculation_node inclui a pergunta"""
    print("=" * 60)
    print("Teste: Calculation Node com Pergunta")
    print("=" * 60)
    print()
    
    state: MessagesState = {
        "messages": [HumanMessage(content="8 por 7")]
    }
    
    result = calculation_node(state)
    messages = result.get("messages", [])
    
    if messages:
        calc_message = messages[-1]
        content = calc_message.content
        print(f"[OK] Calculation node retornou mensagem")
        print(f"   Conteudo: {content}")
        
        if "Você gostou do resultado?" in content:
            print("[OK] Pergunta incluida na resposta")
            return True
        else:
            print("[ERRO] Pergunta nao encontrada na resposta")
            return False
    else:
        print("[ERRO] Nenhuma mensagem retornada")
        return False


def test_positive_feedback_detection():
    """Testa detecção de feedback positivo"""
    print()
    print("=" * 60)
    print("Teste: Detecção de Feedback Positivo")
    print("=" * 60)
    print()
    
    # Simular estado após cálculo: mensagem do cálculo + resposta do usuário
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
    
    test_cases = [
        ("sim", True),
        ("gostei", True),
        ("obrigado", True),
        ("perfeito", True),
        ("não", False),
        ("não gostei", False),
        ("errado", False),
    ]
    
    passed = 0
    failed = 0
    
    for user_response, expected in test_cases:
        state: MessagesState = {
            "messages": [
                HumanMessage(content="8 por 7"),  # Mensagem original
                calc_message,  # Resposta do cálculo
                HumanMessage(content=user_response)  # Feedback do usuário
            ]
        }
        
        result = detect_positive_feedback(state)
        
        if result == expected:
            print(f"[OK] '{user_response}' -> {result} (esperado: {expected})")
            passed += 1
        else:
            print(f"[ERRO] '{user_response}' -> {result} (esperado: {expected})")
            failed += 1
    
    print()
    print(f"Resultado: {passed} passaram, {failed} falharam")
    return failed == 0


def test_should_call_webhook():
    """Testa função de roteamento should_call_webhook"""
    print()
    print("=" * 60)
    print("Teste: Roteamento should_call_webhook")
    print("=" * 60)
    print()
    
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
    
    # Teste com feedback positivo
    state_positive: MessagesState = {
        "messages": [
            HumanMessage(content="8 por 7"),
            calc_message,
            HumanMessage(content="sim")
        ]
    }
    
    result = should_call_webhook(state_positive)
    if result == "webhook":
        print("[OK] Feedback positivo -> roteia para webhook")
    else:
        print(f"[ERRO] Feedback positivo -> {result} (esperado: webhook)")
        return False
    
    # Teste com feedback negativo
    state_negative: MessagesState = {
        "messages": [
            HumanMessage(content="8 por 7"),
            calc_message,
            HumanMessage(content="não")
        ]
    }
    
    result = should_call_webhook(state_negative)
    if result == "end":
        print("[OK] Feedback negativo -> roteia para end")
    else:
        print(f"[ERRO] Feedback negativo -> {result} (esperado: end)")
        return False
    
    # Teste sem feedback (apenas cálculo)
    state_no_feedback: MessagesState = {
        "messages": [
            HumanMessage(content="8 por 7"),
            calc_message
        ]
    }
    
    result = should_call_webhook(state_no_feedback)
    if result == "end":
        print("[OK] Sem feedback -> roteia para end")
    else:
        print(f"[ERRO] Sem feedback -> {result} (esperado: end)")
        return False
    
    return True


def main():
    """Executa todos os testes"""
    print()
    print("=" * 60)
    print("Testes do Fluxo de Feedback Condicional")
    print("=" * 60)
    print()
    
    test1 = test_calculation_with_question()
    test2 = test_positive_feedback_detection()
    test3 = test_should_call_webhook()
    
    print()
    print("=" * 60)
    if test1 and test2 and test3:
        print("[OK] TODOS OS TESTES PASSARAM!")
    else:
        print("[ERRO] ALGUNS TESTES FALHARAM")
    print("=" * 60)
    print()
    print("Nota: O fluxo completo requer duas invocacoes:")
    print("  1. Usuario: '8 por 7' -> Calculation: 'O resultado e 56. Voce gostou?'")
    print("  2. Usuario: 'sim' -> Webhook (se feedback positivo) ou End")


if __name__ == "__main__":
    main()
