"""
Rotas para visualização de traces do agente.
Fornece endpoints para acessar dados de traces em diferentes formatos.
"""
from flask import Blueprint, jsonify, request
from app.services.traceability_service import TraceabilityService

trace_bp = Blueprint('trace', __name__)
traceability = TraceabilityService()

@trace_bp.route('/api/trace/<trace_id>', methods=['GET'])
def get_trace(trace_id):
    """Retorna trace completo"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    return jsonify(trace), 200

@trace_bp.route('/api/trace/<trace_id>/graph', methods=['GET'])
def get_trace_graph(trace_id):
    """Retorna dados do grafo para visualização"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    # Construir estrutura de grafo
    nodes = []
    edges = []
    
    # Nós do grafo
    graph_steps = trace.get('graph_steps', [])
    for step in graph_steps:
        node_name = step.get('node')
        if node_name:
            nodes.append({
                'id': node_name,
                'label': node_name.replace('_', ' ').title(),
                'timestamp': step.get('timestamp'),
                'duration_ms': step.get('duration_ms'),
                'data': {
                    'output': step.get('output'),
                    'state_snapshot': step.get('state_snapshot')
                }
            })
    
    # Edges do grafo
    edges_taken = trace.get('edges_taken', [])
    for edge in edges_taken:
        edges.append({
            'id': f"{edge.get('from')}-{edge.get('to')}",
            'source': edge.get('from'),
            'target': edge.get('to'),
            'label': edge.get('condition', ''),
            'timestamp': edge.get('timestamp')
        })
    
    # Adicionar nós padrão do grafo se não estiverem nos steps
    default_nodes = ['detect_intent', 'route_decision', 'bypass_analysis', 'react_agent', 'format_response']
    existing_node_ids = {n['id'] for n in nodes}
    for node_id in default_nodes:
        if node_id not in existing_node_ids:
            nodes.append({
                'id': node_id,
                'label': node_id.replace('_', ' ').title(),
                'timestamp': None,
                'duration_ms': None,
                'data': {}
            })
    
    # Handoff: incluir quando o trace tiver evento type=handoff
    handoff = None
    for e in trace.get('events', []):
        if e.get('type') == 'handoff':
            gs = trace.get('graph_steps')
            at_node = gs[-1]['node'] if gs else None
            handoff = {
                'occurred': True,
                'reason': e.get('payload', {}).get('reason', 'Não especificado'),
                'rule': e.get('payload', {}).get('rule', 'Não especificado'),
                'at_node': at_node
            }
            break
    
    return jsonify({
        'trace_id': trace_id,
        'nodes': nodes,
        'edges': edges,
        'route': trace.get('route'),
        'intent': trace.get('intent'),
        'status': trace.get('status'),
        'handoff': handoff
    }), 200

@trace_bp.route('/api/trace/<trace_id>/steps', methods=['GET'])
def get_trace_steps(trace_id):
    """Retorna passos detalhados do trace"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    # Obter todas as tool_calls para associar aos steps
    tool_calls = trace.get('tool_calls', [])
    
    # Criar mapa de tool_calls por timestamp aproximado (para associar aos graph_steps)
    # Tool calls geralmente acontecem dentro de um graph_step
    tool_calls_by_time = {}
    for tool_call in tool_calls:
        timestamp = tool_call.get('timestamp', '')
        if timestamp:
            # Usar timestamp como chave para associar
            tool_calls_by_time[timestamp] = tool_calls_by_time.get(timestamp, [])
            tool_calls_by_time[timestamp].append(tool_call)
    
    # Combinar graph_steps e reasoning_steps
    steps = []
    
    # Adicionar graph steps com tools associadas
    for step in trace.get('graph_steps', []):
        node_name = step.get('node')
        step_timestamp = step.get('timestamp', '')
        
        # Encontrar tool_calls que podem estar associadas a este step
        # Tools geralmente são chamadas dentro de bypass_analysis ou react_agent
        step_tools = []
        step_tool_calls = []
        
        # Se o step tem output com tools_used, usar isso
        output = step.get('output', {})
        if isinstance(output, dict) and 'tools_used' in output:
            step_tools = output.get('tools_used', [])
        
        # Também buscar tool_calls que podem estar relacionadas a este node
        # Por timestamp aproximado (dentro de 5 segundos)
        if step_timestamp:
            try:
                from datetime import datetime, timedelta
                step_time = datetime.fromisoformat(step_timestamp.replace('Z', '+00:00'))
                for tool_call in tool_calls:
                    tool_timestamp = tool_call.get('timestamp', '')
                    if tool_timestamp:
                        try:
                            tool_time = datetime.fromisoformat(tool_timestamp.replace('Z', '+00:00'))
                            # Se a tool foi chamada dentro de 5 segundos do step, associar
                            if abs((tool_time - step_time).total_seconds()) < 5:
                                step_tool_calls.append(tool_call)
                                if tool_call.get('tool_name') not in step_tools:
                                    step_tools.append(tool_call.get('tool_name'))
                        except:
                            pass
            except:
                pass
        
        steps.append({
            'type': 'graph_step',
            'node': node_name,
            'timestamp': step_timestamp,
            'duration_ms': step.get('duration_ms'),
            'input': step.get('state_snapshot', {}),
            'output': output,
            'tools_used': step_tools,
            'tool_calls': step_tool_calls  # Detalhes completos das tool calls
        })
    
    # Adicionar reasoning steps (ReAct)
    for step in trace.get('reasoning_steps', []):
        steps.append({
            'type': step.get('type'),  # 'thought', 'action', 'observation'
            'content': step.get('content'),
            'tool': step.get('tool'),
            'timestamp': step.get('timestamp'),
            'input': step.get('input'),
            'output': step.get('output')
        })
    
    # Ordenar por timestamp
    steps.sort(key=lambda x: x.get('timestamp', ''))
    
    return jsonify({
        'trace_id': trace_id,
        'steps': steps,
        'total_steps': len(steps)
    }), 200

@trace_bp.route('/api/trace/<trace_id>/timeline', methods=['GET'])
def get_trace_timeline(trace_id):
    """Retorna timeline cronológica do trace"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    timeline = []
    start_time = None
    
    # Processar graph_steps
    for step in trace.get('graph_steps', []):
        timestamp_str = step.get('timestamp')
        if timestamp_str:
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if start_time is None:
                    start_time = timestamp
                
                relative_time_ms = (timestamp - start_time).total_seconds() * 1000
                
                timeline.append({
                    'type': 'node_execution',
                    'node': step.get('node'),
                    'timestamp': timestamp_str,
                    'relative_time_ms': relative_time_ms,
                    'duration_ms': step.get('duration_ms'),
                    'label': step.get('node', '').replace('_', ' ').title()
                })
            except Exception as e:
                print(f"[TraceVisualization] Erro ao processar timestamp: {e}")
    
    # Processar reasoning_steps
    for step in trace.get('reasoning_steps', []):
        timestamp_str = step.get('timestamp')
        if timestamp_str:
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if start_time is None:
                    start_time = timestamp
                
                relative_time_ms = (timestamp - start_time).total_seconds() * 1000
                
                timeline.append({
                    'type': 'reasoning',
                    'reasoning_type': step.get('type'),
                    'tool': step.get('tool'),
                    'timestamp': timestamp_str,
                    'relative_time_ms': relative_time_ms,
                    'content': step.get('content', '')[:100]  # Primeiros 100 chars
                })
            except Exception as e:
                print(f"[TraceVisualization] Erro ao processar timestamp: {e}")
    
    # Ordenar por tempo relativo
    timeline.sort(key=lambda x: x.get('relative_time_ms', 0))
    
    return jsonify({
        'trace_id': trace_id,
        'start_time': trace.get('timestamp'),
        'end_time': trace.get('completed_at'),
        'timeline': timeline,
        'total_events': len(timeline)
    }), 200

@trace_bp.route('/api/trace/<trace_id>/tools', methods=['GET'])
def get_trace_tools(trace_id):
    """Retorna todas as tools utilizadas no trace com detalhes"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    tool_calls = trace.get('tool_calls', [])
    tools_used = trace.get('tools_used', [])
    
    # Calcular estatísticas
    total_tools = len(tool_calls)
    total_duration_ms = sum(tc.get('duration_ms', 0) or 0 for tc in tool_calls)
    unique_tools = list(set(tc.get('tool_name') for tc in tool_calls if tc.get('tool_name')))
    
    # Agrupar tools por nome para estatísticas
    tools_stats = {}
    for tool_call in tool_calls:
        tool_name = tool_call.get('tool_name')
        if tool_name:
            if tool_name not in tools_stats:
                tools_stats[tool_name] = {
                    'count': 0,
                    'total_duration_ms': 0,
                    'calls': []
                }
            tools_stats[tool_name]['count'] += 1
            tools_stats[tool_name]['total_duration_ms'] += (tool_call.get('duration_ms', 0) or 0)
            tools_stats[tool_name]['calls'].append(tool_call)
    
    return jsonify({
        'trace_id': trace_id,
        'tools_used': tools_used,  # Lista simples de nomes
        'tool_calls': tool_calls,  # Lista completa com detalhes
        'statistics': {
            'total_tools': total_tools,
            'unique_tools': len(unique_tools),
            'total_duration_ms': total_duration_ms,
            'average_duration_ms': total_duration_ms / total_tools if total_tools > 0 else 0,
            'tools_stats': tools_stats  # Estatísticas por tool
        }
    }), 200

@trace_bp.route('/api/trace/<trace_id>/help', methods=['GET'])
def get_trace_help(trace_id):
    """Retorna explicações e ajuda sobre o trace"""
    trace = traceability.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace não encontrado'}), 404
    
    help_data = {
        'trace_id': trace_id,
        'explanations': {
            'nodes': {
                'detect_intent': {
                    'name': 'Detect Intent',
                    'description': 'Detecta a intenção da mensagem do usuário usando análise de palavras-chave. Identifica se a pergunta é sobre carteira, adequação, diversificação, etc.',
                    'color': '#4CAF50'
                },
                'route_decision': {
                    'name': 'Route Decision',
                    'description': 'Decide qual rota seguir baseado na intenção detectada. Pode escolher "bypass" para análises simples ou "react" para raciocínio complexo.',
                    'color': '#2196F3'
                },
                'bypass_analysis': {
                    'name': 'Bypass Analysis',
                    'description': 'Análise direta sem agente ReAct. Usado para intenções simples como obter carteira, onde uma sequência fixa de ferramentas é suficiente.',
                    'color': '#FF9800'
                },
                'react_agent': {
                    'name': 'React Agent',
                    'description': 'Agente ReAct que usa ferramentas e raciocina passo a passo. Usado para perguntas complexas que requerem múltiplas iterações de pensamento, ação e observação.',
                    'color': '#9C27B0'
                },
                'format_response': {
                    'name': 'Format Response',
                    'description': 'Formata a resposta final para o usuário, garantindo que seja clara, estruturada e útil.',
                    'color': '#F44336'
                }
            },
            'step_types': {
                'graph_step': {
                    'name': 'Graph Step',
                    'description': 'Execução de um nó do grafo LangGraph. Mostra quando cada nó foi executado e seus resultados.',
                    'icon': '🔷'
                },
                'thought': {
                    'name': 'Thought',
                    'description': 'Raciocínio do agente ReAct - o que o agente está pensando antes de tomar uma ação.',
                    'icon': '💭'
                },
                'action': {
                    'name': 'Action',
                    'description': 'Ação executada - chamada de uma ferramenta (tool) para obter informações ou realizar uma análise.',
                    'icon': '⚡'
                },
                'observation': {
                    'name': 'Observation',
                    'description': 'Observação/resultado de uma ação - o que a ferramenta retornou após ser executada.',
                    'icon': '👁️'
                }
            },
            'fields': {
                'intent': {
                    'name': 'Intent',
                    'description': 'Intenção detectada da mensagem (ex: carteira_analysis, buscar_oportunidades)'
                },
                'route': {
                    'name': 'Route',
                    'description': 'Rota escolhida pelo grafo (bypass, react, llm_direct)'
                },
                'status': {
                    'name': 'Status',
                    'description': 'Status do trace (in_progress, completed, error)'
                }
            }
        },
        'trace_info': {
            'intent': trace.get('intent'),
            'route': trace.get('route'),
            'status': trace.get('status'),
            'tools_used': trace.get('tools_used', [])
        }
    }
    
    return jsonify(help_data), 200

@trace_bp.route('/api/traces', methods=['GET'])
def list_traces():
    """Lista traces recentes"""
    limit = request.args.get('limit', 50, type=int)
    traces = traceability.list_traces(limit=limit)
    
    return jsonify({
        'traces': traces,
        'total': len(traces)
    }), 200

