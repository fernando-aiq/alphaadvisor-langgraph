"""
Rotas para o Agent Builder conversacional estilo LangSmith
"""
from flask import Blueprint, request, jsonify
from app.utils.jwt_utils import get_user_id_from_token
from app.services.agent_builder_service import AgentBuilderService
from app.routes.configuracoes import configuracoes_usuario, CONFIGURACOES_PADRAO
import copy

agent_builder_bp = Blueprint('agent_builder', __name__)
builder_service = AgentBuilderService()

def get_user_config(user_id: str) -> dict:
    """Obtém configuração do usuário"""
    if user_id not in configuracoes_usuario:
        configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
    return configuracoes_usuario[user_id]

def get_agent_builder_config(user_id: str) -> dict:
    """Obtém configuração do agent builder do usuário"""
    user_config = get_user_config(user_id)
    return user_config.get('agent_builder', CONFIGURACOES_PADRAO['agent_builder'].copy())

@agent_builder_bp.route('/api/agent-builder/chat', methods=['POST'])
def builder_chat():
    """Processa mensagem do builder conversacional"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        message = data.get('message', '')
        context = data.get('context', [])
        
        # Obter configuração atual
        current_config = get_agent_builder_config(user_id)
        
        # Processar mensagem do builder
        result = builder_service.process_builder_message(message, current_config, context)
        
        # Aplicar atualizações se houver
        if result.get('config_updates'):
            updated_config = builder_service.apply_config_updates(current_config, result['config_updates'])
            
            # Salvar configuração atualizada
            user_config = get_user_config(user_id)
            user_config['agent_builder'] = updated_config
        
        return jsonify({
            'response': result.get('response', ''),
            'action': result.get('action'),
            'config': get_agent_builder_config(user_id)
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro no chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/config', methods=['GET'])
def get_config():
    """Obtém configuração atual do agente"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        config = get_agent_builder_config(user_id)
        
        # Adicionar informações de tools disponíveis
        available_tools = builder_service.get_available_tools()
        for tool in available_tools:
            tool['enabled'] = config.get('tools_enabled', {}).get(tool['id'], False)
        
        return jsonify({
            'config': config,
            'available_tools': available_tools
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao obter config: {e}")
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/config', methods=['POST'])
def save_config():
    """Salva configuração do agente"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        data = request.get_json()
        if not data or 'config' not in data:
            return jsonify({'error': 'Configuração é obrigatória'}), 400
        
        config = data['config']
        
        # Validar e salvar
        user_config = get_user_config(user_id)
        user_config['agent_builder'] = config
        
        return jsonify({
            'message': 'Configuração salva com sucesso',
            'config': config
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao salvar config: {e}")
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/tools', methods=['GET'])
def list_tools():
    """Lista tools disponíveis"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        available_tools = builder_service.get_available_tools()
        config = get_agent_builder_config(user_id)
        
        # Marcar tools habilitadas
        for tool in available_tools:
            tool['enabled'] = config.get('tools_enabled', {}).get(tool['id'], False)
        
        return jsonify({
            'tools': available_tools
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao listar tools: {e}")
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/tools', methods=['POST'])
def update_tool():
    """Adiciona ou atualiza uma tool"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        data = request.get_json()
        if not data or 'tool_id' not in data:
            return jsonify({'error': 'tool_id é obrigatório'}), 400
        
        tool_id = data['tool_id']
        enabled = data.get('enabled', True)
        
        # Atualizar configuração
        config = get_agent_builder_config(user_id)
        if 'tools_enabled' not in config:
            config['tools_enabled'] = {}
        
        config['tools_enabled'][tool_id] = enabled
        
        # Salvar
        user_config = get_user_config(user_id)
        user_config['agent_builder'] = config
        
        return jsonify({
            'message': f'Tool {tool_id} {"habilitada" if enabled else "desabilitada"} com sucesso',
            'config': config
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao atualizar tool: {e}")
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/tools/<tool_id>', methods=['DELETE'])
def remove_tool(tool_id):
    """Remove uma tool da configuração"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        config = get_agent_builder_config(user_id)
        if 'tools_enabled' in config and tool_id in config['tools_enabled']:
            del config['tools_enabled'][tool_id]
            
            # Salvar
            user_config = get_user_config(user_id)
            user_config['agent_builder'] = config
        
        return jsonify({
            'message': f'Tool {tool_id} removida com sucesso',
            'config': config
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao remover tool: {e}")
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/test', methods=['POST'])
def test_agent():
    """Testa o agente com uma mensagem"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        message = data.get('message', '')
        context = data.get('context', [])
        
        # Obter configuração atual
        config = get_agent_builder_config(user_id)
        
        # Testar agente
        result = builder_service.test_agent(message, config, context)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao testar agente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@agent_builder_bp.route('/api/agent-builder/subagents', methods=['POST'])
def manage_subagents():
    """Cria ou gerencia subagentes"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        data = request.get_json()
        action = data.get('action', 'create')  # create, update, delete
        
        # Por enquanto, retornar sucesso (implementação futura)
        return jsonify({
            'message': 'Funcionalidade de subagentes será implementada em breve',
            'action': action
        }), 200
        
    except Exception as e:
        print(f"[AgentBuilder] Erro ao gerenciar subagentes: {e}")
        return jsonify({'error': str(e)}), 500

