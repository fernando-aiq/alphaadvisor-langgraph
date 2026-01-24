"""Ferramentas simples para o agente."""

from langchain_core.tools import tool


@tool
def multiply(a: float, b: float) -> float:
    """Multiplica dois números. Use quando o usuário pedir para multiplicar ou calcular um produto."""
    return a * b


@tool
def get_word_length(word: str) -> int:
    """Retorna o número de caracteres de uma palavra. Use quando o usuário perguntar o tamanho ou comprimento de uma palavra."""
    return len(word)
