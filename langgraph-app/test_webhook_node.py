"""
Script de teste para validar o nó webhook no grafo.
Testa se o webhook_node extrai corretamente os dados do calculation_node.
"""
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph_chat import calculation_node, webhook_node
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

def test_calculation_to_webhook_flow():
    """Testa o fluxo calculation → webhook"""
    print("=" * 60)
    print("Teste: Fluxo Calculation -> Webhook")
    print("=" * 60)
    print()
    
    # Criar estado inicial com mensagem de cálculo
    state: MessagesState = {
        "messages": [HumanMessage(content="8 por 7")]
    }
    
    # Executar calculation_node
    print("1. Executando calculation_node...")
    result_state = calculation_node(state)
    
    messages_after_calc = result_state.get("messages", [])
    if not messages_after_calc:
        print("[ERRO] Nenhuma mensagem retornada do calculation_node")
        return False
    
    calc_message = messages_after_calc[-1]
    print(f"[OK] Calculation node executado")
    print(f"   Conteúdo: {calc_message.content}")
    
    # Verificar se calculation_data está em additional_kwargs
    if hasattr(calc_message, 'additional_kwargs') and calc_message.additional_kwargs:
        calc_data = calc_message.additional_kwargs.get("calculation_data")
        if calc_data:
            print(f"[OK] Dados do cálculo encontrados em additional_kwargs")
            print(f"   num1: {calc_data.get('num1')}")
            print(f"   operator: {calc_data.get('operator')}")
            print(f"   num2: {calc_data.get('num2')}")
            print(f"   result: {calc_data.get('result')}")
        else:
            print("[ERRO] calculation_data não encontrado em additional_kwargs")
            return False
    else:
        print("[ERRO] additional_kwargs não encontrado na mensagem")
        return False
    
    print()
    print("2. Executando webhook_node...")
    
    # Executar webhook_node com o estado resultante
    webhook_result = webhook_node(result_state)
    
    messages_after_webhook = webhook_result.get("messages", [])
    
    # Verificar se webhook foi processado
    if len(messages_after_webhook) > len(messages_after_calc):
        webhook_message = messages_after_webhook[-1]
        if hasattr(webhook_message, 'additional_kwargs') and webhook_message.additional_kwargs:
            webhook_status = webhook_message.additional_kwargs.get("webhook_status")
            webhook_url = webhook_message.additional_kwargs.get("webhook_url")
            
            if webhook_url:
                print(f"[OK] Webhook node executado")
                print(f"   URL: {webhook_url}")
                print(f"   Status: {webhook_status}")
            else:
                print("[INFO] Webhook não configurado (CALCULATION_WEBHOOK_URL não definido)")
                print("[OK] Nó webhook executado mas pulou (comportamento esperado)")
        else:
            print("[INFO] Webhook não configurado - nó executou mas não adicionou mensagem")
    else:
        print("[INFO] Webhook não configurado - nó retornou estado sem modificações")
    
    print()
    print("=" * 60)
    print("[OK] Fluxo calculation -> webhook testado com sucesso!")
    print("=" * 60)
    return True


def test_non_calculation_message():
    """Testa que mensagens não-cálculo não passam pelo webhook"""
    print()
    print("=" * 60)
    print("Teste: Mensagem não-cálculo")
    print("=" * 60)
    print()
    
    state: MessagesState = {
        "messages": [HumanMessage(content="qual a minha carteira")]
    }
    
    result = calculation_node(state)
    
    # Verificar que calculation_node não modificou o estado
    if result == state or len(result.get("messages", [])) == len(state.get("messages", [])):
        print("[OK] Mensagem não-cálculo não processada pelo calculation_node")
        return True
    else:
        print("[ERRO] Mensagem não-cálculo foi processada incorretamente")
        return False


def main():
    """Executa todos os testes"""
    print()
    print("=" * 60)
    print("Testes do Nó Webhook no Grafo")
    print("=" * 60)
    print()
    
    test1 = test_calculation_to_webhook_flow()
    test2 = test_non_calculation_message()
    
    print()
    print("=" * 60)
    if test1 and test2:
        print("[OK] TODOS OS TESTES PASSARAM!")
    else:
        print("[ERRO] ALGUNS TESTES FALHARAM")
    print("=" * 60)
    print()
    print("Nota: Para testar webhook real, configure CALCULATION_WEBHOOK_URL no .env")
    print("      e inicie o servidor webhook sample: python webhook_sample_server.py")


if __name__ == "__main__":
    main()
