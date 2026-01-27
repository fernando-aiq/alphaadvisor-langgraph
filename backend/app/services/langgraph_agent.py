"""
Agente LangGraph com conditional edges para routing entre bypass e ReAct.
Implementa grafo de estados para rastreamento completo do fluxo de raciocínio.
"""
import os
import time
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    ToolNode = None
    MemorySaver = None

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

from app.services.agent_tools import (
    obter_carteira, obter_perfil, analisar_adequacao, calcular_projecao,
    buscar_oportunidades, analisar_alinhamento_objetivos,
    analisar_diversificacao, recomendar_rebalanceamento
)
from app.services.traceability_service import TraceabilityService

class AgentState(TypedDict):
    """Estado do agente LangGraph"""
    message: str
    context: Optional[List[Dict]]
    intent: Optional[str]
    route: Optional[str]  # 'bypass' ou 'react'
    carteira: Optional[Dict]
    results: Dict[str, Any]
    response: str
    trace_id: str
    graph_steps: List[Dict]
    tools_used: List[str]

class LangGraphAgent:
    """Agente usando LangGraph com conditional edges"""
    
    def __init__(self, custom_graph_config: Optional[Dict] = None):
        api_key = os.getenv('OPENAI_API_KEY', '')
        model = os.getenv('AI_MODEL', 'gpt-4o')
        
        if api_key:
            self.llm = ChatOpenAI(model=model, temperature=0.7, api_key=api_key)
        else:
            self.llm = None
        
        self.traceability = TraceabilityService()
        self.graph = None
        self.graph_structure = None  # Cache da estrutura do grafo
        self.custom_graph_config = custom_graph_config
        
        if LANGGRAPH_AVAILABLE and self.llm:
            if custom_graph_config and custom_graph_config.get('graph_structure'):
                # Tentar construir grafo customizado
                try:
                    self.graph = self._build_graph_from_config(custom_graph_config['graph_structure'])
                    self.graph_structure = custom_graph_config['graph_structure']
                except Exception as e:
                    print(f"[LangGraphAgent] Erro ao construir grafo customizado, usando padrão: {e}")
                    self.graph = self._build_graph()
                    self.graph_structure = self._get_default_graph_structure()
            else:
                self.graph = self._build_graph()
                self.graph_structure = self._get_default_graph_structure()
    
    def _get_checkpointer(self):
        """Retorna checkpointer apropriado: LangSmithCheckpointer se disponível, senão MemorySaver"""
        langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
        if langsmith_api_key:
            try:
                from langgraph.checkpoint.langsmith import LangSmithCheckpointer
                project_name = os.getenv('LANGSMITH_PROJECT', 'alphaadvisor')
                print(f"[LangGraphAgent] Usando LangSmithCheckpointer - Projeto: {project_name}")
                return LangSmithCheckpointer(project_name=project_name)
            except ImportError:
                print("[LangGraphAgent] LangSmithCheckpointer não disponível, usando MemorySaver")
            except Exception as e:
                print(f"[LangGraphAgent] Erro ao configurar LangSmithCheckpointer: {e}, usando MemorySaver")
        
        return MemorySaver()
    
    def _build_graph(self):
        """Constrói o grafo LangGraph com conditional edges"""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        # Criar grafo
        graph = StateGraph(AgentState)
        
        # Adicionar nós
        graph.add_node("detect_intent", self._detect_intent_node)
        graph.add_node("route_decision", self._route_decision_node)
        graph.add_node("bypass_analysis", self._bypass_analysis_node)
        graph.add_node("react_agent", self._react_agent_node)
        graph.add_node("format_response", self._format_response_node)
        
        # Definir entry point
        graph.set_entry_point("detect_intent")
        
        # Adicionar edges
        graph.add_edge("detect_intent", "route_decision")
        
        # Conditional edge: route_decision → bypass ou react
        graph.add_conditional_edges(
            "route_decision",
            self._should_use_bypass,
            {
                "bypass": "bypass_analysis",
                "react": "react_agent"
            }
        )
        
        # Ambos os caminhos levam ao format_response
        graph.add_edge("bypass_analysis", "format_response")
        graph.add_edge("react_agent", "format_response")
        graph.add_edge("format_response", END)
        
        # Compilar grafo com checkpointer apropriado
        checkpointer = self._get_checkpointer()
        return graph.compile(checkpointer=checkpointer)
    
    def _get_default_graph_structure(self) -> Dict[str, Any]:
        """Retorna a estrutura padrão do grafo para visualização com informações completas"""
        return {
            'entry_point': 'detect_intent',
            'nodes': [
                {
                    'id': 'detect_intent',
                    'type': 'langgraph_node',
                    'label': 'Detectar Intenção',
                    'description': 'Detecta a intenção da mensagem do usuário usando análise de palavras-chave e contexto',
                    'position': {'x': 100, 'y': 200},
                    'config': {},
                    'tools_used': [],
                    'is_entry_point': True,
                    'is_final': False,
                    'metadata': {
                        'function': '_detect_intent_node',
                        'execution_type': 'synchronous',
                        'outputs': ['intent']
                    }
                },
                {
                    'id': 'route_decision',
                    'type': 'langgraph_node',
                    'label': 'Decisão de Roteamento',
                    'description': 'Decide qual caminho seguir baseado na intenção detectada. Usa bypass para análises completas ou react para respostas dinâmicas',
                    'position': {'x': 400, 'y': 200},
                    'config': {},
                    'tools_used': [],
                    'is_entry_point': False,
                    'is_final': False,
                    'metadata': {
                        'function': '_route_decision_node',
                        'execution_type': 'synchronous',
                        'outputs': ['route'],
                        'conditional': True
                    }
                },
                {
                    'id': 'bypass_analysis',
                    'type': 'langgraph_node',
                    'label': 'Análise Bypass',
                    'description': 'Executa sequência fixa de análises para intents que requerem análises completas da carteira',
                    'position': {'x': 700, 'y': 100},
                    'config': {},
                    'tools_used': [
                        'obter_carteira',
                        'analisar_adequacao',
                        'analisar_alinhamento_objetivos',
                        'analisar_diversificacao',
                        'recomendar_rebalanceamento',
                        'buscar_oportunidades',
                        'calcular_projecao'
                    ],
                    'is_entry_point': False,
                    'is_final': False,
                    'metadata': {
                        'function': '_bypass_analysis_node',
                        'execution_type': 'sequential',
                        'outputs': ['carteira', 'results'],
                        'tools_description': 'Usa diferentes combinações de tools dependendo da intenção: alinhamento_objetivos usa todas, adequacao usa 3, diversificacao usa 1, etc.'
                    }
                },
                {
                    'id': 'react_agent',
                    'type': 'langgraph_node',
                    'label': 'Agente ReAct',
                    'description': 'Agente reativo que decide dinamicamente quando usar tools baseado na conversa. Usa padrão ReAct (Reasoning + Acting)',
                    'position': {'x': 700, 'y': 300},
                    'config': {},
                    'tools_used': [
                        'obter_perfil',
                        'obter_carteira',
                        'analisar_adequacao',
                        'analisar_alinhamento_objetivos',
                        'analisar_diversificacao',
                        'recomendar_rebalanceamento',
                        'calcular_projecao',
                        'buscar_oportunidades'
                    ],
                    'is_entry_point': False,
                    'is_final': False,
                    'metadata': {
                        'function': '_react_agent_node',
                        'execution_type': 'iterative',
                        'outputs': ['response'],
                        'tools_description': 'Decide dinamicamente quais tools usar baseado na mensagem do usuário usando padrão ReAct'
                    }
                },
                {
                    'id': 'format_response',
                    'type': 'langgraph_node',
                    'label': 'Formatar Resposta',
                    'description': 'Formata a resposta final para o usuário usando LLM, incorporando resultados das análises ou do agente ReAct',
                    'position': {'x': 1000, 'y': 200},
                    'config': {},
                    'tools_used': [],
                    'is_entry_point': False,
                    'is_final': True,
                    'metadata': {
                        'function': '_format_response_node',
                        'execution_type': 'synchronous',
                        'outputs': ['response'],
                        'uses_llm': True
                    }
                }
            ],
            'edges': [
                {
                    'id': 'e1',
                    'source': 'detect_intent',
                    'target': 'route_decision',
                    'type': 'default',
                    'label': '',
                    'description': 'Fluxo direto após detecção de intenção'
                },
                {
                    'id': 'e2',
                    'source': 'route_decision',
                    'target': 'bypass_analysis',
                    'type': 'conditional',
                    'condition': 'bypass',
                    'label': 'bypass',
                    'description': 'Quando intent requer análise completa (ex: alinhamento_objetivos, adequacao)'
                },
                {
                    'id': 'e3',
                    'source': 'route_decision',
                    'target': 'react_agent',
                    'type': 'conditional',
                    'condition': 'react',
                    'label': 'react',
                    'description': 'Quando intent pode ser resolvido com agente ReAct dinâmico'
                },
                {
                    'id': 'e4',
                    'source': 'bypass_analysis',
                    'target': 'format_response',
                    'type': 'default',
                    'label': '',
                    'description': 'Resultados das análises são formatados'
                },
                {
                    'id': 'e5',
                    'source': 'react_agent',
                    'target': 'format_response',
                    'type': 'default',
                    'label': '',
                    'description': 'Resposta do ReAct é formatada'
                }
            ],
            'conditional_edges': [
                {
                    'source': 'route_decision',
                    'function': '_should_use_bypass',
                    'function_description': 'Retorna "bypass" se intent está na lista de bypass_intents, senão "react"',
                    'conditions': {
                        'bypass': {
                            'target': 'bypass_analysis',
                            'description': 'Quando intent requer análise completa da carteira',
                            'condition_logic': 'intent in ["analisar_alinhamento_objetivos", "analisar_adequacao", "analisar_diversificacao", "recomendar_rebalanceamento", "obter_carteira", "buscar_oportunidades", "calcular_projecao"]'
                        },
                        'react': {
                            'target': 'react_agent',
                            'description': 'Quando intent pode ser resolvido com agente ReAct',
                            'condition_logic': 'intent not in bypass_intents'
                        }
                    }
                }
            ],
            'execution_order': [
                'detect_intent',
                'route_decision',
                ['bypass_analysis', 'react_agent'],  # Um ou outro
                'format_response'
            ]
        }
    
    def get_graph_structure(self, custom_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retorna a estrutura do grafo atual.
        Se custom_config for fornecido, usa essa estrutura, senão retorna a padrão.
        """
        if custom_config and custom_config.get('graph_structure'):
            return custom_config['graph_structure']
        
        # Retornar estrutura padrão
        structure = self._get_default_graph_structure()
        
        # Adicionar informações sobre tools disponíveis
        structure['available_tools'] = [
            {
                'id': 'obter_perfil',
                'name': 'Obter Perfil',
                'description': 'Busca o perfil completo do cliente',
                'type': 'tool',
                'parameters': []
            },
            {
                'id': 'obter_carteira',
                'name': 'Obter Carteira',
                'description': 'Busca dados completos da carteira do cliente',
                'type': 'tool',
                'parameters': []
            },
            {
                'id': 'analisar_adequacao',
                'name': 'Analisar Adequação',
                'description': 'Analisa adequação da carteira ao perfil',
                'type': 'tool',
                'parameters': [
                    {'name': 'carteira', 'type': 'dict', 'required': True},
                    {'name': 'perfil', 'type': 'str', 'required': True}
                ]
            },
            {
                'id': 'analisar_alinhamento_objetivos',
                'name': 'Analisar Alinhamento',
                'description': 'Analisa alinhamento com objetivos',
                'type': 'tool',
                'parameters': [
                    {'name': 'carteira', 'type': 'dict', 'required': True},
                    {'name': 'objetivos', 'type': 'dict', 'required': True}
                ]
            },
            {
                'id': 'analisar_diversificacao',
                'name': 'Analisar Diversificação',
                'description': 'Analisa diversificação da carteira',
                'type': 'tool',
                'parameters': [
                    {'name': 'carteira', 'type': 'dict', 'required': True}
                ]
            },
            {
                'id': 'recomendar_rebalanceamento',
                'name': 'Recomendar Rebalanceamento',
                'description': 'Gera recomendações de rebalanceamento',
                'type': 'tool',
                'parameters': [
                    {'name': 'carteira', 'type': 'dict', 'required': True},
                    {'name': 'perfil', 'type': 'str', 'required': False}
                ]
            },
            {
                'id': 'calcular_projecao',
                'name': 'Calcular Projeção',
                'description': 'Calcula projeção de investimento',
                'type': 'tool',
                'parameters': [
                    {'name': 'valor_atual', 'type': 'float', 'required': True},
                    {'name': 'aporte_mensal', 'type': 'float', 'required': True},
                    {'name': 'prazo_anos', 'type': 'int', 'required': True},
                    {'name': 'rentabilidade_anual', 'type': 'float', 'required': False}
                ]
            },
            {
                'id': 'buscar_oportunidades',
                'name': 'Buscar Oportunidades',
                'description': 'Busca oportunidades de investimento',
                'type': 'tool',
                'parameters': [
                    {'name': 'perfil', 'type': 'str', 'required': True},
                    {'name': 'problemas', 'type': 'list', 'required': False}
                ]
            }
        ]
        
        # Adicionar tipos de nós customizados disponíveis
        structure['available_node_types'] = [
            {
                'id': 'prompt',
                'name': 'Prompt Customizado',
                'description': 'Nó para prompt customizado',
                'type': 'custom',
                'icon': '💬',
                'color': '#4CAF50'
            },
            {
                'id': 'response',
                'name': 'Resposta Pré-definida',
                'description': 'Nó para resposta pré-definida',
                'type': 'custom',
                'icon': '📝',
                'color': '#2196F3'
            },
            {
                'id': 'conditional',
                'name': 'Condição',
                'description': 'Nó de condição customizada',
                'type': 'custom',
                'icon': '🔀',
                'color': '#FF9800'
            },
            {
                'id': 'llm_call',
                'name': 'Chamada LLM',
                'description': 'Nó para chamada LLM customizada',
                'type': 'custom',
                'icon': '🤖',
                'color': '#9C27B0'
            }
        ]
        
        return structure
    
    def _build_graph_from_config(self, graph_structure: Dict[str, Any]):
        """
        Reconstrói o grafo LangGraph a partir de uma estrutura customizada.
        Por enquanto, mantém a estrutura padrão mas permite extensão futura.
        """
        if not LANGGRAPH_AVAILABLE:
            return None
        
        # Por enquanto, usar estrutura padrão
        # Em uma implementação completa, reconstruiria o grafo baseado na estrutura customizada
        # Isso requer mapear nós customizados para funções Python
        
        graph = StateGraph(AgentState)
        
        # Adicionar nós padrão (por enquanto)
        graph.add_node("detect_intent", self._detect_intent_node)
        graph.add_node("route_decision", self._route_decision_node)
        graph.add_node("bypass_analysis", self._bypass_analysis_node)
        graph.add_node("react_agent", self._react_agent_node)
        graph.add_node("format_response", self._format_response_node)
        
        # Definir entry point
        entry_point = graph_structure.get('entry_point', 'detect_intent')
        graph.set_entry_point(entry_point)
        
        # Adicionar edges baseado na estrutura
        for edge in graph_structure.get('edges', []):
            if edge['type'] == 'conditional':
                # Conditional edges precisam de tratamento especial
                # Por enquanto, usar a lógica padrão
                pass
            else:
                # Edge simples
                try:
                    graph.add_edge(edge['source'], edge['target'])
                except Exception as e:
                    print(f"[LangGraphAgent] Erro ao adicionar edge {edge['source']} -> {edge['target']}: {e}")
        
        # Adicionar conditional edges padrão se necessário
        if any(e['type'] == 'conditional' for e in graph_structure.get('edges', [])):
            graph.add_conditional_edges(
                "route_decision",
                self._should_use_bypass,
                {
                    "bypass": "bypass_analysis",
                    "react": "react_agent"
                }
            )
        
        # Garantir que format_response está conectado
        try:
            graph.add_edge("bypass_analysis", "format_response")
            graph.add_edge("react_agent", "format_response")
            graph.add_edge("format_response", END)
        except:
            pass  # Já pode estar conectado
        
        # Compilar grafo com checkpointer apropriado
        checkpointer = self._get_checkpointer()
        return graph.compile(checkpointer=checkpointer)
    
    def _detect_intent_node(self, state: AgentState) -> AgentState:
        """Nó que detecta a intenção da mensagem"""
        start_time = time.time()
        trace_id = state.get("trace_id")
        
        message = state.get("message", "")
        context = state.get("context", [])
        
        # Verificar se é uma confirmação curta (ok, sim, etc) e reutilizar intent do contexto
        message_lower = message.lower().strip()
        short_confirmations = ['ok', 'sim', 'tudo bem', 'pode ser', 'pode', 'claro', 'entendi', 'beleza', 'tá bom']
        
        if message_lower in short_confirmations and context:
            # Procurar a última mensagem do usuário no contexto que não seja confirmação
            last_user_intent = None
            for i in range(len(context) - 1, -1, -1):
                msg = context[i]
                if msg.get('role') == 'user':
                    last_user_msg = msg.get('content', '').lower().strip()
                    # Se não for outra confirmação curta, detectar intent dessa mensagem
                    if last_user_msg not in short_confirmations:
                        last_user_intent = self._detect_intent(msg.get('content', ''))
                        break
            
            if last_user_intent:
                intent = last_user_intent
                if trace_id:
                    self.traceability.add_event(
                        trace_id,
                        'context_reuse',
                        {
                            'message': message,
                            'reused_intent': intent,
                            'source_message': context[i].get('content', '')[:100] if i < len(context) else 'N/A'
                        }
                    )
            else:
                intent = self._detect_intent(message)
        else:
            intent = self._detect_intent(message)
        
        state["intent"] = intent
        duration_ms = (time.time() - start_time) * 1000
        
        # Registrar no trace
        if trace_id:
            self.traceability.set_intent(trace_id, intent)
            self.traceability.add_graph_step(
                trace_id,
                "detect_intent",
                {"message": message[:200], "context_length": len(context) if context else 0},
                {"intent": intent},
                duration_ms
            )
            # Registrar edge de detect_intent para route_decision
            self.traceability.add_edge(trace_id, "detect_intent", "route_decision", None)
            # Adicionar evento de detecção de intenção
            self.traceability.add_event(
                trace_id,
                'intent_detection',
                {
                    'message': message[:200],
                    'intent': intent,
                    'method': 'keyword_matching',
                    'duration_ms': duration_ms
                },
                {'context_length': len(context) if context else 0}
            )
        
        return state
    
    def _route_decision_node(self, state: AgentState) -> AgentState:
        """Nó que decide qual caminho seguir"""
        start_time = time.time()
        trace_id = state.get("trace_id")
        intent = state.get("intent")
        
        # Intenções que usam bypass (sequência fixa)
        # Nota: Todas as intenções agora usam LLM para formatação, mas algumas precisam de análises prévias
        bypass_intents = [
            "analisar_alinhamento_objetivos",
            "analisar_adequacao",
            "analisar_diversificacao",
            "recomendar_rebalanceamento",
            "obter_carteira",
            "buscar_oportunidades",
            "calcular_projecao"
        ]
        
        route = "bypass" if intent in bypass_intents else "react"
        decision_rationale = f"Intent '{intent}' maps to {'bypass' if intent in bypass_intents else 'react'} route"
        state["route"] = route
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Registrar no trace
        if trace_id:
            self.traceability.set_route(trace_id, route)
            self.traceability.add_graph_step(
                trace_id,
                "route_decision",
                {"intent": intent},
                {"route": route, "rationale": decision_rationale},
                duration_ms
            )
            # A edge de route_decision para bypass_analysis ou react_agent será registrada
            # nos respectivos nós quando eles forem executados
            # Adicionar evento de decisão de rota
            self.traceability.add_event(
                trace_id,
                'route_decision',
                {
                    'intent': intent,
                    'route': route,
                    'rationale': decision_rationale,
                    'bypass_intents': bypass_intents,
                    'duration_ms': duration_ms
                }
            )
        
        return state
    
    def _should_use_bypass(self, state: AgentState) -> str:
        """Função de decisão para conditional edge"""
        route = state.get("route", "react")
        return route  # Retorna "bypass" ou "react"
    
    def _bypass_analysis_node(self, state: AgentState) -> AgentState:
        """Nó que executa sequência fixa de análises (bypass)"""
        start_time = time.time()
        trace_id = state.get("trace_id")
        intent = state.get("intent")
        
        # Obter perfil do cliente usando obter_perfil
        tool_start = time.time()
        perfil_data = obter_perfil()
        tool_duration = (time.time() - tool_start) * 1000
        
        if hasattr(perfil_data, 'model_dump'):
            perfil_dict = perfil_data.model_dump()
        elif hasattr(perfil_data, 'dict'):
            perfil_dict = perfil_data.dict()
        else:
            perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
        
        # Extrair perfil de investidor (fallback para 'conservador' se não disponível)
        perfil_investidor = perfil_dict.get('perfilInvestidor', 'conservador').lower()
        
        # Registrar tool call do perfil
        if trace_id:
            self.traceability.add_tool_call(
                trace_id, 'obter_perfil',
                {},
                {'perfilInvestidor': perfil_investidor, 'nome': perfil_dict.get('nome', 'N/A')},
                tool_duration
            )
        
        # Obter PERFIL_JOAO completo para análises que precisam do objeto completo
        try:
            from app.routes.cliente import PERFIL_JOAO
        except:
            PERFIL_JOAO = perfil_dict  # Usar perfil obtido como fallback
        
        # Obter carteira
        tool_start = time.time()
        carteira_data = obter_carteira()
        tool_duration = (time.time() - tool_start) * 1000
        
        if hasattr(carteira_data, 'model_dump'):
            carteira_dict = carteira_data.model_dump()
        elif hasattr(carteira_data, 'dict'):
            carteira_dict = carteira_data.dict()
        else:
            carteira_dict = carteira_data if isinstance(carteira_data, dict) else {}
        
        state["carteira"] = carteira_dict
        state["perfil"] = perfil_dict  # Armazenar perfil no state para uso posterior
        state["tools_used"] = ["obter_perfil", "obter_carteira"]
        results = {}
        
        # Registrar tool call
        if trace_id:
            self.traceability.add_tool_call(
                trace_id, 'obter_carteira',
                {},
                {'carteira_keys': list(carteira_dict.keys()), 'total': carteira_dict.get('total', 0)},
                tool_duration
            )
        
        # Executar análises baseado na intenção
        if intent == "analisar_alinhamento_objetivos":
            tool_start = time.time()
            results["adequacao"] = analisar_adequacao(carteira_dict, perfil_investidor)
            tool_duration = (time.time() - tool_start) * 1000
            adeq_dict = results["adequacao"].model_dump() if hasattr(results["adequacao"], 'model_dump') else (results["adequacao"].dict() if hasattr(results["adequacao"], 'dict') else results["adequacao"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_adequacao', {'perfil': perfil_investidor}, {'score': adeq_dict.get('score', 0)}, tool_duration)
            
            tool_start = time.time()
            results["alinhamento"] = analisar_alinhamento_objetivos(carteira_dict, PERFIL_JOAO)
            tool_duration = (time.time() - tool_start) * 1000
            alinh_dict = results["alinhamento"].model_dump() if hasattr(results["alinhamento"], 'model_dump') else (results["alinhamento"].dict() if hasattr(results["alinhamento"], 'dict') else results["alinhamento"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_alinhamento_objetivos', {'perfil': perfil_investidor}, {'score_geral': alinh_dict.get('score_geral', 0)}, tool_duration)
            
            tool_start = time.time()
            results["diversificacao"] = analisar_diversificacao(carteira_dict)
            tool_duration = (time.time() - tool_start) * 1000
            div_dict = results["diversificacao"].model_dump() if hasattr(results["diversificacao"], 'model_dump') else (results["diversificacao"].dict() if hasattr(results["diversificacao"], 'dict') else results["diversificacao"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_diversificacao', {}, {'score_diversificacao': div_dict.get('score_diversificacao', 0)}, tool_duration)
            
            tool_start = time.time()
            results["rebalanceamento"] = recomendar_rebalanceamento(carteira_dict, perfil_investidor)
            tool_duration = (time.time() - tool_start) * 1000
            reb_dict = results["rebalanceamento"].model_dump() if hasattr(results["rebalanceamento"], 'model_dump') else (results["rebalanceamento"].dict() if hasattr(results["rebalanceamento"], 'dict') else results["rebalanceamento"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'recomendar_rebalanceamento', {'perfil': perfil_investidor}, {'necessario': reb_dict.get('necessario', False)}, tool_duration)
            
            state["tools_used"].extend([
                "obter_perfil", "analisar_adequacao", "analisar_alinhamento_objetivos",
                "analisar_diversificacao", "recomendar_rebalanceamento"
            ])
        elif intent == "analisar_adequacao" or intent == "recomendar_rebalanceamento":
            tool_start = time.time()
            results["adequacao"] = analisar_adequacao(carteira_dict, perfil_investidor)
            tool_duration = (time.time() - tool_start) * 1000
            adeq_dict = results["adequacao"].model_dump() if hasattr(results["adequacao"], 'model_dump') else (results["adequacao"].dict() if hasattr(results["adequacao"], 'dict') else results["adequacao"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_adequacao', {'perfil': perfil_investidor}, {'score': adeq_dict.get('score', 0)}, tool_duration)
            
            tool_start = time.time()
            results["diversificacao"] = analisar_diversificacao(carteira_dict)
            tool_duration = (time.time() - tool_start) * 1000
            div_dict = results["diversificacao"].model_dump() if hasattr(results["diversificacao"], 'model_dump') else (results["diversificacao"].dict() if hasattr(results["diversificacao"], 'dict') else results["diversificacao"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_diversificacao', {}, {'score_diversificacao': div_dict.get('score_diversificacao', 0)}, tool_duration)
            
            tool_start = time.time()
            results["rebalanceamento"] = recomendar_rebalanceamento(carteira_dict, perfil_investidor)
            tool_duration = (time.time() - tool_start) * 1000
            reb_dict = results["rebalanceamento"].model_dump() if hasattr(results["rebalanceamento"], 'model_dump') else (results["rebalanceamento"].dict() if hasattr(results["rebalanceamento"], 'dict') else results["rebalanceamento"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'recomendar_rebalanceamento', {'perfil': perfil_investidor}, {'necessario': reb_dict.get('necessario', False)}, tool_duration)
            
            state["tools_used"].extend([
                "obter_perfil", "analisar_adequacao", "analisar_diversificacao", "recomendar_rebalanceamento"
            ])
        elif intent == "analisar_diversificacao":
            tool_start = time.time()
            results["diversificacao"] = analisar_diversificacao(carteira_dict)
            tool_duration = (time.time() - tool_start) * 1000
            div_dict = results["diversificacao"].model_dump() if hasattr(results["diversificacao"], 'model_dump') else (results["diversificacao"].dict() if hasattr(results["diversificacao"], 'dict') else results["diversificacao"])
            if trace_id:
                self.traceability.add_tool_call(trace_id, 'analisar_diversificacao', {}, {'score_diversificacao': div_dict.get('score_diversificacao', 0)}, tool_duration)
            state["tools_used"].append("analisar_diversificacao")
        elif intent == "buscar_oportunidades":
            # Obter oportunidades baseado no perfil e problemas da carteira
            tool_start = time.time()
            alertas = carteira_dict.get('adequacaoPerfil', {}).get('alertas', [])
            problemas_list = [a.get('mensagem', '') for a in alertas if a.get('mensagem')]
            oportunidades = buscar_oportunidades(perfil_investidor, problemas_list)
            tool_duration = (time.time() - tool_start) * 1000
            
            # Converter para lista de dicts
            ops_list = []
            for op in oportunidades:
                if hasattr(op, 'model_dump'):
                    ops_list.append(op.model_dump())
                elif hasattr(op, 'dict'):
                    ops_list.append(op.dict())
                else:
                    ops_list.append(op if isinstance(op, dict) else {})
            
            results["oportunidades"] = ops_list
            state["tools_used"].append("buscar_oportunidades")
            
            if trace_id:
                self.traceability.add_tool_call(
                    trace_id, 'buscar_oportunidades',
                    {'perfil': perfil_investidor, 'problemas': problemas_list},
                    {'oportunidades_count': len(ops_list)},
                    tool_duration
                )
            state["tools_used"].extend(["obter_perfil", "buscar_oportunidades"])
        elif intent == "calcular_projecao":
            # Calcular projeção baseada nos objetivos
            tool_start = time.time()
            projecao = calcular_projecao(carteira=carteira_dict, perfil=PERFIL_JOAO)
            tool_duration = (time.time() - tool_start) * 1000
            
            if hasattr(projecao, 'model_dump'):
                proj_dict = projecao.model_dump()
            elif hasattr(projecao, 'dict'):
                proj_dict = projecao.dict()
            else:
                proj_dict = projecao if isinstance(projecao, dict) else {}
            
            results["projecao"] = proj_dict
            state["tools_used"].extend(["obter_perfil", "calcular_projecao"])
            
            if trace_id:
                self.traceability.add_tool_call(
                    trace_id, 'calcular_projecao',
                    {'perfil': perfil_investidor},
                    {'projecao_keys': list(proj_dict.keys())},
                    tool_duration
                )
        # Para "obter_carteira", já temos a carteira
        
        state["results"] = results
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Registrar no trace
        if trace_id:
            self.traceability.add_graph_step(
                trace_id,
                "bypass_analysis",
                {"intent": intent, "carteira_keys": list(carteira_dict.keys())},
                {"results_keys": list(results.keys()), "tools_used": state["tools_used"]},
                duration_ms
            )
            self.traceability.add_edge(trace_id, "route_decision", "bypass_analysis", "bypass")
            # Adicionar evento de bypass analysis
            self.traceability.add_event(
                trace_id,
                'bypass_analysis_complete',
                {
                    'intent': intent,
                    'tools_used': state["tools_used"],
                    'results_keys': list(results.keys()),
                    'duration_ms': duration_ms
                }
            )
        
        return state
    
    def _react_agent_node(self, state: AgentState) -> AgentState:
        """Nó que executa agente ReAct via LangGraph usando AgentService com tools"""
        start_time = time.time()
        trace_id = state.get("trace_id")
        message = state.get("message", "")
        context = state.get("context", [])
        intent = state.get("intent")
        
        # Passo 2: Bypass direto para perfil simples
        if intent == "qual_perfil_simples":
            print(f"[LangGraphAgent] Intent 'qual_perfil_simples' detectado - chamando tool diretamente")
            try:
                # Chamar tool diretamente
                tool_start = time.time()
                perfil_data = obter_perfil()
                tool_duration = (time.time() - tool_start) * 1000
                
                # Converter para dict
                if hasattr(perfil_data, 'model_dump'):
                    perfil_dict = perfil_data.model_dump()
                elif hasattr(perfil_data, 'dict'):
                    perfil_dict = perfil_data.dict()
                else:
                    perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                
                # Registrar tool call
                if trace_id:
                    self.traceability.add_tool_call(
                        trace_id,
                        'obter_perfil',
                        {},
                        {'perfilInvestidor': perfil_dict.get('perfilInvestidor', 'N/A'), 'nome': perfil_dict.get('nome', 'N/A')},
                        tool_duration
                    )
                
                # Formatar resposta usando LLM com resultado da tool
                perfil_investidor = perfil_dict.get('perfilInvestidor', 'conservador').upper()
                nome = perfil_dict.get('nome', 'João')
                
                # Usar LLM para formatar resposta de forma natural
                if self.llm:
                    system_prompt = (
                        "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                        "Responda de forma direta, conversacional e empática."
                    )
                    user_prompt = (
                        f"O cliente {nome} perguntou: '{message}'. "
                        f"Você consultou o perfil e descobriu que o perfil de investidor é {perfil_investidor}. "
                        f"Responda de forma DIRETA e CONCISA, apenas informando o perfil. "
                        f"Não faça análises adicionais, apenas informe: 'Seu perfil de investidor é {perfil_investidor}.'"
                    )
                    
                    # SystemMessage e HumanMessage já estão importados no topo do arquivo
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_prompt)
                    ]
                    
                    try:
                        response = self.llm.invoke(messages)
                        response_text = response.content if hasattr(response, 'content') else str(response)
                    except Exception as e:
                        print(f"[LangGraphAgent] Erro ao formatar com LLM: {e}")
                        response_text = f"Seu perfil de investidor é {perfil_investidor}."
                else:
                    response_text = f"Seu perfil de investidor é {perfil_investidor}."
                
                state["response"] = response_text
                state["tools_used"] = ["obter_perfil"]
                
                # Registrar resposta raw
                if trace_id:
                    self.traceability.add_raw_response(trace_id, response_text)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Registrar no trace
                if trace_id:
                    self.traceability.add_graph_step(
                        trace_id,
                        "react_agent",
                        {"message": message[:200], "intent": intent, "bypass": True},
                        {"response_length": len(response_text), "tools_used": ["obter_perfil"]},
                        duration_ms
                    )
                    self.traceability.add_edge(trace_id, "route_decision", "react_agent", "react")
                
                return state
            except Exception as e:
                print(f"[LangGraphAgent] Erro no bypass de perfil: {e}")
                import traceback
                traceback.print_exc()
                # Continuar para o fluxo normal do agente
        
        # Usar AgentService para obter agente com tools
        try:
            from app.services.agent_service import AgentService
            agent_service = AgentService()
            react_agent = agent_service._build_react_agent()
            
            if react_agent:
                # Preparar input com contexto
                input_text = message
                if context:
                    # Adicionar contexto recente ao input
                    context_text = "\n\nContexto da conversa anterior:\n"
                    for msg in context[-3:]:  # Últimas 3 mensagens
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        if role == 'user':
                            context_text += f"Cliente: {content}\n"
                        elif role == 'assistant':
                            context_text += f"Assessor: {content}\n"
                    input_text = context_text + f"\nPergunta atual: {message}"
                
                # Registrar prompt antes de executar
                if trace_id:
                    self.traceability.add_raw_prompt(trace_id, input_text)
                
                # Executar agente e capturar tool calls
                tools_used = []
                
                try:
                    # Executar agente com return_intermediate_steps se disponível
                    if hasattr(react_agent, 'invoke'):
                        # Tentar obter intermediate_steps
                        try:
                            # AgentExecutor pode ter return_intermediate_steps como parâmetro
                            response = react_agent.invoke({"input": input_text}, return_only_outputs=False)
                        except:
                            response = react_agent.invoke({"input": input_text})
                    else:
                        response = react_agent.invoke({"input": input_text})
                    
                    # DEBUG: Log estrutura da resposta
                    print(f"[DEBUG] Response type: {type(response)}")
                    if isinstance(response, dict):
                        print(f"[DEBUG] Response keys: {list(response.keys())}")
                        print(f"[DEBUG] Response full (truncated): {str(response)[:500]}")
                    else:
                        print(f"[DEBUG] Response (not dict): {str(response)[:500]}")
                    
                    response_text = response.get("output", "") if isinstance(response, dict) else str(response)
                    
                    # Verificar se há intermediate_steps no resultado ou no agente
                    intermediate_steps = None
                    if isinstance(response, dict):
                        # Tentar diferentes formas de acessar intermediate_steps
                        if "intermediate_steps" in response:
                            intermediate_steps = response["intermediate_steps"]
                            print(f"[DEBUG] Found intermediate_steps in response: {len(intermediate_steps) if intermediate_steps else 0} steps")
                        elif "intermediate_steps" in response.get("output", {}):
                            intermediate_steps = response["output"]["intermediate_steps"]
                            print(f"[DEBUG] Found intermediate_steps in response.output")
                        # Verificar se está em outro formato
                        for key in response.keys():
                            if "step" in key.lower() or "intermediate" in key.lower():
                                print(f"[DEBUG] Found potential steps key: {key}")
                                potential_steps = response.get(key)
                                if potential_steps and isinstance(potential_steps, list):
                                    intermediate_steps = potential_steps
                                    print(f"[DEBUG] Using {key} as intermediate_steps")
                                    break
                    
                    # Verificar no agente também
                    if not intermediate_steps:
                        if hasattr(react_agent, 'agent') and hasattr(react_agent.agent, 'intermediate_steps'):
                            intermediate_steps = react_agent.agent.intermediate_steps
                            print(f"[DEBUG] Found intermediate_steps in agent.agent")
                        elif hasattr(react_agent, 'intermediate_steps'):
                            intermediate_steps = react_agent.intermediate_steps
                            print(f"[DEBUG] Found intermediate_steps in agent")
                    
                    if not intermediate_steps:
                        print(f"[DEBUG] No intermediate_steps found in response or agent")
                    
                    # Processar intermediate_steps para capturar tool calls
                    if intermediate_steps:
                        for step in intermediate_steps:
                            if len(step) >= 2:
                                tool_action = step[0]
                                tool_result = step[1]
                                
                                # Extrair nome da tool
                                tool_name = None
                                if hasattr(tool_action, 'tool'):
                                    tool_name = tool_action.tool
                                elif hasattr(tool_action, 'name'):
                                    tool_name = tool_action.name
                                elif isinstance(tool_action, dict):
                                    tool_name = tool_action.get('tool', tool_action.get('name'))
                                elif isinstance(tool_action, str):
                                    tool_name = tool_action
                                else:
                                    # Tentar extrair do string representation
                                    tool_str = str(tool_action)
                                    if 'tool=' in tool_str:
                                        tool_name = tool_str.split('tool=')[1].split(',')[0].strip("'\"")
                                    elif 'name=' in tool_str:
                                        tool_name = tool_str.split('name=')[1].split(',')[0].strip("'\"")
                                
                                if tool_name and tool_name not in tools_used:
                                    tools_used.append(tool_name)
                                    if trace_id:
                                        # Extrair input da tool
                                        tool_input = {}
                                        if hasattr(tool_action, 'tool_input'):
                                            tool_input_raw = tool_action.tool_input
                                            if isinstance(tool_input_raw, dict):
                                                tool_input = tool_input_raw
                                            else:
                                                tool_input = {"input": str(tool_input_raw)[:200]}
                                        elif isinstance(tool_action, dict):
                                            tool_input = tool_action.get('tool_input', {})
                                        
                                        # Extrair output da tool
                                        tool_output = {"output": str(tool_result)[:500]} if tool_result else {}
                                        
                                        self.traceability.add_tool_call(
                                            trace_id,
                                            tool_name,
                                            tool_input,
                                            tool_output,
                                            None
                                        )
                                        print(f"[LangGraphAgent] Tool call registrada: {tool_name}")
                    
                    # Passo 4: Verificação de fallback
                    # Se tools_used está vazio e a resposta não contém informações específicas do perfil
                    if not tools_used and intent == "qual_perfil_simples":
                        print(f"[LangGraphAgent] Fallback: tools_used vazio para perfil simples, chamando tool manualmente")
                        # Verificar se resposta contém perfil específico
                        perfil_keywords = ['conservador', 'moderado', 'arrojado', 'agressivo', 'defensivo']
                        resposta_contem_perfil = any(kw in response_text.lower() for kw in perfil_keywords)
                        
                        if not resposta_contem_perfil:
                            # Chamar tool manualmente
                            try:
                                tool_start = time.time()
                                perfil_data = obter_perfil()
                                tool_duration = (time.time() - tool_start) * 1000
                                
                                if hasattr(perfil_data, 'model_dump'):
                                    perfil_dict = perfil_data.model_dump()
                                elif hasattr(perfil_data, 'dict'):
                                    perfil_dict = perfil_data.dict()
                                else:
                                    perfil_dict = perfil_data if isinstance(perfil_data, dict) else {}
                                
                                perfil_investidor = perfil_dict.get('perfilInvestidor', 'conservador').upper()
                                
                                # Registrar tool call
                                if trace_id:
                                    self.traceability.add_tool_call(
                                        trace_id,
                                        'obter_perfil',
                                        {},
                                        {'perfilInvestidor': perfil_investidor},
                                        tool_duration
                                    )
                                
                                # Reformatar resposta
                                response_text = f"Seu perfil de investidor é {perfil_investidor}."
                                tools_used.append("obter_perfil")
                                print(f"[LangGraphAgent] Fallback: tool chamada e resposta reformatada")
                            except Exception as fallback_error:
                                print(f"[LangGraphAgent] Erro no fallback: {fallback_error}")
                    
                    state["response"] = response_text
                    state["tools_used"] = tools_used
                    
                    # Registrar resposta raw
                    if trace_id:
                        self.traceability.add_raw_response(trace_id, response_text)
                except Exception as agent_error:
                    print(f"[LangGraphAgent] Erro ao executar agente: {agent_error}")
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                # Fallback: usar LLM diretamente
                system_prompt = (
                    "⚠️ PRIORIDADE ABSOLUTA: Responda DIRETAMENTE à pergunta do usuário. "
                    "O contexto fornecido (dados da carteira, análises) é apenas informação adicional que você PODE usar se for relevante para responder a pergunta específica. "
                    "Se a pergunta for simples, responda de forma simples e direta, IGNORANDO o contexto se não for necessário. "
                    "A pergunta do usuário é sempre a prioridade - o contexto é opcional e só deve ser usado quando realmente ajudar a responder a pergunta.\n\n"
                    "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                    "Sua abordagem é consultiva, empática e educativa, similar ao padrão CFP (Certified Financial Planner).\n\n"
                    "⚠️ IMPORTANTE: Você está conversando com JOÃO e TEM ACESSO aos dados dele através das ferramentas quando disponíveis.\n\n"
                    "⚠️ PERFIL DE INVESTIDOR: Para saber o perfil do cliente, você DEVE usar a ferramenta obter_perfil. "
                    "NÃO assuma o perfil - sempre consulte usando obter_perfil quando precisar dessa informação.\n\n"
                    "Diretrizes de Conversação:\n"
                    "- Seja conversacional, natural e empático\n"
                    "- Use linguagem acessível, evite jargões técnicos desnecessários\n"
                    "- Eduque o cliente sobre conceitos financeiros de forma clara\n"
                    "- SEMPRE tente responder a pergunta do cliente, mesmo que não tenha todos os dados\n"
                    "- Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas\n\n"
                    "📌 REGRA IMPORTANTE: Se o cliente perguntar 'qual é o meu perfil de investidor' ou 'qual meu perfil' ou variações similares, "
                    "você DEVE usar a ferramenta obter_perfil para obter essa informação e responder de forma DIRETA e CONCISA com o perfil retornado pela ferramenta. "
                    "NÃO faça análises completas da carteira para essa pergunta simples - apenas informe o perfil."
                )
                
                messages = [SystemMessage(content=system_prompt)]
                if context:
                    for msg in context[-6:]:
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        if role == 'user':
                            messages.append(HumanMessage(content=content))
                        elif role == 'assistant':
                            messages.append(AIMessage(content=content))
                
                messages.append(HumanMessage(content=message))
                
                if trace_id:
                    self.traceability.add_raw_prompt(trace_id, message, system_prompt)
                
                response = self.llm.invoke(messages)
                response_text = response.content if hasattr(response, 'content') else str(response)
                state["response"] = response_text
                
                if trace_id:
                    self.traceability.add_raw_response(trace_id, response_text)
        except Exception as e:
            print(f"[LangGraphAgent] Erro no ReAct: {e}")
            import traceback
            tb_str = traceback.format_exc()
            traceback.print_exc()
            
            # Mensagem de erro mais informativa
            error_type = type(e).__name__
            error_msg = (
                f"Desculpe, ocorreu um erro ao processar sua mensagem ({error_type}). "
                "Por favor, tente reformular sua pergunta ou tente novamente mais tarde. "
                "Se o problema persistir, entre em contato com o suporte técnico."
            )
            state["response"] = error_msg
            
            # Registrar erro
            if trace_id:
                try:
                    message_preview = message[:200] if message else 'N/A'
                except:
                    message_preview = 'N/A'
                
                self.traceability.add_error(
                    trace_id,
                    'ReactAgentException',
                    str(e),
                    {'node': 'react_agent', 'error_type': error_type, 'message': message_preview},
                    tb_str
                )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Registrar no trace
        if trace_id:
            try:
                message_preview = message[:200] if message else 'N/A'
                context_length = len(context) if context else 0
            except:
                message_preview = 'N/A'
                context_length = 0
            
            self.traceability.add_graph_step(
                trace_id,
                "react_agent",
                {"message": message_preview, "context_length": context_length},
                {"response_length": len(state.get("response", ""))},
                duration_ms
            )
            self.traceability.add_edge(trace_id, "route_decision", "react_agent", "react")
            # Adicionar evento de execução do ReAct
            self.traceability.add_event(
                trace_id,
                'react_agent_execution',
                {
                    'context_length': len(context),
                    'response_length': len(state.get("response", "")),
                    'duration_ms': duration_ms,
                    'error': None
                }
            )
        
        return state
    
    def _format_with_llm(self, message: str, carteira: Optional[Dict], results: Dict, intent: Optional[str], context: Optional[List], trace_id: Optional[str]) -> str:
        """Formata resposta usando LLM com dados da carteira e resultados das análises"""
        if not self.llm:
            return (
                "Desculpe, o serviço de IA não está disponível no momento. "
                "Isso pode ocorrer se a chave da API não estiver configurada ou se houver um problema temporário. "
                "Por favor, verifique as configurações ou tente novamente mais tarde. "
                "Se o problema persistir, entre em contato com o suporte técnico."
            )
        
        try:
            # Verificar se é pergunta simples sobre perfil
            message_lower = message.lower().strip()
            is_simple_profile_question = any(kw in message_lower for kw in [
                'qual é o meu perfil', 'qual é meu perfil', 'qual meu perfil',
                'meu perfil de investidor', 'qual meu perfil de investidor',
                'qual o meu perfil', 'meu perfil é', 'qual perfil'
            ]) and not any(kw in message_lower for kw in ['adequada', 'adequado', 'está adequada', 'adequação', 'carteira', 'minha carteira'])
            
            # Preparar system prompt
            system_prompt = (
                "⚠️ PRIORIDADE ABSOLUTA: Responda DIRETAMENTE à pergunta do usuário. "
                "O contexto fornecido (dados da carteira, análises) é apenas informação adicional que você PODE usar se for relevante para responder a pergunta específica. "
                "Se a pergunta for simples, responda de forma simples e direta, IGNORANDO o contexto se não for necessário. "
                "A pergunta do usuário é sempre a prioridade - o contexto é opcional e só deve ser usado quando realmente ajudar a responder a pergunta.\n\n"
                "Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter. "
                "Responda de forma consultiva e no estilo CFP, usando os dados da carteira fornecidos quando disponíveis. "
                "IMPORTANTE: Para saber o perfil de investidor do cliente, você DEVE usar a ferramenta obter_perfil. "
                "NÃO assuma o perfil - sempre consulte usando obter_perfil quando precisar dessa informação. "
                "\n\n📌 REGRA IMPORTANTE: Se o cliente perguntar APENAS 'qual é o meu perfil de investidor' ou 'qual meu perfil' ou variações similares, "
                "você DEVE usar a ferramenta obter_perfil para obter essa informação e responder de forma DIRETA e CONCISA com o perfil retornado pela ferramenta. "
                "NÃO faça análises completas da carteira para essa pergunta simples - apenas informe o perfil. "
                "Apenas se o cliente perguntar sobre adequação, alinhamento ou problemas da carteira, aí sim faça análises detalhadas. "
                "\n\n⚠️ REGRA CRÍTICA: Você DEVE fazer análises proativas. NÃO peça ao cliente para fazer verificações. "
                "Você TEM os dados da carteira e DEVE analisar:\n"
                "- Adequação do perfil de risco (renda variável deve ser 10-15%, liquidez 15-20% para conservador)\n"
                "- Alinhamento com objetivos de curto/médio/longo prazo (avaliar alocação por horizonte temporal)\n"
                "- Diversificação (verificar concentração por classe e por ativo)\n"
                "- Necessidade de rebalanceamento (propor ajustes específicos quando necessário)\n"
                "\nPara perguntas sobre adequação, alinhamento, diversificação ou ajustes, você DEVE:\n"
                "1. Analisar os dados fornecidos\n"
                "2. Identificar problemas específicos\n"
                "3. Propor ajustes concretos com valores\n"
                "4. Explicar o impacto esperado\n"
                "\nSempre tente responder a pergunta do cliente, mesmo que não tenha todos os dados. "
                "Se faltarem dados específicos, forneça orientações gerais baseadas em boas práticas e pergunte quais informações adicionais seriam úteis. "
                "A resposta precisa ter QUEBRAS DE LINHA claras e leitura fácil. "
                "Use títulos curtos e listas com um item por linha. "
                "Use o contexto da conversa anterior quando relevante para entender referências do cliente. "
                "Sempre termine com próximos passos práticos ou perguntas para obter mais informações quando necessário."
            )
            
            # Preparar user content com dados
            user_content = f"Pergunta do cliente: {message}\n\n"
            
            # Só incluir dados da carteira se NÃO for pergunta simples sobre perfil
            if carteira and not is_simple_profile_question:
                total = float(carteira.get('total', 0) or 0)
                dinheiro_parado = float(carteira.get('dinheiroParado', 0) or 0)
                total_carteira = total + dinheiro_parado
                distribuicao = carteira.get('distribuicaoPercentual', {})
                investimentos = carteira.get('investimentos', [])
                
                user_content += f"Dados da carteira (João):\n"
                user_content += f"- Total da carteira (investido + parado): R$ {total_carteira:,.2f}\n"
                user_content += f"- Patrimônio investido: R$ {total:,.2f}\n"
                user_content += f"- Dinheiro parado: R$ {dinheiro_parado:,.2f}\n"
                user_content += f"- Distribuição:\n"
                user_content += f"  • Renda Fixa: {distribuicao.get('rendaFixa', 0):.1f}%\n"
                user_content += f"  • Renda Variável: {distribuicao.get('rendaVariavel', 0):.1f}%\n"
                user_content += f"  • Liquidez: {distribuicao.get('liquidez', 0):.1f}%\n"
                
                if investimentos:
                    user_content += f"\nInvestimentos:\n"
                    for inv in investimentos:
                        user_content += f"- {inv.get('nome', 'N/A')}: R$ {inv.get('valor', 0):,.2f} ({inv.get('tipo', 'N/A')})\n"
                
                alertas = carteira.get('adequacaoPerfil', {}).get('alertas', [])
                if alertas:
                    user_content += f"\nAlertas:\n"
                    for alerta in alertas:
                        user_content += f"- {alerta.get('mensagem', '')}\n"
            
            # Adicionar resultados das análises se disponíveis (só se NÃO for pergunta simples sobre perfil)
            if results and not is_simple_profile_question:
                user_content += "\n\nResultados das análises realizadas:\n"
                
                if "adequacao" in results:
                    adeq = results["adequacao"]
                    if hasattr(adeq, 'model_dump'):
                        adeq_dict = adeq.model_dump()
                    elif hasattr(adeq, 'dict'):
                        adeq_dict = adeq.dict()
                    else:
                        adeq_dict = adeq
                    user_content += f"\nAdequação ao Perfil:\n"
                    user_content += f"- Score: {adeq_dict.get('score', 0)}/100\n"
                    if adeq_dict.get('problemas'):
                        user_content += f"- Problemas: {', '.join(adeq_dict.get('problemas', []))}\n"
                    if adeq_dict.get('recomendacoes'):
                        user_content += f"- Recomendações: {', '.join(adeq_dict.get('recomendacoes', []))}\n"
                
                if "alinhamento" in results:
                    alinh = results["alinhamento"]
                    if hasattr(alinh, 'model_dump'):
                        alinh_dict = alinh.model_dump()
                    elif hasattr(alinh, 'dict'):
                        alinh_dict = alinh.dict()
                    else:
                        alinh_dict = alinh
                    user_content += f"\nAlinhamento com Objetivos:\n"
                    user_content += f"- Score Geral: {alinh_dict.get('score_geral', 0)}/100\n"
                    if alinh_dict.get('problemas_curto'):
                        user_content += f"- Problemas Curto Prazo: {', '.join(alinh_dict.get('problemas_curto', []))}\n"
                    if alinh_dict.get('problemas_medio'):
                        user_content += f"- Problemas Médio Prazo: {', '.join(alinh_dict.get('problemas_medio', []))}\n"
                    if alinh_dict.get('problemas_longo'):
                        user_content += f"- Problemas Longo Prazo: {', '.join(alinh_dict.get('problemas_longo', []))}\n"
                
                if "diversificacao" in results:
                    div = results["diversificacao"]
                    if hasattr(div, 'model_dump'):
                        div_dict = div.model_dump()
                    elif hasattr(div, 'dict'):
                        div_dict = div.dict()
                    else:
                        div_dict = div
                    user_content += f"\nDiversificação:\n"
                    user_content += f"- Score: {div_dict.get('score_diversificacao', 0)}/100\n"
                    if div_dict.get('problemas'):
                        user_content += f"- Problemas: {', '.join(div_dict.get('problemas', []))}\n"
                
                if "rebalanceamento" in results:
                    reb = results["rebalanceamento"]
                    if hasattr(reb, 'model_dump'):
                        reb_dict = reb.model_dump()
                    elif hasattr(reb, 'dict'):
                        reb_dict = reb.dict()
                    else:
                        reb_dict = reb
                    user_content += f"\nRebalanceamento:\n"
                    user_content += f"- Necessário: {'Sim' if reb_dict.get('necessario', False) else 'Não'}\n"
                    if reb_dict.get('ajustes'):
                        user_content += f"- Ajustes sugeridos: {', '.join(reb_dict.get('ajustes', []))}\n"
                
                if "oportunidades" in results:
                    ops = results["oportunidades"]
                    if isinstance(ops, list):
                        user_content += f"\nOportunidades:\n"
                        for op in ops:
                            if hasattr(op, 'model_dump'):
                                op_dict = op.model_dump()
                            elif hasattr(op, 'dict'):
                                op_dict = op.dict()
                            else:
                                op_dict = op
                            user_content += f"- {op_dict.get('nome', 'N/A')} ({op_dict.get('tipo', 'N/A')}): {op_dict.get('justificativa', '')}\n"
                
                if "projecao" in results:
                    proj = results["projecao"]
                    if isinstance(proj, dict):
                        user_content += f"\nProjeção:\n"
                        if proj.get('valor_final'):
                            user_content += f"- Valor Final Projetado: R$ {proj.get('valor_final', 0):,.2f}\n"
                        if proj.get('valor_atual'):
                            user_content += f"- Valor Atual: R$ {proj.get('valor_atual', 0):,.2f}\n"
                        if proj.get('aporte_mensal_necessario'):
                            user_content += f"- Aporte Mensal Necessário: R$ {proj.get('aporte_mensal_necessario', 0):,.2f}\n"
                        if proj.get('observacoes'):
                            user_content += f"- Observações: {proj.get('observacoes', '')}\n"
            
            # Preparar mensagens
            messages = [SystemMessage(content=system_prompt)]
            
            # Adicionar contexto histórico se disponível
            if context:
                for msg in context[-4:]:  # Últimas 4 mensagens
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        messages.append(HumanMessage(content=content))
                    elif role == 'assistant':
                        messages.append(AIMessage(content=content))
            
            # Adicionar mensagem atual
            messages.append(HumanMessage(content=user_content))
            
            # Chamar LLM
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Registrar no trace
            if trace_id:
                self.traceability.add_raw_prompt(trace_id, user_content, system_prompt)
                self.traceability.add_raw_response(trace_id, response_text)
            
            if not response_text or not response_text.strip():
                return (
                    "Desculpe, não consegui gerar uma resposta para sua pergunta. "
                    "Isso pode ocorrer devido a um problema temporário com o serviço de IA. "
                    "Por favor, tente reformular sua pergunta ou tente novamente mais tarde. "
                    "Se o problema persistir, entre em contato com o suporte técnico."
                )
            return response_text.strip()
            
        except Exception as e:
            print(f"[LangGraphAgent] Erro ao formatar com LLM: {e}")
            import traceback
            traceback.print_exc()
            if trace_id:
                self.traceability.add_error(trace_id, 'LLMFormatError', str(e), {'intent': intent})
            return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."
    
    def _format_response_node(self, state: AgentState) -> AgentState:
        """Nó que formata a resposta final usando LLM"""
        start_time = time.time()
        trace_id = state.get("trace_id")
        route = state.get("route")
        intent = state.get("intent")
        results = state.get("results", {})
        carteira = state.get("carteira")
        message = state.get("message", "")
        context = state.get("context", [])
        
        if route == "bypass":
            # Formatar resposta do bypass usando LLM
            if not self.llm:
                state["response"] = (
                    "Desculpe, o serviço de IA não está disponível no momento. "
                    "Isso pode ocorrer se a chave da API não estiver configurada ou se houver um problema temporário. "
                    "Por favor, verifique as configurações ou tente novamente mais tarde. "
                    "Se o problema persistir, entre em contato com o suporte técnico."
                )
                return state
            
            response = self._format_with_llm(message, carteira, results, intent, context, trace_id)
        else:
            # Resposta já formatada pelo ReAct
            response = state.get("response", "")
            if not response and not self.llm:
                response = "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
        
        state["response"] = response
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Registrar no trace
        if trace_id:
            self.traceability.add_graph_step(
                trace_id,
                "format_response",
                {"route": route, "intent": intent},
                {"response_length": len(response)},
                duration_ms
            )
            if route == "bypass":
                self.traceability.add_edge(trace_id, "bypass_analysis", "format_response", None)
            else:
                self.traceability.add_edge(trace_id, "react_agent", "format_response", None)
        
        return state
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """Detecta intenção do usuário"""
        message_lower = message.lower().strip()
        message_normalized = message_lower.replace('mminha', 'minha').replace('cartiera', 'carteira')
        
        # Priorizar recomendações sobre carteira genérica
        # Recomendações (verificar primeiro para evitar conflito com "carteira")
        if any(kw in message_lower for kw in ['recomendação', 'recomenda', 'recomendo', 'recomende', 'oportunidade', 'aplicar', 'investir em', 'onde investir', 'o que você recomenda']):
            return "buscar_oportunidades"
        
        # Projeção
        if any(kw in message_lower for kw in ['projeção', 'quanto preciso', 'quanto investir', 'objetivo', '1 milhão']):
            return "calcular_projecao"
        
        # Perguntas simples sobre perfil (verificar ANTES da verificação genérica de adequação)
        # Estas perguntas devem ir para react route, não bypass
        perfil_simples_keywords = [
            'qual é o meu perfil', 'qual é meu perfil', 'qual meu perfil',
            'meu perfil de investidor', 'qual meu perfil de investidor',
            'qual o meu perfil', 'qual o meu perfil de investidor',
            'meu perfil é', 'qual perfil', 'qual meu perfil de risco'
        ]
        # Verificar se é pergunta simples sobre perfil (não sobre adequação)
        if any(kw in message_lower for kw in perfil_simples_keywords):
            # Se também mencionar adequação/carteira, pode ser sobre adequação
            if not any(kw in message_lower for kw in ['adequada', 'adequado', 'está adequada', 'adequação', 'carteira', 'minha carteira']):
                return "qual_perfil_simples"  # Retorna intent específico para rastreamento
        
        # Adequação (verificar depois das perguntas simples sobre perfil)
        if any(kw in message_lower for kw in ['adequada', 'adequado', 'perfil', 'está adequada', 'adequação', 'perfil de risco']):
            return "analisar_adequacao"
        
        # Alinhamento
        if any(kw in message_lower for kw in ['alinhado', 'alinhamento', 'objetivos', 'curto prazo', 'médio prazo', 'longo prazo', 'horizonte']):
            return "analisar_alinhamento_objetivos"
        
        # Diversificação
        if any(kw in message_lower for kw in ['diversificação', 'diversificado', 'concentração', 'concentrado', 'diversificar']):
            return "analisar_diversificacao"
        
        # Rebalanceamento e alocação (verificar antes de carteira genérica)
        if any(kw in message_lower for kw in [
            'rebalanceamento', 'rebalancear', 'ajustes', 'ajustar', 'mudanças', 'revisão',
            'alocação', 'alocacao', 'mudar alocação', 'mudar alocacao', 'mudança de alocação',
            'mudança de alocacao', 'realocar', 'realocação', 'realocacao', 'mudar minha alocação',
            'mudar minha alocacao', 'vale a pena mudar', 'mudar alocação', 'ajustar alocação',
            'rebalancear carteira', 'revisar alocação'
        ]):
            return "recomendar_rebalanceamento"
        
        # Carteira (verificar por último)
        carteira_keywords = [
            'minha carteira', 'meu saldo', 'meus investimentos', 'meu patrimônio',
            'carteira', 'saldo', 'investimentos', 'patrimônio',
            'qual a minha', 'qual meu', 'quanto tenho'
        ]
        for keyword in carteira_keywords:
            if keyword in message_normalized or keyword in message_lower:
                return "obter_carteira"
        
        return None
    
    def _format_analise_completa(self, carteira: Dict, results: Dict) -> str:
        """DEPRECATED: Não usar mais. Use _format_with_llm em vez disso."""
        # Este método não deve mais ser chamado - todas as respostas devem usar LLM
        return "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
    
    def _format_analise_adequacao(self, carteira: Dict, results: Dict) -> str:
        """DEPRECATED: Não usar mais. Use _format_with_llm em vez disso."""
        # Este método não deve mais ser chamado - todas as respostas devem usar LLM
        return "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
    
    def _format_analise_diversificacao(self, carteira: Dict, results: Dict) -> str:
        """DEPRECATED: Não usar mais. Use _format_with_llm em vez disso."""
        # Este método não deve mais ser chamado - todas as respostas devem usar LLM
        return "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
    
    def _format_carteira_manual(self, carteira: Dict) -> str:
        """DEPRECATED: Não usar mais. Use _format_with_llm em vez disso."""
        # Este método não deve mais ser chamado - todas as respostas devem usar LLM
        return "Desculpe, o serviço de IA não está disponível no momento. Por favor, tente novamente mais tarde."
    
    def process_message(self, message: str, context: Optional[List] = None) -> Dict:
        """Processa mensagem usando LangGraph"""
        if not self.graph:
            # Retornar erro se LangGraph não disponível (não mais resposta determinística)
            model = os.getenv('AI_MODEL', 'gpt-4o')
            trace_id = self.traceability.create_trace(message, context=context, model=model)
            error_msg = (
                "Desculpe, o serviço de IA não está disponível no momento. "
                "Isso pode ocorrer se o LangGraph não estiver instalado ou configurado corretamente. "
                "Por favor, verifique as configurações do sistema ou entre em contato com o suporte técnico."
            )
            self.traceability.add_error(
                trace_id,
                'LangGraphUnavailableError',
                'LangGraph agent not available',
                {'message': message[:200]}
            )
            self.traceability.finalize_trace(
                trace_id,
                {"resposta": error_msg},
                {"source": "error", "error": "langgraph_unavailable"}
            )
            return {
                "response": error_msg,
                "trace_id": trace_id,
                "explicacao": None
            }
        
        # Criar trace com contexto e model
        model = os.getenv('AI_MODEL', 'gpt-4o')
        trace_id = self.traceability.create_trace(message, context=context, model=model)
        
        # Estado inicial
        initial_state: AgentState = {
            "message": message,
            "context": context or [],
            "intent": None,
            "route": None,
            "carteira": None,
            "results": {},
            "response": "",
            "trace_id": trace_id,
            "graph_steps": [],
            "tools_used": []
        }
        
        try:
            # Registrar início da execução do grafo
            self.traceability.add_event(
                trace_id,
                'graph_execution_start',
                {
                    'message': message[:200],
                    'context_length': len(context) if context else 0,
                    'model': model
                }
            )
            
            # Executar grafo
            config = {"configurable": {"thread_id": trace_id}}
            final_state = self.graph.invoke(initial_state, config)
            
            # Registrar fim da execução
            self.traceability.add_event(
                trace_id,
                'graph_execution_complete',
                {
                    'route': final_state.get("route"),
                    'intent': final_state.get("intent"),
                    'tools_used': final_state.get("tools_used", []),
                    'response_length': len(final_state.get("response", ""))
                }
            )
            
            # Finalizar trace
            self.traceability.finalize_trace(
                trace_id,
                {"resposta": final_state.get("response", "")},
                {
                    "tools_used": final_state.get("tools_used", []),
                    "route": final_state.get("route"),
                    "intent": final_state.get("intent")
                }
            )
            
            return {
                "response": final_state.get("response", ""),
                "trace_id": trace_id,
                "explicacao": {
                    "tools_used": final_state.get("tools_used", []),
                    "route": final_state.get("route"),
                    "intent": final_state.get("intent")
                }
            }
        except Exception as e:
            print(f"[LangGraphAgent] Erro ao processar: {e}")
            import traceback
            tb_str = traceback.format_exc()
            traceback.print_exc()
            
            # Mensagem de erro mais informativa
            error_type = type(e).__name__
            error_msg = f"Erro ao processar sua mensagem ({error_type}). Por favor, tente reformular sua pergunta ou tente novamente mais tarde."
            
            # Registrar erro
            try:
                message_preview = message[:200] if message else 'N/A'
            except:
                message_preview = 'N/A'
            
            self.traceability.add_error(
                trace_id,
                'LangGraphExecutionException',
                str(e),
                {'method': 'process_message', 'error_type': error_type, 'message': message_preview},
                tb_str
            )
            
            self.traceability.finalize_trace(
                trace_id,
                {"resposta": error_msg},
                {"error": str(e), "error_type": error_type}
            )
            
            return {
                "response": error_msg,
                "trace_id": trace_id,
                "explicacao": {"error": str(e), "error_type": error_type}
            }

