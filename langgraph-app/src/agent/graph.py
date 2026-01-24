"""Reexporta o grafo usado pelo LangGraph/Studio (MessagesState + tools).

A implementação está em graph_chat.py; langgraph.json aponta para graph_chat
para o Studio reconhecer a chave "messages" e ativar o Chat.
"""

from agent.graph_chat import graph

__all__ = ["graph"]
