"""
Endpoints LangGraph Server para compatibilidade com LangSmith Studio.

Expõe o agente LangGraph através de endpoints compatíveis com o formato
esperado pelo LangGraph Server e LangSmith Studio.
Usa o grafo MessagesState diretamente.
Injeta regras de redirecionamento (Autonomia) em config para o grafo.
"""
from flask import Blueprint, request, jsonify, Response
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import uuid
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

langgraph_server_bp = Blueprint('langgraph_server', __name__)

# Regras padrão quando não houver configuração (espelha CONFIGURACOES_PADRAO)
_DEFAULT_REGRAS_REDIRECIONAMENTO = [
    "Solicitação de valores acima de R$ 100.000",
    "Reclamações ou insatisfação",
    "Solicitação de cancelamento de conta",
    "Questões legais ou regulatórias",
]


def _inject_regras_redirecionamento(config: dict) -> None:
    """
    Injeta regras_redirecionamento da autonomia do usuário em config["configurable"].
    Usa user_id do token, do body config.configurable.user_id ou "default".
    """
    if "configurable" not in config:
        config["configurable"] = {}
    try:
        from app.utils.jwt_utils import get_user_id_from_token
        from app.routes.configuracoes import configuracoes_usuario, CONFIGURACOES_PADRAO
        token = (request.headers.get("Authorization") or "").replace("Bearer ", "").strip()
        user_id = get_user_id_from_token(token) if token else None
        if user_id is None and isinstance(config.get("configurable"), dict):
            user_id = config["configurable"].get("user_id") or "default"
        user_id = user_id or "default"
        cfg = configuracoes_usuario.get(user_id, CONFIGURACOES_PADRAO)
        autonomia = cfg.get("autonomia", {}) or CONFIGURACOES_PADRAO.get("autonomia", {})
        regras = autonomia.get("regras_redirecionamento", _DEFAULT_REGRAS_REDIRECIONAMENTO)
        config["configurable"]["regras_redirecionamento"] = regras
    except Exception as e:
        logger.warning("[LangGraphServer] Falha ao carregar regras de redirecionamento: %s", e)
        config["configurable"]["regras_redirecionamento"] = _DEFAULT_REGRAS_REDIRECIONAMENTO


# Funções helper para logging estruturado
def log_request(endpoint_name, method, **kwargs):
    """
    Log estruturado de requisição recebida.
    
    Args:
        endpoint_name: Nome do endpoint
        method: Método HTTP
        **kwargs: Dados adicionais para log
    """
    log_data = {
        "endpoint": endpoint_name,
        "method": method,
        "path": request.path,
        "remote_addr": request.remote_addr
    }
    log_data.update(kwargs)
    logger.info(f"[LangGraphServer] REQUEST: {json.dumps(log_data, default=str)}")


def log_response(endpoint_name, status_code, duration_ms=None, **kwargs):
    """
    Log estruturado de resposta enviada.
    
    Args:
        endpoint_name: Nome do endpoint
        status_code: Código de status HTTP
        duration_ms: Duração em milissegundos (opcional)
        **kwargs: Dados adicionais para log
    """
    log_data = {
        "endpoint": endpoint_name,
        "status_code": status_code,
        "path": request.path
    }
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    log_data.update(kwargs)
    logger.info(f"[LangGraphServer] RESPONSE: {json.dumps(log_data, default=str)}")


def log_error(endpoint_name, error, context=None):
    """
    Log estruturado de erro.
    
    Args:
        endpoint_name: Nome do endpoint
        error: Exceção ou mensagem de erro
        context: Contexto adicional do erro
    """
    log_data = {
        "endpoint": endpoint_name,
        "error": str(error),
        "error_type": type(error).__name__ if hasattr(error, '__class__') else "Unknown",
        "path": request.path,
        "method": request.method
    }
    if context:
        log_data["context"] = context
    logger.error(f"[LangGraphServer] ERROR: {json.dumps(log_data, default=str)}")
    import traceback
    logger.error(f"[LangGraphServer] TRACEBACK: {traceback.format_exc()}")


def assistant_not_found_response(assistant_id):
    """
    Retorna resposta padronizada para assistente não encontrado.
    
    Args:
        assistant_id: ID do assistente que não foi encontrado
    
    Returns:
        Tupla (response, status_code) para retornar no endpoint
    """
    return jsonify({
        "error": f"Assistant {assistant_id} not found",
        "message": f"O assistente '{assistant_id}' não existe. Use 'agent' como assistant_id.",
        "available_assistants": ["agent"]
    }), 404


def validate_request_body(required_fields=None):
    """
    Valida se o request body existe e contém campos obrigatórios.
    
    Args:
        required_fields: Lista de campos obrigatórios (ex: ['input', 'assistant_id'])
    
    Returns:
        (data, error_response) - Tupla com dados e resposta de erro (se houver)
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return None, (jsonify({"error": "Request body é obrigatório"}), 400)
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return None, (jsonify({
                "error": "Campos obrigatórios faltando",
                "missing_fields": missing_fields
            }), 400)
    
    return data, None


def validate_messages(messages):
    """
    Valida formato de mensagens.
    
    Args:
        messages: Lista de mensagens
    
    Returns:
        (is_valid, error_response) - Tupla com validação e resposta de erro (se houver)
    """
    if not messages:
        return False, (jsonify({"error": "messages é obrigatório no input"}), 400)
    
    for msg in messages:
        if not isinstance(msg, dict):
            return False, (jsonify({
                "error": "Formato de mensagem inválido",
                "message": "Cada mensagem deve ser um objeto/dicionário"
            }), 400)
        
        if "role" not in msg or "content" not in msg:
            return False, (jsonify({
                "error": "Formato de mensagem inválido",
                "message": "Cada mensagem deve ter 'role' e 'content'",
                "received": msg
            }), 400)
        
        if msg.get("role") not in ["user", "assistant", "system", "tool"]:
            return False, (jsonify({
                "error": "Role inválido",
                "message": f"Role deve ser 'user', 'assistant', 'system' ou 'tool', recebido: {msg.get('role')}"
            }), 400)
    
    return True, None

# Instância global do grafo (lazy loading)
_graph = None
_graph_error = None

def get_graph():
    """Obtém o grafo (singleton com lazy loading)"""
    global _graph, _graph_error
    
    # Se já tentou carregar e falhou, retornar erro
    if _graph_error is not None:
        raise _graph_error
    
    # Se já carregou, retornar
    if _graph is not None:
        return _graph
    
    # Tentar carregar o grafo
    try:
        from app.services.langgraph_graph import graph
        _graph = graph
        logger.info("[LangGraphServer] Grafo inicializado com sucesso")
        return _graph
    except Exception as e:
        _graph_error = e
        logger.error(f"[LangGraphServer] Erro ao inicializar grafo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def convert_messages_to_json(messages):
    """
    Converte mensagens LangChain para formato JSON esperado pelo LangSmith Studio.
    
    Args:
        messages: Lista de mensagens LangChain (HumanMessage, AIMessage, etc.)
    
    Returns:
        Lista de dicionários no formato {"role": "...", "content": "..."}
    """
    result = []
    for msg in messages:
        if hasattr(msg, 'content'):
            role = "user"
            if hasattr(msg, '__class__'):
                class_name = msg.__class__.__name__
                if "Human" in class_name:
                    role = "user"
                elif "AI" in class_name or "Assistant" in class_name:
                    role = "assistant"
                elif "System" in class_name:
                    role = "system"
                elif "Tool" in class_name:
                    role = "tool"
            
            content = msg.content if hasattr(msg, 'content') else str(msg)
            result.append({
                "role": role,
                "content": content
            })
        elif isinstance(msg, dict):
            # Já está no formato correto
            result.append(msg)
    return result


def is_langchain_message(obj):
    """
    Verifica se um objeto é uma mensagem LangChain (AIMessage, HumanMessage, SystemMessage, etc.).
    
    Args:
        obj: Objeto a verificar
    
    Returns:
        True se for uma mensagem LangChain, False caso contrário
    """
    if obj is None:
        return False
    # Verificar por tipo de classe
    if hasattr(obj, '__class__'):
        class_name = obj.__class__.__name__
        if any(msg_type in class_name for msg_type in ['Message', 'AIMessage', 'HumanMessage', 'SystemMessage', 'ToolMessage']):
            return True
    # Verificar se tem atributo 'content' e não é dict/list (indicando mensagem LangChain)
    if hasattr(obj, 'content') and not isinstance(obj, (dict, list, str, int, float, bool)):
        return True
    return False


def convert_state_to_json(state_values):
    """
    Converte state_values para formato JSON serializável.
    Especialmente converte mensagens LangChain para formato JSON.
    Detecta mensagens LangChain em qualquer nível de aninhamento.
    
    Args:
        state_values: Dicionário ou objeto contendo valores do estado
    
    Returns:
        Dicionário com valores convertidos para formato JSON serializável
    """
    # Verificar se é uma mensagem LangChain diretamente
    if is_langchain_message(state_values):
        converted = convert_messages_to_json([state_values])
        return converted[0] if converted else str(state_values)
    
    if isinstance(state_values, dict):
        result = {}
        for key, value in state_values.items():
            # Verificar se é uma mensagem LangChain
            if is_langchain_message(value):
                converted = convert_messages_to_json([value])
                result[key] = converted[0] if converted else str(value)
            elif key == "messages" and isinstance(value, list):
                # Converter lista de mensagens
                result[key] = convert_messages_to_json(value)
            elif isinstance(value, (dict, list)):
                # Recursivamente converter dicts e lists
                result[key] = convert_state_to_json(value)
            elif hasattr(value, 'content') and not isinstance(value, (dict, list, str, int, float, bool)):
                # Objeto com atributo 'content' que não é dict/list (provavelmente mensagem LangChain)
                converted = convert_messages_to_json([value])
                result[key] = converted[0] if converted else str(value)
            else:
                result[key] = value
        return result
    elif isinstance(state_values, list):
        # Verificar cada item da lista antes de processar recursivamente
        result = []
        for item in state_values:
            if is_langchain_message(item):
                # Converter mensagem LangChain
                converted = convert_messages_to_json([item])
                result.append(converted[0] if converted else str(item))
            elif isinstance(item, (dict, list)):
                # Processar recursivamente
                result.append(convert_state_to_json(item))
            elif hasattr(item, 'content') and not isinstance(item, (dict, list, str, int, float, bool)):
                # Objeto com atributo 'content' que não é dict/list
                converted = convert_messages_to_json([item])
                result.append(converted[0] if converted else str(item))
            else:
                result.append(item)
        return result
    else:
        return state_values


@langgraph_server_bp.route('/', methods=['GET', 'OPTIONS'])
def root():
    """
    Endpoint raiz para descoberta do servidor LangGraph.
    Retorna informações sobre o servidor e endpoints disponíveis.
    """
    try:
        # Tentar verificar se grafo está disponível, mas não falhar se não estiver
        graph_available = False
        try:
            get_graph()
            graph_available = True
        except Exception as e:
            logger.warning(f"[LangGraphServer] Grafo não disponível no root: {e}")
        
        return jsonify({
            "status": "ok",
            "service": "langgraph-server",
            "version": "1.0.0",
            "graph_available": graph_available,
            "endpoints": {
                "assistants": "/assistants",
                "threads": "/threads",
                "health": "/health",
                "docs": "/docs"
            }
        }), 200
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro no root: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@langgraph_server_bp.route('/info', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/info', methods=['GET', 'OPTIONS'])
def info():
    """
    Endpoint de informações do servidor LangGraph (compatibilidade com LangSmith Studio).
    Retorna informações sobre o servidor, versão e capacidades.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info("[LangGraphServer] info: Endpoint /info chamado")
        
        # Tentar verificar se grafo está disponível
        graph_available = False
        graph_error = None
        try:
            get_graph()
            graph_available = True
        except Exception as e:
            graph_error = str(e)
            logger.warning(f"[LangGraphServer] info: Grafo não disponível: {e}")
        
        # Retornar informações no formato esperado pelo LangSmith Studio
        info_response = {
            "status": "ok",
            "service": "langgraph-server",
            "version": "1.0.0",
            "server_type": "langgraph",
            "graph_available": graph_available,
            "capabilities": {
                "assistants": True,
                "threads": True,
                "streaming": True,  # Temos endpoints de stream
                "checkpointing": True  # Usamos MemorySaver para checkpointing
            },
            "endpoints": {
                "assistants": "/assistants",
                "assistants_search": "/assistants/search",
                "threads": "/threads",
                "health": "/health",
                "docs": "/docs",
                "info": "/info"
            }
        }
        
        if graph_error:
            info_response["graph_error"] = graph_error
        
        logger.info(f"[LangGraphServer] info: Retornando informações do servidor (graph_available={graph_available})")
        return jsonify(info_response), 200
    except Exception as e:
        logger.error(f"[LangGraphServer] info: Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@langgraph_server_bp.route('/docs', methods=['GET'])
def docs():
    """
    Endpoint de documentação OpenAPI (compatibilidade com LangGraph Server).
    Retorna informações básicas sobre a API.
    """
    try:
        return jsonify({
            "openapi": "3.0.0",
            "info": {
                "title": "AlphaAdvisor LangGraph Server",
                "version": "1.0.0",
                "description": "LangGraph Server API for AlphaAdvisor Agent"
            },
            "paths": {
                "/assistants": {
                    "get": {
                        "summary": "List assistants",
                        "responses": {
                            "200": {
                                "description": "List of assistants"
                            }
                        }
                    },
                    "post": {
                        "summary": "Search assistants",
                        "responses": {
                            "200": {
                                "description": "Search results"
                            }
                        }
                    }
                },
                "/threads": {
                    "get": {
                        "summary": "List threads",
                        "responses": {
                            "200": {
                                "description": "List of threads"
                            }
                        }
                    },
                    "post": {
                        "summary": "Create thread",
                        "responses": {
                            "200": {
                                "description": "Thread created"
                            }
                        }
                    }
                }
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/search', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/search', methods=['POST', 'OPTIONS'])
def search_assistants():
    """
    Busca assistentes com filtros (formato LangGraph Server).
    Retorna array direto de assistants.
    Este endpoint NÃO precisa do grafo - apenas retorna lista de assistentes disponíveis.
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        # Tentar obter JSON, mas não falhar se não houver Content-Type correto ou body vazio
        # force=True: tenta fazer parse mesmo sem Content-Type correto
        # silent=True: retorna None em vez de lançar exceção
        data = request.get_json(force=True, silent=True) or {}
        
        log_request("search_assistants", request.method, data_keys=list(data.keys()))
        
        limit = data.get('limit', 100)
        offset = data.get('offset', 0)
        
        now = datetime.utcnow().isoformat() + 'Z'
        assistants = [
            {
                "assistant_id": "agent",
                "graph_id": "agent",
                "name": "AlphaAdvisor Agent",
                "description": "Agente LangGraph do AlphaAdvisor com análise de carteira e recomendações",
                "metadata": {},
                "config": {
                    "configurable": {}
                },
                "version": 1,
                "created_at": now,
                "updated_at": now
            }
        ]
        
        # Aplicar paginação
        if offset > 0 or limit < len(assistants):
            assistants = assistants[offset:offset+limit]
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("search_assistants", 200, duration_ms, assistants_count=len(assistants))
        
        return jsonify(assistants), 200
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("search_assistants", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e), "type": type(e).__name__}), 500


@langgraph_server_bp.route('/assistants', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants', methods=['GET', 'OPTIONS'])
def list_assistants():
    """
    Lista assistentes (grafos) disponíveis.
    
    GET /assistants - Lista simples
    
    Retorna lista de grafos que podem ser usados pelo Studio.
    """
    try:
        # Se for OPTIONS (preflight CORS), retornar OK
        if request.method == 'OPTIONS':
            return '', 200
        
        # Formato completo conforme especificação LangGraph Server
        now = datetime.utcnow().isoformat() + 'Z'
        
        assistants = [
            {
                "assistant_id": "agent",
                "graph_id": "agent",
                "name": "AlphaAdvisor Agent",
                "description": "Agente LangGraph do AlphaAdvisor com análise de carteira e recomendações",
                "metadata": {},
                "config": {
                    "configurable": {}
                },
                "version": 1,
                "created_at": now,
                "updated_at": now
            }
        ]
        
        logger.info(f"[LangGraphServer] list_assistants: retornando {len(assistants)} assistentes")
        
        # Retornar objeto com chave assistants (formato GET)
        return jsonify({
            "assistants": assistants
        }), 200
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao listar assistants: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/<assistant_id>', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/<assistant_id>', methods=['GET', 'OPTIONS'])
def get_assistant(assistant_id):
    """
    Obtém informações de um assistente específico.
    
    Args:
        assistant_id: ID do assistente
    
    Retorna informações do assistente ou 404 se não existir.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info(f"[LangGraphServer] get_assistant: Buscando assistente {assistant_id}")
        
        # Por enquanto, apenas o assistente "agent" existe
        if assistant_id == "agent":
            now = datetime.utcnow().isoformat() + 'Z'
            assistant = {
                "assistant_id": "agent",
                "graph_id": "agent",
                "name": "AlphaAdvisor Agent",
                "description": "Agente LangGraph do AlphaAdvisor com análise de carteira e recomendações",
                "metadata": {},
                "config": {
                    "configurable": {}
                },
                "version": 1,
                "created_at": now,
                "updated_at": now
            }
            logger.info(f"[LangGraphServer] get_assistant: Assistente {assistant_id} encontrado")
            return jsonify(assistant), 200
        else:
            logger.warning(f"[LangGraphServer] get_assistant: Assistente {assistant_id} não encontrado")
            return assistant_not_found_response(assistant_id)
            
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao obter assistant {assistant_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/<assistant_id>/schemas', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/<assistant_id>/schemas', methods=['GET', 'OPTIONS'])
def get_assistant_schemas(assistant_id):
    """
    Obtém schemas (input/output) de um assistente específico.
    
    Args:
        assistant_id: ID do assistente
    
    Retorna schemas do assistente ou 404 se não existir.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info(f"[LangGraphServer] get_assistant_schemas: Buscando schemas do assistente {assistant_id}")
        
        # Por enquanto, apenas o assistente "agent" existe
        if assistant_id == "agent":
            # Retornar schemas no formato correto esperado pelo LangSmith Studio
            # O formato deve incluir graph_id, state_schema, input_schema, output_schema
            message_schema = {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["user", "assistant", "system", "tool"]
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": ["role", "content"]
            }
            
            schemas = {
                "graph_id": "agent",
                "state_schema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": message_schema,
                            "description": "Lista de mensagens da conversa"
                        }
                    },
                    "required": ["messages"],
                    "additionalProperties": False
                },
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": message_schema,
                            "description": "Mensagens de entrada para o grafo"
                        }
                    },
                    "required": ["messages"],
                    "additionalProperties": False
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": message_schema,
                            "description": "Mensagens de saída do grafo"
                        }
                    },
                    "required": ["messages"],
                    "additionalProperties": False
                }
            }
            logger.info(f"[LangGraphServer] get_assistant_schemas: Schemas do assistente {assistant_id} retornados")
            logger.info(f"[LangGraphServer] get_assistant_schemas: state_schema tem 'messages' como chave principal: {'messages' in schemas.get('state_schema', {}).get('properties', {})}")
            logger.info(f"[LangGraphServer] get_assistant_schemas: Schema completo: {json.dumps(schemas, indent=2)}")
            return jsonify(schemas), 200
        else:
            logger.warning(f"[LangGraphServer] get_assistant_schemas: Assistente {assistant_id} não encontrado")
            return assistant_not_found_response(assistant_id)
            
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao obter schemas do assistant {assistant_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/<assistant_id>/graph', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/<assistant_id>/graph', methods=['GET', 'OPTIONS'])
def get_assistant_graph(assistant_id):
    """
    Obtém a estrutura do grafo de um assistente específico.
    
    Args:
        assistant_id: ID do assistente
    
    Retorna estrutura do grafo ou 404 se não existir.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info(f"[LangGraphServer] get_assistant_graph: Buscando grafo do assistente {assistant_id}")
        
        # Por enquanto, apenas o assistente "agent" existe
        if assistant_id == "agent":
            try:
                graph_instance = get_graph()
                
                # Obter estrutura básica do grafo
                # O grafo compilado tem informações sobre nós e arestas
                graph_structure = {
                    "nodes": [
                        {
                            "id": "init",
                            "name": "init",
                            "type": "init"
                        },
                        {
                            "id": "agent",
                            "name": "agent",
                            "type": "agent"
                        },
                        {
                            "id": "tools",
                            "name": "tools",
                            "type": "tool"
                        },
                        {
                            "id": "end",
                            "name": "end",
                            "type": "end"
                        }
                    ],
                    "edges": [
                        {
                            "source": "START",
                            "target": "init"
                        },
                        {
                            "source": "init",
                            "target": "agent"
                        },
                        {
                            "source": "agent",
                            "target": "tools",
                            "condition": "has_tool_calls"
                        },
                        {
                            "source": "agent",
                            "target": "end",
                            "condition": "no_tool_calls"
                        },
                        {
                            "source": "tools",
                            "target": "agent"
                        },
                        {
                            "source": "end",
                            "target": "END"
                        }
                    ],
                    "state_schema": {
                        "type": "object",
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {
                                            "type": "string",
                                            "enum": ["user", "assistant", "system", "tool"]
                                        },
                                        "content": {
                                            "type": "string"
                                        }
                                    },
                                    "required": ["role", "content"]
                                },
                                "description": "Lista de mensagens da conversa"
                            }
                        },
                        "required": ["messages"],
                        "additionalProperties": False
                    }
                }
                
                logger.info(f"[LangGraphServer] get_assistant_graph: Grafo do assistente {assistant_id} retornado")
                return jsonify(graph_structure), 200
            except Exception as graph_error:
                logger.error(f"[LangGraphServer] get_assistant_graph: Erro ao obter grafo: {graph_error}")
                return jsonify({
                    "error": "Graph not available",
                    "message": str(graph_error)
                }), 503
        else:
            logger.warning(f"[LangGraphServer] get_assistant_graph: Assistente {assistant_id} não encontrado")
            return assistant_not_found_response(assistant_id)
            
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao obter grafo do assistant {assistant_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/<assistant_id>/subgraphs', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/<assistant_id>/subgraphs', methods=['GET', 'OPTIONS'])
def get_assistant_subgraphs(assistant_id):
    """
    Obtém subgrafos de um assistente específico.
    
    Args:
        assistant_id: ID do assistente
    
    Retorna lista de subgrafos ou 404 se não existir.
    Por enquanto, retorna lista vazia pois não temos subgrafos aninhados.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info(f"[LangGraphServer] get_assistant_subgraphs: Buscando subgrafos do assistente {assistant_id}")
        
        # Por enquanto, apenas o assistente "agent" existe
        if assistant_id == "agent":
            # Por enquanto, não temos subgrafos aninhados
            # Retornar lista vazia (formato esperado pelo LangSmith Studio)
            subgraphs = []
            
            logger.info(f"[LangGraphServer] get_assistant_subgraphs: Subgrafos do assistente {assistant_id} retornados (vazio)")
            return jsonify(subgraphs), 200
        else:
            logger.warning(f"[LangGraphServer] get_assistant_subgraphs: Assistente {assistant_id} não encontrado")
            return assistant_not_found_response(assistant_id)
            
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao obter subgrafos do assistant {assistant_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/assistants/<assistant_id>/versions', methods=['GET', 'POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/assistants/<assistant_id>/versions', methods=['GET', 'POST', 'OPTIONS'])
def get_assistant_versions(assistant_id):
    """
    Obtém versões de um assistente específico.
    
    O LangSmith Studio usa este endpoint para gerenciar versões de assistentes.
    
    Args:
        assistant_id: ID do assistente
    
    Retorna lista de versões do assistente ou 404 se não existir.
    Por enquanto, retorna uma versão única (versão 1).
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        log_request("get_assistant_versions", request.method, assistant_id=assistant_id)
        
        # Por enquanto, apenas o assistente "agent" existe
        if assistant_id == "agent":
            now = datetime.utcnow().isoformat() + 'Z'
            
            # Retornar lista de versões (por enquanto apenas versão 1)
            versions = [
                {
                    "version": 1,
                    "assistant_id": "agent",
                    "graph_id": "agent",
                    "name": "AlphaAdvisor Agent",
                    "description": "Agente LangGraph do AlphaAdvisor com análise de carteira e recomendações",
                    "metadata": {},
                    "config": {
                        "configurable": {}
                    },
                    "created_at": now,
                    "updated_at": now
                }
            ]
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_response("get_assistant_versions", 200, duration_ms, assistant_id=assistant_id, versions_count=len(versions))
            logger.info(f"[LangGraphServer] get_assistant_versions: Retornando {len(versions)} versão(ões) para assistente {assistant_id}")
            return jsonify(versions), 200
        else:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.warning(f"[LangGraphServer] get_assistant_versions: Assistente {assistant_id} não encontrado")
            log_response("get_assistant_versions", 404, duration_ms, assistant_id=assistant_id)
            return assistant_not_found_response(assistant_id)
            
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("get_assistant_versions", e, {"assistant_id": assistant_id, "duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads', methods=['GET', 'POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads', methods=['GET', 'POST', 'OPTIONS'])
def threads_handler():
    """
    Handler unificado para threads - roteia para list ou create baseado no método
    """
    if request.method == 'OPTIONS':
        return '', 200
    elif request.method == 'GET':
        return list_threads()
    elif request.method == 'POST':
        return create_thread()


@langgraph_server_bp.route('/threads/search', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/search', methods=['POST', 'OPTIONS'])
def search_threads():
    """
    Busca threads com filtros (formato LangGraph Server).
    
    O LangSmith Studio usa este endpoint para buscar threads.
    
    Formato esperado:
    {
        "limit": 100,
        "offset": 0,
        "metadata": {},  # Opcional: filtros de metadata
        "before": "thread_id"  # Opcional: buscar antes de um thread_id
    }
    
    Retorna array direto de threads.
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json(force=True, silent=True) or {}
        log_request("search_threads", request.method, data_keys=list(data.keys()))
        
        limit = data.get('limit', 100)
        offset = data.get('offset', 0)
        metadata_filter = data.get('metadata', {})
        before = data.get('before', None)
        
        # Por enquanto, retornar lista vazia pois não temos sistema de busca de threads
        # Em produção, isso deveria consultar o checkpointer para buscar threads
        threads = []
        
        # Se houver um grafo com checkpointer, tentar obter threads
        try:
            graph_instance = get_graph()
            # Por enquanto, não temos método para listar threads do checkpointer
            # O MemorySaver não expõe uma API para listar threads
            # Em produção, seria necessário usar um checkpointer persistente (ex: PostgreSQL)
        except Exception as e:
            logger.debug(f"[LangGraphServer] search_threads: Não foi possível obter threads do checkpointer: {e}")
        
        # Aplicar paginação
        if offset > 0 or limit < len(threads):
            threads = threads[offset:offset+limit]
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("search_threads", 200, duration_ms, threads_count=len(threads))
        
        # Retornar array direto conforme especificação LangGraph Server
        return jsonify(threads), 200
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("search_threads", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e), "type": type(e).__name__}), 500


def list_threads():
    """
    Lista threads existentes.
    
    Nota: Por enquanto retorna lista vazia, pois não temos persistência
    de threads. Em produção, isso deveria consultar o checkpointer.
    """
    try:
        # Por enquanto, retornar lista vazia
        # Em produção, consultar checkpointer para listar threads
        return jsonify({
            "threads": []
        }), 200
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao listar threads: {e}")
        return jsonify({"error": str(e)}), 500


def create_thread():
    """
    Cria uma nova thread e opcionalmente executa o grafo.
    
    Formato esperado:
    {
        "assistant_id": "agent",
        "input": {
            "messages": [{"role": "user", "content": "..."}]  # Opcional
        }
    }
    
    Se mensagens forem fornecidas, executa o grafo.
    Se não, cria uma thread vazia (comportamento esperado pelo LangSmith Studio).
    
    Retorna:
    {
        "thread_id": "...",
        "values": {
            "messages": [...]
        }
    }
    """
    start_time = datetime.utcnow()
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        assistant_id = data.get("assistant_id", "agent")
        input_data = data.get("input", {})
        messages = input_data.get("messages", [])
        
        log_request("create_thread", request.method, assistant_id=assistant_id, messages_count=len(messages))
        
        # Gerar thread_id
        thread_id = str(uuid.uuid4())
        
        # Se não houver mensagens, criar thread vazia (comportamento esperado pelo LangSmith Studio)
        if not messages:
            result_dict = {
                "thread_id": thread_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "values": {
                    "messages": []
                }
            }
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_response("create_thread", 200, duration_ms, thread_id=thread_id, empty_thread=True)
            return jsonify(result_dict), 200
        
        # Validar formato das mensagens
        is_valid, error_response = validate_messages(messages)
        if not is_valid:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_error("create_thread", "Formato de mensagem inválido", {"messages_count": len(messages)})
            return error_response
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
        
        if not langchain_messages:
            logger.warning("[LangGraphServer] create_thread: Nenhuma mensagem de usuário encontrada")
            return jsonify({"error": "Pelo menos uma mensagem com role='user' é necessária"}), 400
        
        # Obter grafo e executar
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] create_thread: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        config = data.get("config", {"configurable": {"thread_id": thread_id}})
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id
        _inject_regras_redirecionamento(config)
        
        # Executar grafo com MessagesState
        # Com checkpointer, o LangGraph automaticamente preserva o estado
        logger.info(f"[LangGraphServer] create_thread: Executando grafo para thread {thread_id}")
        result = graph_instance.invoke({"messages": langchain_messages}, config=config)
        
        # Converter todas as mensagens do resultado para formato de resposta
        # O resultado contém TODAS as mensagens (input + resposta)
        all_messages = convert_messages_to_json(result.get("messages", []))
        
        result_dict = {
            "thread_id": thread_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "values": {
                "messages": all_messages
            }
        }
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("create_thread", 200, duration_ms, thread_id=thread_id, messages_count=len(all_messages))
        return jsonify(result_dict), 200
        
    except RuntimeError as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("create_thread", e, {"duration_ms": duration_ms, "error_type": "RuntimeError"})
        return jsonify({"error": str(e), "message": "LangGraph não está disponível"}), 503
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("create_thread", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500




@langgraph_server_bp.route('/threads/<thread_id>', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>', methods=['GET', 'OPTIONS'])
def get_thread(thread_id):
    """
    Obtém estado de uma thread específica do checkpointer.
    
    Args:
        thread_id: ID da thread
    
    Retorna:
    {
        "thread_id": "...",
        "values": {
            "messages": [...]
        }
    }
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        log_request("get_thread", request.method, thread_id=thread_id)
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] get_thread: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Config com thread_id para checkpointer
        config = {"configurable": {"thread_id": thread_id}}
        
        # Recuperar estado do checkpointer
        try:
            state = graph_instance.get_state(config)
            
            # Se estado não existir ou estiver vazio, retornar thread vazia (não 404)
            # O LangSmith Studio espera 200 mesmo quando thread não existe
            if state is None or not state.values:
                logger.info(f"[LangGraphServer] get_thread: Thread {thread_id} não encontrada, retornando thread vazia")
                return jsonify({
                    "thread_id": thread_id,
                    "values": {
                        "messages": []
                    }
                }), 200
            
            # Extrair mensagens do estado
            messages = state.values.get("messages", [])
            
            # Converter mensagens LangChain para formato JSON
            response_messages = convert_messages_to_json(messages)
            
            result_dict = {
                "thread_id": thread_id,
                "values": {
                    "messages": response_messages
                }
            }
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_response("get_thread", 200, duration_ms, thread_id=thread_id, messages_count=len(response_messages))
            return jsonify(result_dict), 200
            
        except Exception as state_error:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_error("get_thread", state_error, {"thread_id": thread_id, "duration_ms": duration_ms})
            return jsonify({
                "error": "Thread não encontrada",
                "message": f"Erro ao recuperar thread {thread_id}: {str(state_error)}"
            }), 404
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("get_thread", e, {"thread_id": thread_id, "duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/history', methods=['GET', 'POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/history', methods=['GET', 'POST', 'OPTIONS'])
def get_thread_history(thread_id):
    """
    Retorna o histórico de estados de uma thread.
    
    Suporta GET e POST conforme especificação LangGraph Server.
    GET: parâmetros via query string (limit, before)
    POST: parâmetros via body JSON (limit, before, metadata, checkpoint)
    
    O LangSmith Studio chama este endpoint para obter o histórico da thread.
    Quando não há histórico disponível, retorna lista vazia.
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        # Parsear parâmetros
        if request.method == 'GET':
            limit = request.args.get('limit', default=10, type=int)
            before = request.args.get('before', default=None, type=str)
        else:  # POST
            data = request.get_json() or {}
            limit = data.get('limit', 10)
            before = data.get('before', None)
            # metadata e checkpoint são aceitos mas não usados na filtragem por enquanto
        
        logger.info(f"[LangGraphServer] get_thread_history: Buscando histórico da thread {thread_id} (limit={limit}, before={before})")
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] get_thread_history: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        config = {"configurable": {"thread_id": thread_id}}
        history_items = []
        
        try:
            # Tentar usar get_state_history se disponível
            if hasattr(graph_instance, "get_state_history"):
                states = list(graph_instance.get_state_history(config))
                
                # Processar cada state e criar item de histórico completo
                for idx, state in enumerate(states):
                    if state is None:
                        continue
                    
                    # Extrair valores do state
                    values = state.values or {}
                    messages = convert_messages_to_json(values.get("messages", []))
                    
                    # Extrair informações de checkpoint
                    checkpoint_id = None
                    checkpoint_ns = ""
                    checkpoint_map = {}
                    metadata = {}
                    created_at = None
                    next_nodes = []
                    
                    # Tentar extrair informações do state
                    if hasattr(state, 'checkpoint'):
                        checkpoint = state.checkpoint
                        if isinstance(checkpoint, dict):
                            checkpoint_id = checkpoint.get('id') or checkpoint.get('checkpoint_id')
                            checkpoint_ns = checkpoint.get('ns', '')
                            checkpoint_map = checkpoint.get('map', {})
                    
                    # Tentar extrair metadata
                    if hasattr(state, 'metadata'):
                        metadata = state.metadata if isinstance(state.metadata, dict) else {}
                    
                    # Tentar extrair created_at
                    if hasattr(state, 'created_at'):
                        created_at = state.created_at
                    elif hasattr(state, 'ts'):
                        created_at = state.ts
                    
                    # Tentar extrair next nodes
                    if hasattr(state, 'next'):
                        next_nodes = state.next if isinstance(state.next, list) else []
                    
                    # Gerar checkpoint_id se não disponível
                    if not checkpoint_id:
                        checkpoint_id = f"{thread_id}-{idx}"
                    
                    # Gerar timestamp se não disponível
                    if not created_at:
                        created_at = datetime.utcnow().isoformat() + "Z"
                    elif isinstance(created_at, (int, float)):
                        # Converter timestamp numérico para ISO 8601
                        from datetime import datetime as dt
                        created_at = dt.fromtimestamp(created_at).isoformat() + "Z"
                    elif not created_at.endswith('Z'):
                        # Garantir formato ISO 8601 com Z
                        if '+' not in created_at and 'Z' not in created_at:
                            created_at = created_at + "Z"
                    
                    # Criar item de histórico completo
                    history_item = {
                        "values": {"messages": messages},
                        "checkpoint": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id,
                            "checkpoint_map": checkpoint_map
                        },
                        "metadata": metadata,
                        "created_at": created_at,
                        "next": next_nodes,
                        "tasks": [],  # Tasks não são expostas pelo MemorySaver
                        "parent_checkpoint": None  # Parent checkpoint não é exposto pelo MemorySaver
                    }
                    
                    history_items.append(history_item)
            else:
                # Fallback: usar get_state e retornar como único item
                state = graph_instance.get_state(config)
                if state is not None and state.values:
                    messages = convert_messages_to_json(state.values.get("messages", []))
                    
                    # Criar checkpoint básico
                    checkpoint_id = f"{thread_id}-0"
                    created_at = datetime.utcnow().isoformat() + "Z"
                    
                    history_item = {
                        "values": {"messages": messages},
                        "checkpoint": {
                            "thread_id": thread_id,
                            "checkpoint_ns": "",
                            "checkpoint_id": checkpoint_id,
                            "checkpoint_map": {}
                        },
                        "metadata": {},
                        "created_at": created_at,
                        "next": [],
                        "tasks": [],
                        "parent_checkpoint": None
                    }
                    
                    history_items.append(history_item)
            
            # Aplicar filtro 'before' se fornecido
            if before:
                # Filtrar checkpoints anteriores (mais antigos) ao checkpoint_id especificado
                filtered_items = []
                for item in history_items:
                    if item["checkpoint"]["checkpoint_id"] == before:
                        break  # Parar quando encontrar o checkpoint especificado
                    filtered_items.append(item)  # Adicionar checkpoints anteriores
                history_items = filtered_items
            
            # Aplicar limite
            history_items = history_items[:limit]
            
        except Exception as state_error:
            logger.error(f"[LangGraphServer] get_thread_history: Erro ao recuperar histórico: {state_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"error": str(state_error)}), 500
        
        logger.info(f"[LangGraphServer] get_thread_history: {len(history_items)} item(ns) retornado(s) para thread {thread_id}")
        # Retornar array direto conforme especificação LangGraph Server
        # O LangSmith Studio espera um array de checkpoint objects
        return jsonify(history_items), 200
        
    except Exception as e:
        logger.error(f"[LangGraphServer] get_thread_history: Erro inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/runs', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/runs', methods=['GET', 'OPTIONS'])
def list_thread_runs(thread_id):
    """
    Lista runs de uma thread específica.
    
    Query parameters:
    - limit: Número de resultados (padrão: 10)
    - offset: Número de resultados para pular (padrão: 0)
    - status: Filtrar por status (pending, running, success, error, timeout, interrupted)
    
    Retorna array de runs com informações: run_id, thread_id, assistant_id, status, created_at, updated_at, metadata
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        # Parsear query parameters
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        status_filter = request.args.get('status', default=None, type=str)
        
        logger.info(f"[LangGraphServer] list_thread_runs: Listando runs da thread {thread_id} (limit={limit}, offset={offset}, status={status_filter})")
        
        # Por enquanto, retornar lista vazia pois não temos sistema de tracking de runs
        # Em produção, isso deveria consultar um sistema de persistência de runs
        # Por enquanto, podemos tentar inferir runs do histórico de estados do checkpointer
        
        runs = []
        
        try:
            graph_instance = get_graph()
            config = {"configurable": {"thread_id": thread_id}}
            
            # Tentar obter histórico de estados para inferir runs
            if hasattr(graph_instance, "get_state_history"):
                states = list(graph_instance.get_state_history(config))
                
                # Cada checkpoint pode representar um "run"
                for idx, state in enumerate(states):
                    if state is None:
                        continue
                    
                    # Gerar run_id baseado no checkpoint
                    run_id = f"{thread_id}-run-{idx}"
                    
                    # Determinar status baseado no estado
                    run_status = "success"  # Default
                    if hasattr(state, "next") and state.next:
                        run_status = "running"
                    
                    # Extrair timestamp se disponível
                    created_at = datetime.utcnow().isoformat() + "Z"
                    if hasattr(state, "created_at"):
                        created_at = state.created_at
                    elif hasattr(state, "ts"):
                        if isinstance(state.ts, (int, float)):
                            from datetime import datetime as dt
                            created_at = dt.fromtimestamp(state.ts).isoformat() + "Z"
                        else:
                            created_at = str(state.ts)
                    
                    run = {
                        "run_id": run_id,
                        "thread_id": thread_id,
                        "assistant_id": "agent",
                        "status": run_status,
                        "created_at": created_at,
                        "updated_at": created_at,
                        "metadata": {}
                    }
                    
                    # Aplicar filtro de status se fornecido
                    if status_filter and run["status"] != status_filter:
                        continue
                    
                    runs.append(run)
        except Exception as e:
            logger.warning(f"[LangGraphServer] list_thread_runs: Erro ao obter histórico de estados: {e}")
            # Continuar com lista vazia
        
        # Aplicar paginação
        total_runs = len(runs)
        runs = runs[offset:offset+limit]
        
        logger.info(f"[LangGraphServer] list_thread_runs: Retornando {len(runs)} runs (total: {total_runs}) para thread {thread_id}")
        
        # Retornar array direto conforme especificação LangGraph Server
        return jsonify(runs), 200
        
    except Exception as e:
        logger.error(f"[LangGraphServer] list_thread_runs: Erro inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/runs/<run_id>', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/runs/<run_id>', methods=['GET', 'OPTIONS'])
def get_thread_run(thread_id, run_id):
    """
    Obtém informações detalhadas de um run específico.
    
    Args:
        thread_id: ID da thread
        run_id: ID do run
    
    Retorna:
    {
        "run_id": "...",
        "thread_id": "...",
        "assistant_id": "...",
        "status": "success|running|error|pending|timeout|interrupted",
        "created_at": "...",
        "updated_at": "...",
        "metadata": {},
        "kwargs": {}
    }
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        logger.info(f"[LangGraphServer] get_thread_run: Buscando run {run_id} da thread {thread_id}")
        
        # Por enquanto, tentar inferir informações do run do histórico
        # Em produção, isso deveria consultar um sistema de persistência de runs
        try:
            graph_instance = get_graph()
            config = {"configurable": {"thread_id": thread_id}}
            
            # Tentar obter histórico para encontrar o run
            run_data = None
            if hasattr(graph_instance, "get_state_history"):
                states = list(graph_instance.get_state_history(config))
                
                # Procurar run_id no histórico (pode estar no formato thread_id-run-{idx})
                for idx, state in enumerate(states):
                    if state is None:
                        continue
                    
                    # Gerar run_id esperado
                    expected_run_id = f"{thread_id}-run-{idx}"
                    if expected_run_id == run_id or str(run_id) in str(state):
                        # Determinar status
                        run_status = "success"
                        if hasattr(state, "next") and state.next:
                            run_status = "running"
                        
                        # Extrair timestamp
                        created_at = datetime.utcnow().isoformat() + "Z"
                        if hasattr(state, "created_at"):
                            created_at = state.created_at
                        elif hasattr(state, "ts"):
                            if isinstance(state.ts, (int, float)):
                                from datetime import datetime as dt
                                created_at = dt.fromtimestamp(state.ts).isoformat() + "Z"
                            else:
                                created_at = str(state.ts)
                        
                        run_data = {
                            "run_id": run_id,
                            "thread_id": thread_id,
                            "assistant_id": "agent",
                            "status": run_status,
                            "created_at": created_at,
                            "updated_at": created_at,
                            "metadata": {},
                            "kwargs": {}
                        }
                        break
        except Exception as e:
            logger.warning(f"[LangGraphServer] get_thread_run: Erro ao obter informações do run: {e}")
        
        if not run_data:
            logger.warning(f"[LangGraphServer] get_thread_run: Run {run_id} não encontrado para thread {thread_id}")
            return jsonify({
                "error": "Run não encontrado",
                "message": f"Run {run_id} não existe para thread {thread_id}"
            }), 404
        
        logger.info(f"[LangGraphServer] get_thread_run: Run {run_id} encontrado (status: {run_data['status']})")
        return jsonify(run_data), 200
        
    except Exception as e:
        logger.error(f"[LangGraphServer] get_thread_run: Erro inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>', methods=['POST'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>', methods=['POST'])
def update_thread(thread_id):
    """
    Atualiza uma thread existente (adiciona nova mensagem e executa).
    
    Com checkpointer, o LangGraph automaticamente preserva o histórico de mensagens.
    Quando invoke é chamado com config contendo thread_id, ele:
    - Recupera estado anterior do checkpointer
    - Adiciona novas mensagens ao estado
    - Executa o grafo
    - Salva novo estado no checkpointer
    
    Formato esperado:
    {
        "input": {
            "messages": [{"role": "user", "content": "..."}]
        }
    }
    """
    start_time = datetime.utcnow()
    try:
        data, error_response = validate_request_body(['input'])
        if error_response:
            log_error("update_thread", "Request body inválido", {"thread_id": thread_id})
            return error_response
        
        log_request("update_thread", request.method, thread_id=thread_id, has_input=bool(data.get("input")))
        
        input_data = data.get("input", {})
        new_messages = input_data.get("messages", [])
        
        # Validar mensagens
        is_valid, error_response = validate_messages(new_messages)
        if not is_valid:
            log_error("update_thread", "Mensagens inválidas", {"thread_id": thread_id})
            return error_response
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] update_thread: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Config com thread_id para checkpointer
        config = data.get("config", {"configurable": {"thread_id": thread_id}})
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id
        _inject_regras_redirecionamento(config)
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in new_messages:
            if msg.get("role") == "user":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                langchain_messages.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                langchain_messages.append(SystemMessage(content=msg.get("content", "")))
        
        if not langchain_messages:
            logger.warning("[LangGraphServer] update_thread: Nenhuma mensagem válida encontrada")
            return jsonify({"error": "Pelo menos uma mensagem válida é necessária"}), 400
        
        # Com checkpointer, o LangGraph automaticamente:
        # 1. Recupera estado anterior (se existir)
        # 2. Adiciona novas mensagens ao estado
        # 3. Executa o grafo
        # 4. Salva novo estado
        logger.info(f"[LangGraphServer] update_thread: Executando grafo para thread {thread_id} com {len(langchain_messages)} nova(s) mensagem(ns)")
        result = graph_instance.invoke({"messages": langchain_messages}, config=config)
        
        # Converter todas as mensagens do resultado para formato de resposta
        # O resultado contém TODAS as mensagens (histórico + novas + resposta)
        all_messages = convert_messages_to_json(result.get("messages", []))
        
        result_dict = {
            "thread_id": thread_id,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "values": {
                "messages": all_messages
            }
        }
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("update_thread", 200, duration_ms, thread_id=thread_id, messages_count=len(all_messages))
        return jsonify(result_dict), 200
        
    except RuntimeError as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("update_thread", e, {"thread_id": thread_id, "duration_ms": duration_ms, "error_type": "RuntimeError"})
        return jsonify({"error": str(e), "message": "LangGraph não está disponível"}), 503
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("update_thread", e, {"thread_id": thread_id, "duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/runs/stream', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/runs/stream', methods=['POST', 'OPTIONS'])
def create_run_stream(thread_id):
    """
    Cria um run em uma thread existente e faz stream do output em tempo real.
    
    Formato esperado:
    {
        "assistant_id": "agent",
        "input": {
            "messages": [{"role": "user", "content": "..."}]
        },
        "stream_mode": "values",  # Opcional: "values", "updates", "messages"
        "stream_resumable": false,  # Opcional
        "on_disconnect": "cancel"  # Opcional: "cancel", "continue"
    }
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json(force=True, silent=True) or {}
        
        assistant_id = data.get("assistant_id", "agent")
        input_data = data.get("input", {})
        
        # Tentar obter mensagens de múltiplos formatos possíveis
        messages = input_data.get("messages", [])
        if not messages:
            # Tentar diretamente no data
            messages = data.get("messages", [])
        if not messages and isinstance(input_data, list):
            # Se input_data é uma lista, pode ser que as mensagens estejam diretamente lá
            messages = input_data
        
        stream_mode = data.get("stream_mode", "values")
        # stream_mode pode ser uma lista no LangGraph Studio
        if isinstance(stream_mode, list):
            stream_mode = stream_mode[0] if stream_mode else "values"
        
        stream_resumable = data.get("stream_resumable", False)
        on_disconnect = data.get("on_disconnect", "cancel")
        
        log_request("create_run_stream", request.method, thread_id=thread_id, assistant_id=assistant_id, 
                   messages_count=len(messages), stream_mode=stream_mode)
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] create_run_stream: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Config com thread_id para checkpointer (definir antes de usar)
        config = data.get("config", {"configurable": {"thread_id": thread_id}})
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id
        _inject_regras_redirecionamento(config)
        
        # Se não houver mensagens no input, tentar recuperar do estado atual da thread ou do histórico
        if not messages:
            logger.info(f"[LangGraphServer] create_run_stream: Nenhuma mensagem no input, tentando recuperar do estado da thread {thread_id}")
            try:
                # Primeiro, tentar recuperar do estado atual
                state = graph_instance.get_state(config)
                if state and state.values:
                    existing_messages = state.values.get("messages", [])
                    if existing_messages:
                        # Converter mensagens LangChain para formato JSON
                        messages = convert_messages_to_json(existing_messages)
                        logger.info(f"[LangGraphServer] create_run_stream: Recuperadas {len(messages)} mensagens do estado da thread")
                    else:
                        logger.info(f"[LangGraphServer] create_run_stream: Thread {thread_id} existe mas não tem mensagens no estado atual")
                else:
                    logger.info(f"[LangGraphServer] create_run_stream: Thread {thread_id} não encontrada no checkpointer")
                
                # Se ainda não houver mensagens, tentar recuperar do histórico
                if not messages:
                    logger.info(f"[LangGraphServer] create_run_stream: Tentando recuperar mensagens do histórico da thread {thread_id}")
                    try:
                        # Tentar usar get_state_history se disponível
                        if hasattr(graph_instance, "get_state_history"):
                            states = list(graph_instance.get_state_history(config))
                            # Pegar o último estado que tenha mensagens
                            for state in reversed(states):
                                if state and state.values:
                                    existing_messages = state.values.get("messages", [])
                                    if existing_messages:
                                        messages = convert_messages_to_json(existing_messages)
                                        logger.info(f"[LangGraphServer] create_run_stream: Recuperadas {len(messages)} mensagens do histórico da thread")
                                        break
                    except Exception as history_error:
                        logger.warning(f"[LangGraphServer] create_run_stream: Erro ao recuperar histórico: {history_error}")
                
                # Se ainda não houver mensagens, permitir criar run vazio
                if not messages:
                    logger.info(f"[LangGraphServer] create_run_stream: Nenhuma mensagem encontrada, criando run vazio")
            except Exception as state_error:
                logger.warning(f"[LangGraphServer] create_run_stream: Erro ao recuperar estado da thread: {state_error}")
                # Continuar com mensagens vazias - pode ser uma nova thread
                messages = []
        
        # Se ainda não houver mensagens, permitir continuar (pode ser um run vazio ou teste)
        if not messages:
            logger.info(f"[LangGraphServer] create_run_stream: Continuando com mensagens vazias para thread {thread_id}")
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    langchain_messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    langchain_messages.append(AIMessage(content=msg.get("content", "")))
                elif msg.get("role") == "system":
                    langchain_messages.append(SystemMessage(content=msg.get("content", "")))
            elif hasattr(msg, 'content'):
                # Já é uma mensagem LangChain
                langchain_messages.append(msg)
        
        # Gerar run_id
        run_id = str(uuid.uuid4())
        
        def generate():
            try:
                event_id = 0
                
                # Enviar evento de início do run
                yield f"id: {event_id}\n"
                yield f"event: run_start\n"
                yield f"data: {json.dumps({'run_id': run_id, 'thread_id': thread_id, 'assistant_id': assistant_id})}\n\n"
                event_id += 1
                
                # Stream dos eventos do grafo
                # Se não houver mensagens, passar estado vazio ou recuperar do checkpointer
                stream_input = {"messages": langchain_messages} if langchain_messages else {}
                for event in graph_instance.stream(stream_input, config=config):
                    try:
                        # LangGraph stream pode retornar tuplas (node_name, state) ou dicionários
                        event_data = {}
                        node_name = None
                        
                        # Processar formato de tupla: (node_name, state_dict)
                        if isinstance(event, tuple) and len(event) == 2:
                            node_name, state_obj = event
                            # Converter state object para dict se necessário
                            if isinstance(state_obj, dict):
                                event_data = state_obj
                            elif hasattr(state_obj, "values"):
                                event_data = {"values": state_obj.values}
                            elif hasattr(state_obj, "__dict__"):
                                event_data = state_obj.__dict__
                            else:
                                event_data = {"state": str(state_obj)}
                        # Processar formato de dicionário
                        elif isinstance(event, dict):
                            event_data = event
                            node_name = event.get("node") or event.get("__pregel_node")
                        else:
                            # Formato desconhecido, converter para string
                            event_data = {"raw": str(event)}
                        
                        # Extrair valores do estado de forma segura
                        state_values = {}
                        if isinstance(event_data, dict):
                            if "values" in event_data:
                                state_values = event_data["values"]
                            else:
                                state_values = event_data
                        
                        # Converter state_values para formato JSON serializável
                        # Isso converte mensagens LangChain (AIMessage, HumanMessage, etc.) para formato JSON
                        state_values_json = convert_state_to_json(state_values)
                        event_data_json = convert_state_to_json(event_data)
                        
                        # Formatar evento conforme stream_mode
                        if stream_mode == "values":
                            # Enviar apenas valores do estado
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'values': state_values_json})}\n\n"
                            event_id += 1
                        elif stream_mode == "updates":
                            # Enviar atualizações completas
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'update': event_data_json})}\n\n"
                            event_id += 1
                        else:
                            # Modo padrão: enviar tudo
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'event': event_data_json})}\n\n"
                            event_id += 1
                    except Exception as stream_error:
                        logger.error(f"[LangGraphServer] create_run_stream: Erro ao processar evento do stream: {stream_error}")
                        logger.error(f"[LangGraphServer] create_run_stream: Tipo do evento: {type(event)}, Valor: {event}")
                        # Continuar com próximo evento
                        continue
                
                # Enviar evento de conclusão do run
                yield f"id: {event_id}\n"
                yield f"event: run_end\n"
                yield f"data: {json.dumps({'run_id': run_id, 'status': 'completed'})}\n\n"
                
            except Exception as e:
                error_event = {
                    "event": "error",
                    "data": {
                        "run_id": run_id,
                        "error": str(e)
                    }
                }
                yield f"id: {event_id}\n"
                yield f"event: error\n"
                yield f"data: {json.dumps(error_event)}\n\n"
        
        headers = {
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream',
            'X-Run-ID': run_id  # Adicionar run_id no header para o LangSmith Studio
        }
        
        if stream_resumable:
            headers['X-Stream-Resumable'] = 'true'
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("create_run_stream", 200, duration_ms, thread_id=thread_id, run_id=run_id, stream_started=True)
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers=headers
        )
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("create_run_stream", e, {"thread_id": thread_id, "duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/runs/<run_id>/stream', methods=['GET', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/runs/<run_id>/stream', methods=['GET', 'OPTIONS'])
def join_run_stream(thread_id, run_id):
    """
    Junta-se a um stream de run existente.
    
    Permite resumir um stream a partir de um evento específico usando o header Last-Event-ID.
    
    Query parameters:
    - stream_mode: Modo de stream (values, updates, messages, etc.)
    - cancel_on_disconnect: Se true, cancela o run se cliente desconectar (padrão: false)
    
    Headers:
    - Last-Event-ID: ID do último evento recebido (para resumir stream)
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        stream_mode = request.args.get('stream_mode', 'values')
        cancel_on_disconnect = request.args.get('cancel_on_disconnect', 'false').lower() == 'true'
        last_event_id = request.headers.get('Last-Event-ID', None)
        
        logger.info(f"[LangGraphServer] join_run_stream: Juntando-se ao stream do run {run_id} da thread {thread_id} (last_event_id={last_event_id})")
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] join_run_stream: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Por enquanto, retornar erro pois não temos sistema de tracking de streams ativos
        # Em produção, isso deveria consultar streams ativos e retomar de onde parou
        logger.warning(f"[LangGraphServer] join_run_stream: Stream resumable não implementado completamente para run {run_id}")
        
        # Retornar erro informativo
        return jsonify({
            "error": "Stream não encontrado ou não resumable",
            "message": f"Run {run_id} não tem stream ativo ou não suporta resumir. Use POST /threads/{thread_id}/runs/stream para criar novo stream."
        }), 404
        
    except Exception as e:
        logger.error(f"[LangGraphServer] join_run_stream: Erro inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/threads/<thread_id>/stream', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/threads/<thread_id>/stream', methods=['POST', 'OPTIONS'])
def stream_thread(thread_id):
    """
    Executa thread em modo stream (Server-Sent Events).
    
    Formato esperado:
    {
        "input": {
            "messages": [{"role": "user", "content": "..."}]
        }
    }
    """
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Request body é obrigatório"}), 400
        
        input_data = data.get("input", {})
        messages = input_data.get("messages", [])
        
        if not messages:
            return jsonify({"error": "messages é obrigatório no input"}), 400
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] stream_thread: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                langchain_messages.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                langchain_messages.append(SystemMessage(content=msg.get("content", "")))
        
        # Config com thread_id para checkpointer
        config = data.get("config", {"configurable": {"thread_id": thread_id}})
        if "configurable" not in config:
            config["configurable"] = {}
        config["configurable"]["thread_id"] = thread_id
        _inject_regras_redirecionamento(config)
        
        def generate():
            try:
                for event in graph_instance.stream({"messages": langchain_messages}, config=config):
                    yield f"data: {json.dumps(event)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_event = {"event": "error", "data": {"error": str(e)}}
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"[LangGraphServer] Erro ao fazer stream da thread {thread_id}: {e}")
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/runs/wait', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/runs/wait', methods=['POST', 'OPTIONS'])
def create_stateless_run_wait():
    """
    Cria um run stateless (sem thread_id) e espera pela conclusão.
    
    Executa o grafo diretamente sem persistência de estado entre execuções.
    Útil para requisições one-shot onde não é necessário manter histórico.
    
    Formato esperado:
    {
        "assistant_id": "agent",
        "input": {
            "messages": [{"role": "user", "content": "..."}]
        },
        "metadata": {},
        "config": {}
    }
    
    Retorna resultado completo após conclusão.
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data, error_response = validate_request_body(['input'])
        if error_response:
            log_error("create_stateless_run_wait", "Request body inválido", {})
            return error_response
        
        assistant_id = data.get("assistant_id", "agent")
        input_data = data.get("input", {})
        messages = input_data.get("messages", [])
        metadata = data.get("metadata", {})
        config = data.get("config", {})
        
        log_request("create_stateless_run_wait", request.method, assistant_id=assistant_id, messages_count=len(messages))
        
        # Validar mensagens
        is_valid, error_response = validate_messages(messages)
        if not is_valid:
            log_error("create_stateless_run_wait", "Mensagens inválidas", {})
            return error_response
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] create_stateless_run_wait: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    langchain_messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    langchain_messages.append(AIMessage(content=msg.get("content", "")))
                elif msg.get("role") == "system":
                    langchain_messages.append(SystemMessage(content=msg.get("content", "")))
            elif hasattr(msg, 'content'):
                langchain_messages.append(msg)
        
        # Gerar run_id para tracking
        run_id = str(uuid.uuid4())
        
        if "configurable" not in config:
            config["configurable"] = {}
        _inject_regras_redirecionamento(config)
        
        # Executar grafo sem thread_id (stateless)
        logger.info(f"[LangGraphServer] create_stateless_run_wait: Executando grafo para run {run_id}")
        result = graph_instance.invoke({"messages": langchain_messages}, config=config)
        
        # Converter mensagens do resultado
        all_messages = convert_messages_to_json(result.get("messages", []))
        
        run_result = {
            "run_id": run_id,
            "assistant_id": assistant_id,
            "status": "success",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata,
            "values": {
                "messages": all_messages
            }
        }
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("create_stateless_run_wait", 200, duration_ms, run_id=run_id, messages_count=len(all_messages))
        return jsonify(run_result), 200
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("create_stateless_run_wait", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/runs/stream', methods=['POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/runs/stream', methods=['POST', 'OPTIONS'])
def create_stateless_run_stream():
    """
    Cria um run stateless (sem thread_id) e faz stream do output em tempo real.
    
    Executa o grafo diretamente sem persistência de estado, fazendo stream dos eventos.
    
    Formato esperado:
    {
        "assistant_id": "agent",
        "input": {
            "messages": [{"role": "user", "content": "..."}]
        },
        "stream_mode": "values",
        "metadata": {},
        "config": {}
    }
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data, error_response = validate_request_body(['input'])
        if error_response:
            log_error("create_stateless_run_stream", "Request body inválido", {})
            return error_response
        
        assistant_id = data.get("assistant_id", "agent")
        input_data = data.get("input", {})
        messages = input_data.get("messages", [])
        stream_mode = data.get("stream_mode", "values")
        metadata = data.get("metadata", {})
        config = data.get("config", {})
        
        log_request("create_stateless_run_stream", request.method, assistant_id=assistant_id, 
                   messages_count=len(messages), stream_mode=stream_mode)
        
        # Validar mensagens
        is_valid, error_response = validate_messages(messages)
        if not is_valid:
            log_error("create_stateless_run_stream", "Mensagens inválidas", {})
            return error_response
        
        # Obter grafo
        try:
            graph_instance = get_graph()
        except Exception as graph_error:
            logger.error(f"[LangGraphServer] create_stateless_run_stream: Erro ao obter grafo: {graph_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Grafo não disponível",
                "message": str(graph_error)
            }), 503
        
        # Converter mensagens para formato LangChain
        langchain_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    langchain_messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    langchain_messages.append(AIMessage(content=msg.get("content", "")))
                elif msg.get("role") == "system":
                    langchain_messages.append(SystemMessage(content=msg.get("content", "")))
            elif hasattr(msg, 'content'):
                langchain_messages.append(msg)
        
        # Gerar run_id
        run_id = str(uuid.uuid4())
        
        if "configurable" not in config:
            config["configurable"] = {}
        _inject_regras_redirecionamento(config)
        
        def generate():
            try:
                event_id = 0
                
                # Enviar evento de início do run
                yield f"id: {event_id}\n"
                yield f"event: run_start\n"
                yield f"data: {json.dumps({'run_id': run_id, 'assistant_id': assistant_id})}\n\n"
                event_id += 1
                
                # Stream dos eventos do grafo (sem thread_id)
                stream_input = {"messages": langchain_messages}
                for event in graph_instance.stream(stream_input, config=config):
                    try:
                        # Processar evento conforme formato
                        event_data = {}
                        node_name = None
                        
                        if isinstance(event, tuple) and len(event) == 2:
                            node_name, state_obj = event
                            if isinstance(state_obj, dict):
                                event_data = state_obj
                            elif hasattr(state_obj, "values"):
                                event_data = {"values": state_obj.values}
                            elif hasattr(state_obj, "__dict__"):
                                event_data = state_obj.__dict__
                            else:
                                event_data = {"state": str(state_obj)}
                        elif isinstance(event, dict):
                            event_data = event
                            node_name = event.get("node") or event.get("__pregel_node")
                        else:
                            event_data = {"raw": str(event)}
                        
                        # Extrair valores do estado
                        state_values = {}
                        if isinstance(event_data, dict):
                            if "values" in event_data:
                                state_values = event_data["values"]
                            else:
                                state_values = event_data
                        
                        # Converter state_values para formato JSON serializável
                        # Isso converte mensagens LangChain (AIMessage, HumanMessage, etc.) para formato JSON
                        state_values_json = convert_state_to_json(state_values)
                        event_data_json = convert_state_to_json(event_data)
                        
                        # Formatar evento conforme stream_mode
                        if stream_mode == "values":
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'values': state_values_json})}\n\n"
                            event_id += 1
                        elif stream_mode == "updates":
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'update': event_data_json})}\n\n"
                            event_id += 1
                        else:
                            yield f"id: {event_id}\n"
                            yield f"event: state_update\n"
                            yield f"data: {json.dumps({'run_id': run_id, 'node': node_name, 'event': event_data_json})}\n\n"
                            event_id += 1
                    except Exception as stream_error:
                        logger.error(f"[LangGraphServer] create_stateless_run_stream: Erro ao processar evento: {stream_error}")
                        continue
                
                # Enviar evento de conclusão
                yield f"id: {event_id}\n"
                yield f"event: run_end\n"
                yield f"data: {json.dumps({'run_id': run_id, 'status': 'completed'})}\n\n"
                
            except Exception as e:
                error_event = {
                    "event": "error",
                    "data": {
                        "run_id": run_id,
                        "error": str(e)
                    }
                }
                yield f"id: {event_id}\n"
                yield f"event: error\n"
                yield f"data: {json.dumps(error_event)}\n\n"
        
        headers = {
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream',
            'X-Run-ID': run_id
        }
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("create_stateless_run_stream", 200, duration_ms, run_id=run_id, stream_started=True)
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers=headers
        )
        
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("create_stateless_run_stream", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/debug/routes', methods=['GET'])
def debug_routes():
    """
    Endpoint de debug para listar todas as rotas registradas.
    Útil para verificar se as rotas estão sendo registradas corretamente.
    """
    try:
        from flask import current_app
        routes = []
        for rule in current_app.url_map.iter_rules():
            routes.append({
                'rule': rule.rule,
                'methods': list(rule.methods),
                'endpoint': rule.endpoint,
                'arguments': list(rule.arguments) if rule.arguments else []
            })
        
        # Filtrar rotas do langgraph_server
        langgraph_routes = [r for r in routes if 'langgraph_server' in r['endpoint'] or '/assistants' in r['rule'] or '/threads' in r['rule']]
        
        return jsonify({
            'all_routes_count': len(routes),
            'langgraph_routes': langgraph_routes,
            'all_routes': routes
        }), 200
    except Exception as e:
        logger.error(f"[LangGraphServer] debug_routes: Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@langgraph_server_bp.route('/debug/test-search', methods=['POST', 'GET'])
def debug_test_search():
    """
    Endpoint de debug para testar o handler search_assistants diretamente.
    """
    try:
        logger.info("[LangGraphServer] debug_test_search: Testando handler search_assistants")
        # Chamar o handler search_assistants diretamente
        return search_assistants()
    except Exception as e:
        logger.error(f"[LangGraphServer] debug_test_search: Erro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@langgraph_server_bp.route('/store/namespaces', methods=['GET', 'POST', 'OPTIONS'])
@langgraph_server_bp.route('/langgraph/store/namespaces', methods=['GET', 'POST', 'OPTIONS'])
def get_store_namespaces():
    """
    Obtém namespaces do store (checkpointer).
    
    O LangSmith Studio usa este endpoint para gerenciar namespaces do checkpointer.
    Por enquanto, retorna uma lista vazia ou um namespace padrão.
    
    Retorna lista de namespaces disponíveis.
    """
    start_time = datetime.utcnow()
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        log_request("get_store_namespaces", request.method)
        
        # Por enquanto, retornar lista vazia ou namespace padrão
        # Em produção, isso deveria consultar o checkpointer para listar namespaces
        namespaces = []
        
        # Se houver um grafo com checkpointer, tentar obter namespaces
        try:
            graph_instance = get_graph()
            if hasattr(graph_instance, 'checkpointer') and graph_instance.checkpointer:
                # Se o checkpointer tiver método para listar namespaces, usar
                # Por enquanto, apenas retornar lista vazia
                pass
        except Exception as e:
            logger.debug(f"[LangGraphServer] get_store_namespaces: Não foi possível obter namespaces do checkpointer: {e}")
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_response("get_store_namespaces", 200, duration_ms, namespaces_count=len(namespaces))
        logger.info(f"[LangGraphServer] get_store_namespaces: Retornando {len(namespaces)} namespace(s)")
        
        # Retornar array direto conforme especificação LangGraph Server
        return jsonify(namespaces), 200
            
    except Exception as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_error("get_store_namespaces", e, {"duration_ms": duration_ms})
        return jsonify({"error": str(e)}), 500


@langgraph_server_bp.route('/health', methods=['GET'])
@langgraph_server_bp.route('/langgraph/health', methods=['GET'])
def health_check():
    """Health check para verificar se o servidor LangGraph está disponível"""
    try:
        # Tentar obter grafo, mas não falhar se não estiver disponível
        graph_available = False
        graph_error = None
        try:
            graph_instance = get_graph()
            if graph_instance is not None:
                graph_available = True
        except Exception as e:
            graph_error = str(e)
            logger.warning(f"[LangGraphServer] health_check: Grafo não disponível: {e}")
        
        if graph_available:
            return jsonify({
                "status": "ok",
                "message": "LangGraph Server está disponível",
                "assistants": ["agent"],
                "graph_available": True
            }), 200
        else:
            return jsonify({
                "status": "partial",
                "message": "LangGraph Server está rodando, mas grafo não está disponível",
                "assistants": ["agent"],
                "graph_available": False,
                "error": graph_error
            }), 200  # Retornar 200 mesmo sem grafo, pois o servidor está funcionando
    except Exception as e:
        logger.error(f"[LangGraphServer] health_check: Erro inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
