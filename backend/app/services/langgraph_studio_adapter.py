"""
Adapter para conectar LangGraph Agent com LangSmith Studio.

Converte entre MessagesState (formato esperado pelo Studio) e AgentState
(formato usado pelo grafo interno).
"""
import os
import uuid
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.services.langgraph_agent import LangGraphAgent, AgentState


class LangGraphStudioAdapter:
    """Adapter para converter entre MessagesState e AgentState"""
    
    def __init__(self, custom_graph_config: Optional[Dict] = None):
        """Inicializa o adapter com uma instância do LangGraphAgent"""
        try:
            self.agent = LangGraphAgent(custom_graph_config=custom_graph_config)
            self.graph = self.agent.graph if self.agent else None
            if not self.graph:
                raise RuntimeError("LangGraph não foi inicializado corretamente")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[LangGraphStudioAdapter] Erro ao inicializar: {e}")
            self.agent = None
            self.graph = None
            raise
    
    def messages_to_agent_state(self, messages: List[Dict], thread_id: Optional[str] = None) -> AgentState:
        """
        Converte mensagens do formato Studio para AgentState.
        
        Args:
            messages: Lista de mensagens no formato [{"role": "user", "content": "..."}]
            thread_id: ID da thread (usado como trace_id)
        
        Returns:
            AgentState pronto para execução
        """
        # Extrair última mensagem do usuário e histórico
        user_message = None
        context = []
        
        # Processar mensagens em ordem
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                # Se já temos uma mensagem do usuário, a anterior vai para contexto
                if user_message is not None:
                    context.append({"role": "user", "content": user_message})
                user_message = content
            elif role == "assistant":
                # Mensagens do assistente vão para contexto
                context.append({"role": "assistant", "content": content})
        
        # Se não encontrou mensagem do usuário, usar a última mensagem
        if not user_message and messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user":
                user_message = last_msg.get("content", "")
            else:
                # Se última mensagem não é do usuário, usar conteúdo mesmo assim
                user_message = last_msg.get("content", "")
        
        # Se ainda não tem mensagem, usar string vazia
        if not user_message:
            user_message = ""
        
        # Usar thread_id como trace_id se fornecido, senão gerar novo
        trace_id = thread_id or str(uuid.uuid4())
        
        return {
            "message": user_message,
            "context": context,
            "intent": None,
            "route": None,
            "carteira": None,
            "results": {},
            "response": "",
            "trace_id": trace_id,
            "graph_steps": [],
            "tools_used": []
        }
    
    def agent_state_to_messages(self, agent_state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """
        Converte AgentState de volta para formato MessagesState esperado pelo Studio.
        
        Args:
            agent_state: Estado final do agente após execução
            thread_id: ID da thread
        
        Returns:
            Dicionário no formato esperado pelo Studio
        """
        messages = []
        
        # Adicionar mensagens do contexto (histórico)
        context = agent_state.get("context", [])
        for ctx_msg in context:
            role = ctx_msg.get("role", "user")
            content = ctx_msg.get("content", "")
            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": content})
        
        # Adicionar mensagem do usuário atual
        user_message = agent_state.get("message", "")
        if user_message:
            messages.append({"role": "user", "content": user_message})
        
        # Adicionar resposta do assistente
        response = agent_state.get("response", "")
        if response:
            messages.append({"role": "assistant", "content": response})
        
        return {
            "thread_id": thread_id,
            "values": {
                "messages": messages
            },
            "config": {
                "configurable": {
                    "thread_id": thread_id
                }
            }
        }
    
    def invoke(self, messages: List[Dict], thread_id: Optional[str] = None, config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executa o grafo com mensagens do Studio e retorna resultado no formato esperado.
        
        Args:
            messages: Lista de mensagens no formato Studio
            thread_id: ID da thread (opcional, será gerado se não fornecido)
            config: Configuração adicional (opcional)
        
        Returns:
            Dicionário com thread_id e values (messages)
        """
        if not self.agent or not self.graph:
            raise RuntimeError("LangGraph não está disponível")
        
        # Gerar thread_id se não fornecido
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Extrair última mensagem do usuário e contexto
        user_message = None
        context = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                if user_message is not None:
                    context.append({"role": "user", "content": user_message})
                user_message = content
            elif role == "assistant":
                context.append({"role": "assistant", "content": content})
        
        if not user_message and messages:
            user_message = messages[-1].get("content", "")
        
        if not user_message:
            user_message = ""
        
        try:
            # Usar o método process_message do LangGraphAgent
            # Ele já gerencia trace_id e execução do grafo
            result = self.agent.process_message(user_message, context=context if context else None)
            
            # Extrair resposta e trace_id
            response = result.get("response", "")
            trace_id_used = result.get("trace_id", thread_id)
            
            # Construir lista de mensagens para retorno
            output_messages = []
            
            # Adicionar histórico
            for ctx_msg in context:
                output_messages.append({
                    "role": ctx_msg.get("role", "user"),
                    "content": ctx_msg.get("content", "")
                })
            
            # Adicionar mensagem do usuário
            if user_message:
                output_messages.append({"role": "user", "content": user_message})
            
            # Adicionar resposta do assistente
            if response:
                output_messages.append({"role": "assistant", "content": response})
            
            return {
                "thread_id": trace_id_used,
                "values": {
                    "messages": output_messages
                },
                "config": config or {"configurable": {"thread_id": trace_id_used}}
            }
        except Exception as e:
            # Em caso de erro, retornar mensagem de erro no formato esperado
            import traceback
            traceback.print_exc()
            
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            messages_with_error = messages.copy()
            messages_with_error.append({"role": "assistant", "content": error_msg})
            
            return {
                "thread_id": thread_id,
                "values": {
                    "messages": messages_with_error
                },
                "config": config or {"configurable": {"thread_id": thread_id}},
                "error": str(e)
            }
    
    def stream(self, messages: List[Dict], thread_id: Optional[str] = None, config: Optional[Dict] = None):
        """
        Executa o grafo em modo stream (para suporte futuro).
        
        Args:
            messages: Lista de mensagens no formato Studio
            thread_id: ID da thread
            config: Configuração adicional
        
        Yields:
            Eventos de stream no formato esperado pelo Studio
        """
        if not self.graph:
            raise RuntimeError("LangGraph não está disponível")
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        agent_state = self.messages_to_agent_state(messages, thread_id)
        graph_config = config or {"configurable": {"thread_id": thread_id}}
        
        try:
            # Stream do grafo
            for event in self.graph.stream(agent_state, graph_config):
                # Converter eventos para formato Studio
                yield {
                    "event": "on_chain_start" if "on_chain_start" in str(event) else "data",
                    "data": event,
                    "thread_id": thread_id
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": str(e)},
                "thread_id": thread_id
            }
