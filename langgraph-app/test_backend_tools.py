"""
Script para testar se as tools do backend estão funcionando no grafo
"""
import sys
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

from agent.graph_chat import graph, tools
from langchain_core.messages import HumanMessage

def test_graph_with_tools():
    """Testa o grafo com uma mensagem que deve acionar tools"""
    print("=" * 70)
    print("Testando Grafo com Tools do Backend")
    print("=" * 70)
    
    print(f"\nTools disponíveis: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:80]}...")
    
    # Testar com mensagem sobre perfil
    print("\n[1] Testando mensagem sobre perfil...")
    try:
        result = graph.invoke({
            "messages": [HumanMessage(content="Qual é meu perfil de investidor?")]
        })
        
        messages = result.get("messages", [])
        print(f"   Resposta recebida: {len(messages)} mensagens")
        
        # Verificar se há tool calls
        tool_calls_found = False
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls_found = True
                print(f"   Tool calls encontrados: {len(msg.tool_calls)}")
                for tc in msg.tool_calls:
                    print(f"     - {tc.get('name', 'N/A')}")
        
        if not tool_calls_found:
            print("   [AVISO] Nenhuma tool call encontrada - o LLM pode ter respondido diretamente")
        
        # Última mensagem (resposta final)
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                content = last_msg.content[:200]
                print(f"   Resposta: {content}...")
        
        print("   [OK] Grafo executado com sucesso")
        return True
        
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Testar com mensagem sobre carteira
    print("\n[2] Testando mensagem sobre carteira...")
    try:
        result = graph.invoke({
            "messages": [HumanMessage(content="Qual é o total da minha carteira?")]
        })
        
        messages = result.get("messages", [])
        print(f"   Resposta recebida: {len(messages)} mensagens")
        
        # Verificar tool calls
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print(f"   Tool calls: {[tc.get('name') for tc in msg.tool_calls]}")
        
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                content = last_msg.content[:200]
                print(f"   Resposta: {content}...")
        
        print("   [OK] Grafo executado com sucesso")
        return True
        
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_graph_with_tools()
    if success:
        print("\n" + "=" * 70)
        print("TESTES CONCLUÍDOS")
        print("=" * 70)
        print("\nO grafo está funcionando com as tools do backend!")
        print("Agora você pode iniciar o servidor e testar no LangSmith Studio.")
    else:
        print("\n" + "=" * 70)
        print("ALGUNS TESTES FALHARAM")
        print("=" * 70)
        sys.exit(1)
