"""
Script de teste para validar o fluxo determinístico de cálculos simples.
"""
import sys
from pathlib import Path

# Adicionar o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph_chat import detect_simple_calculation, calculate_simple_expression
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

def test_detect_simple_calculation():
    """Testa a detecção de cálculos simples"""
    print("=" * 60)
    print("Teste de Detecção de Cálculos Simples")
    print("=" * 60)
    print()
    
    test_cases = [
        ("8 por 7", (8.0, '*', 7.0)),
        ("10 mais 5", (10.0, '+', 5.0)),
        ("20 menos 8", (20.0, '-', 8.0)),
        ("100 dividido por 4", (100.0, '/', 4.0)),
        ("8 x 7", (8.0, '*', 7.0)),
        ("10 + 5", (10.0, '+', 5.0)),
        ("20 - 8", (20.0, '-', 8.0)),
        ("100 / 4", (100.0, '/', 4.0)),
        ("8 * 7", (8.0, '*', 7.0)),
        ("8 vezes 7", (8.0, '*', 7.0)),
        ("qual a minha carteira", None),
        ("olá", None),
        ("recomende investimentos", None),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = detect_simple_calculation(input_text.lower())
        
        if result == expected:
            print(f"[OK] PASS: '{input_text}' -> {result}")
            passed += 1
        else:
            print(f"[ERRO] FAIL: '{input_text}'")
            print(f"  Esperado: {expected}")
            print(f"  Obtido:   {result}")
            failed += 1
    
    print()
    print(f"Resultado: {passed} passaram, {failed} falharam")
    return failed == 0


def test_calculate_simple_expression():
    """Testa o cálculo de expressões simples"""
    print()
    print("=" * 60)
    print("Teste de Cálculo de Expressões Simples")
    print("=" * 60)
    print()
    
    test_cases = [
        (8.0, '*', 7.0, 56.0),
        (10.0, '+', 5.0, 15.0),
        (20.0, '-', 8.0, 12.0),
        (100.0, '/', 4.0, 25.0),
        (15.0, '*', 3.0, 45.0),
    ]
    
    passed = 0
    failed = 0
    
    for num1, operator, num2, expected in test_cases:
        try:
            result = calculate_simple_expression(num1, operator, num2)
            if abs(result - expected) < 0.0001:  # Comparação com tolerância para floats
                print(f"[OK] PASS: {num1} {operator} {num2} = {result}")
                passed += 1
            else:
                print(f"[ERRO] FAIL: {num1} {operator} {num2}")
                print(f"  Esperado: {expected}")
                print(f"  Obtido:   {result}")
                failed += 1
        except Exception as e:
            print(f"[ERRO] ERROR: {num1} {operator} {num2} -> {e}")
            failed += 1
    
    # Teste de divisão por zero
    try:
        calculate_simple_expression(10.0, '/', 0.0)
        print("[ERRO] FAIL: Divisão por zero deveria lançar exceção")
        failed += 1
    except ValueError:
        print("[OK] PASS: Divisão por zero detectada corretamente")
        passed += 1
    
    print()
    print(f"Resultado: {passed} passaram, {failed} falharam")
    return failed == 0


def test_should_route_to_calculation():
    """Testa a função de roteamento"""
    print()
    print("=" * 60)
    print("Teste de Roteamento")
    print("=" * 60)
    print()
    
    from agent.graph_chat import should_route_to_calculation
    
    test_cases = [
        ("8 por 7", "calculate"),
        ("10 mais 5", "calculate"),
        ("qual a minha carteira", "agent"),
        ("olá", "agent"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_route in test_cases:
        state: MessagesState = {
            "messages": [HumanMessage(content=input_text)]
        }
        result = should_route_to_calculation(state)
        
        if result == expected_route:
            print(f"[OK] PASS: '{input_text}' -> {result}")
            passed += 1
        else:
            print(f"[ERRO] FAIL: '{input_text}'")
            print(f"  Esperado: {expected_route}")
            print(f"  Obtido:   {result}")
            failed += 1
    
    print()
    print(f"Resultado: {passed} passaram, {failed} falharam")
    return failed == 0


def main():
    """Executa todos os testes"""
    print()
    print("=" * 60)
    print("Testes do Fluxo Determinístico de Cálculos")
    print("=" * 60)
    print()
    
    test1 = test_detect_simple_calculation()
    test2 = test_calculate_simple_expression()
    test3 = test_should_route_to_calculation()
    
    print()
    print("=" * 60)
    if test1 and test2 and test3:
        print("[OK] TODOS OS TESTES PASSARAM!")
    else:
        print("[ERRO] ALGUNS TESTES FALHARAM")
    print("=" * 60)


if __name__ == "__main__":
    main()
