from flask import Blueprint, request, jsonify
from app.services.ai_service import AIService
from app.utils.jwt_utils import get_user_id_from_token
from app.routes.configuracoes import configuracoes_usuario, CONFIGURACOES_PADRAO
import os

chat_bp = Blueprint('chat', __name__)
ai_service = AIService()

@chat_bp.route('/api/chat/debug', methods=['GET'])
def chat_debug():
    """Endpoint de debug para verificar configuração da OpenAI"""
    api_key = os.getenv('OPENAI_API_KEY', '')
    model = os.getenv('AI_MODEL', 'gpt-4o')
    
    # Verificar TraceabilityService
    traceability_status = {
        'available': hasattr(ai_service, 'traceability') and ai_service.traceability is not None,
        'traceability_object': str(ai_service.traceability) if hasattr(ai_service, 'traceability') else None
    }
    
    # Tentar importar TraceabilityService diretamente
    try:
        from app.services.traceability_service import TraceabilityService
        traceability_status['import_success'] = True
        try:
            test_trace = TraceabilityService()
            traceability_status['initialization_success'] = True
            traceability_status['traces_dir'] = str(test_trace.traces_dir) if hasattr(test_trace, 'traces_dir') else None
        except Exception as e:
            traceability_status['initialization_success'] = False
            traceability_status['initialization_error'] = str(e)
    except Exception as e:
        traceability_status['import_success'] = False
        traceability_status['import_error'] = str(e)
    
    return jsonify({
        'api_key_present': bool(api_key),
        'api_key_length': len(api_key) if api_key else 0,
        'api_key_preview': api_key[:10] + '...' if api_key and len(api_key) > 10 else 'N/A',
        'model': model,
        'client_available': ai_service._get_client() is not None,
        'agent_available': hasattr(ai_service, 'use_agent') and ai_service.use_agent,
        'agent_error': getattr(ai_service, 'agent_error', None),
        'last_client_error': getattr(ai_service, 'last_client_error', None),
        'last_openai_error': getattr(ai_service, 'last_openai_error', None),
        'traceability': traceability_status
    }), 200

# Endpoint de trace movido para trace_visualization.py
# Mantido aqui apenas para compatibilidade (redireciona)
@chat_bp.route('/api/chat/trace/<trace_id>', methods=['GET'])
def obter_trace(trace_id):
    """Recupera trace completo de uma conversa para auditoria (compatibilidade)"""
    try:
        from app.services.traceability_service import TraceabilityService
        traceability = TraceabilityService()
        trace = traceability.get_trace(trace_id)
        
        if not trace:
            return jsonify({'error': 'Trace não encontrado'}), 404
        
        return jsonify(trace), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            print("[Chat] ERRO: Request body vazio")
            return jsonify({
                'error': 'Request body é obrigatório',
                'response': 'Por favor, envie uma mensagem válida.',
                'message': 'Por favor, envie uma mensagem válida.'
            }), 400
        
        message = data.get('message', '')
        context = data.get('context', [])  # Histórico de mensagens anteriores
        
        print(f"[Chat] Recebida mensagem: {message}")
        print(f"[Chat] Tipo da mensagem: {type(message)}")
        print(f"[Chat] Mensagem vazia? {not message}")
        print(f"[Chat] Contexto recebido: {len(context) if context else 0} mensagens")
        
        if not message or not message.strip():
            print("[Chat] ERRO: Mensagem vazia")
            return jsonify({
                'error': 'Mensagem é obrigatória',
                'response': 'Por favor, envie uma mensagem não vazia.',
                'message': 'Por favor, envie uma mensagem não vazia.'
            }), 400
        
        # Obter configurações do agent_builder do usuário
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = get_user_id_from_token(token) if token else request.args.get('user_id', 'default')
        
        user_config = configuracoes_usuario.get(user_id, CONFIGURACOES_PADRAO.copy())
        agent_builder_config = user_config.get('agent_builder', {})
        
        # Processar mensagem com IA (passando contexto e configs do agent_builder)
        print("[Chat] Processando mensagem com AIService...")
        ai_result = ai_service.process_message(message, context=context, agent_builder_config=agent_builder_config)
        
        # Se o resultado for um dict (do AgentService), extrair informações
        if isinstance(ai_result, dict):
            response = ai_result.get('response', str(ai_result))
            trace_id = ai_result.get('trace_id', '')
            explicacao = ai_result.get('explicacao')
        else:
            # Se for string (fallback legacy), criar dict
            response = str(ai_result) if ai_result else "Desculpe, não consegui processar sua mensagem."
            trace_id = ''
            explicacao = None
        
        print(f"[Chat] Resposta gerada (tipo: {type(response)}): {response[:100] if response else 'VAZIA'}...")
        print(f"[Chat] Resposta vazia? {not response or not response.strip()}")
        
        # Garantir que temos uma resposta válida
        if not response or not response.strip():
            print("[Chat] AVISO: Resposta vazia do AIService, usando fallback")
            response = "Desculpe, não consegui processar sua mensagem. Por favor, tente novamente."
        
        # Garantir que retornamos sempre um JSON válido
        result = {
            'response': response,
            'message': response  # Para compatibilidade
        }
        
        # Adicionar trace_id se disponível
        if trace_id:
            result['trace_id'] = trace_id
        
        print(f"[Chat] Retornando resposta: {result}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[Chat] ERRO ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()
        
        # Sempre retornar uma resposta válida mesmo em caso de erro
        error_message = f'Erro ao processar mensagem: {str(e)}'
        return jsonify({
            'error': str(e), 
            'response': error_message,
            'message': error_message
        }), 500


