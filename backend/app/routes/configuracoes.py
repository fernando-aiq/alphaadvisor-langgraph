from flask import Blueprint, request, jsonify
import copy
from app.utils.jwt_utils import get_user_id_from_token
from app.services.s3_service import get_config_from_s3, put_config_to_s3, is_s3_configured

configuracoes_bp = Blueprint('configuracoes', __name__)

# Configurações padrão
CONFIGURACOES_PADRAO = {
    'geral': {
        'modeloIA': 'gpt-4o',
        'tomConversa': 'formal',
        'tamanhoResposta': 'detalhada',
        'idioma': 'pt-BR',
        'ocultarValores': False,
        'confirmarAcoes': True,
        'escreverLogs': False
    },
    'ofertas': {
        'habilitarOfertas': True,
        'evitarOfertasSensiveis': True,
        'modoEducativo': False,
        'ofertasProativas': True,
        'perfilInvestidor': 'conservador',
        'estiloOfertasReativas': 'consultivo',
        'estiloOfertasProativas': 'leve',
        'turnosMinimos': 2,
        'minutosMinimos': 30,
        'tempoInatividade': 300,
        'maxOfertasProativas': 3,
        'horarioInicio': 9,
        'horarioFim': 18
    },
    'ferramentas': {
        'consultaSaldo': True,
        'carteiraAtual': True,
        'evolucaoCarteira': True,
        'ativosDisponiveis': True,
        'minhasOrdens': True,
        'meusResgates': True,
        'inicioCarteira': True,
        'simulacaoCDB': True
    },
    'performance': {
        'maxItens': 100,
        'maxChamadas': 10,
        'timeoutLLM': 30,
        'diasRetencao': 90
    },
    'alertas': {
        'alertasVencimento': True,
        'oportunidadesProativas': True,
        'alertasMercado': True
    },
    'agent_builder': {
        'persona': 'Você é o AlphaAdvisor, assessor virtual de investimentos do Banco Inter.',
        'instrucoes': 'Sua abordagem é consultiva, empática e educativa.',
        'regras': [],
        'exemplos': [],
        'intents': [],
        'intent_flows': {},
        'tools_enabled': {
            'obter_perfil': True,
            'obter_carteira': True,
            'analisar_adequacao': True,
            'analisar_alinhamento_objetivos': True,
            'analisar_diversificacao': True,
            'recomendar_rebalanceamento': True,
            'calcular_projecao': True,
            'buscar_oportunidades': True
        },
        'max_iterations': 5,
        'temperature': 0.7
    },
    'autonomia': {
        'nivel': 'assistido',
        'acoes': {
            'executar_ordens': False,
            'simular': True,
            'enviar_mensagens_externas': False,
            'criar_alertas': True,
            'modificar_carteira': False
        },
        'respostas': {
            'falar_sobre_precos': True,
            'falar_sobre_risco': True,
            'recomendar_produtos': True,
            'fornecer_projecoes': True,
            'comparar_produtos': True
        },
        'regras_redirecionamento': [
            'Solicitação de valores acima de R$ 100.000',
            'Reclamações ou insatisfação',
            'Solicitação de cancelamento de conta',
            'Questões legais ou regulatórias'
        ]
    }
}

# Armazenamento em memória (cache; S3 é a fonte de verdade quando configurado)
configuracoes_usuario = {}


def _get_config_for_user(user_id: str, fill_cache: bool = True):
    """
    Obtém configurações do usuário: S3 (se configurado) -> cache -> padrão.
    Se fill_cache=True e vier do S3, preenche configuracoes_usuario[user_id].
    """
    if is_s3_configured():
        from_s3 = get_config_from_s3(user_id)
        if from_s3 is not None:
            if fill_cache:
                configuracoes_usuario[user_id] = from_s3
            return from_s3
    # Fallback: cache ou padrão
    if user_id in configuracoes_usuario:
        return configuracoes_usuario[user_id]
    return copy.deepcopy(CONFIGURACOES_PADRAO)


@configuracoes_bp.route('/api/configuracoes', methods=['GET'])
def obter_configuracoes():
    """Obtém todas as configurações do usuário"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    user_id = user_id_from_token or request.args.get('user_id', 'default')

    config = _get_config_for_user(user_id)
    return jsonify(config), 200

@configuracoes_bp.route('/api/configuracoes', methods=['POST'])
def salvar_configuracoes():
    """Salva configurações do usuário (memória + S3 quando configurado)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    user_id = user_id_from_token or request.args.get('user_id', 'default')

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados de configuração são obrigatórios'}), 400

    # Garantir que temos config atual (S3 ou cache) antes de mesclar
    _get_config_for_user(user_id)
    if user_id not in configuracoes_usuario:
        configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)

    for secao, valores in data.items():
        if secao in configuracoes_usuario[user_id]:
            if isinstance(configuracoes_usuario[user_id][secao], dict) and isinstance(valores, dict):
                configuracoes_usuario[user_id][secao].update(valores)
            else:
                configuracoes_usuario[user_id][secao] = valores
        else:
            configuracoes_usuario[user_id][secao] = valores

    # Espelhar autonomia em "default" para o agente LangSmith
    if user_id != 'default' and 'autonomia' in data:
        if 'default' not in configuracoes_usuario:
            configuracoes_usuario['default'] = copy.deepcopy(CONFIGURACOES_PADRAO)
        if 'autonomia' not in configuracoes_usuario['default']:
            configuracoes_usuario['default']['autonomia'] = copy.deepcopy(CONFIGURACOES_PADRAO.get('autonomia', {}))
        configuracoes_usuario['default']['autonomia'].update(data['autonomia'])

    # Persistir no S3
    import logging
    _log = logging.getLogger(__name__)
    ok1 = put_config_to_s3(user_id, configuracoes_usuario[user_id])
    if not ok1:
        _log.warning("[Configuracoes] S3 put_config_to_s3 falhou para user_id=%s (bucket configurado?)", user_id)
    if user_id != 'default' and 'autonomia' in data:
        ok2 = put_config_to_s3('default', configuracoes_usuario['default'])
        if not ok2:
            _log.warning("[Configuracoes] S3 put_config_to_s3 falhou para default")

    return jsonify({
        'message': 'Configurações salvas com sucesso',
        'configuracoes': configuracoes_usuario[user_id]
    }), 200

@configuracoes_bp.route('/api/configuracoes/regras_redirecionamento', methods=['GET'])
def obter_regras_redirecionamento():
    """Retorna as regras de redirecionamento (handoff) e respostas permitidas. Usado pelo LangSmith/Studio.
    Sempre usa 'default' (configuradas na página Autonomia, persistidas no S3). Uma única chamada traz ambos."""
    config = _get_config_for_user('default')
    autonomia = config.get('autonomia', {}) or CONFIGURACOES_PADRAO.get('autonomia', {})
    regras = autonomia.get('regras_redirecionamento') or CONFIGURACOES_PADRAO.get('autonomia', {}).get('regras_redirecionamento', [])
    respostas = autonomia.get('respostas') or CONFIGURACOES_PADRAO.get('autonomia', {}).get('respostas', {})
    return jsonify({
        "regras_redirecionamento": regras,
        "respostas": respostas
    }), 200


@configuracoes_bp.route('/api/configuracoes/reset', methods=['POST'])
def resetar_configuracoes():
    """Reseta configurações para padrão (memória + S3 quando configurado)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    user_id = user_id_from_token or request.args.get('user_id', 'default')

    configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
    ok = put_config_to_s3(user_id, configuracoes_usuario[user_id])
    if not ok:
        import logging
        logging.getLogger(__name__).warning("[Configuracoes] S3 put_config_to_s3 falhou no reset user_id=%s", user_id)

    return jsonify({
        'message': 'Configurações resetadas',
        'configuracoes': CONFIGURACOES_PADRAO
    }), 200

@configuracoes_bp.route('/api/configuracoes/graph/current', methods=['GET'])
def obter_grafo_atual():
    """Obtém a estrutura atual do grafo LangGraph"""
    try:
        from app.services.langgraph_agent import LangGraphAgent
        
        # Tentar extrair user_id do token JWT no header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id_from_token = get_user_id_from_token(token) if token else None
        user_id = user_id_from_token or request.args.get('user_id', 'default')
        
        print(f"[Configuracoes] Obtendo grafo para user_id: {user_id}")
        
        # Obter configurações do usuário (S3 + cache ou padrão)
        user_config = _get_config_for_user(user_id)
        agent_builder_config = user_config.get('agent_builder', {})
        
        # Verificar se há grafo customizado
        custom_graph = agent_builder_config.get('graph_structure')
        if custom_graph:
            print(f"[Configuracoes] Usando grafo customizado para user_id: {user_id}")
        else:
            print(f"[Configuracoes] Usando grafo padrão para user_id: {user_id}")
        
        # Criar instância do LangGraphAgent para obter estrutura
        try:
            langgraph_agent = LangGraphAgent(custom_graph_config=agent_builder_config if custom_graph else None)
            graph_structure = langgraph_agent.get_graph_structure(custom_config=agent_builder_config if custom_graph else None)
            
            if not graph_structure:
                print("[Configuracoes] WARNING: graph_structure é None, retornando estrutura padrão")
                # Retornar estrutura padrão se None
                langgraph_agent_default = LangGraphAgent()
                graph_structure = langgraph_agent_default._get_default_graph_structure()
            
            print(f"[Configuracoes] Grafo obtido com sucesso: {len(graph_structure.get('nodes', []))} nós")
            return jsonify(graph_structure), 200
        except Exception as e:
            print(f"[Configuracoes] Erro ao criar LangGraphAgent: {e}")
            import traceback
            traceback.print_exc()
            # Retornar estrutura padrão em caso de erro
            langgraph_agent_default = LangGraphAgent()
            graph_structure = langgraph_agent_default._get_default_graph_structure()
            return jsonify(graph_structure), 200
            
    except Exception as e:
        import traceback
        print(f"[Configuracoes] Erro geral ao obter grafo: {e}")
        traceback.print_exc()
        # Tentar retornar estrutura padrão mesmo em caso de erro crítico
        try:
            from app.services.langgraph_agent import LangGraphAgent
            langgraph_agent_default = LangGraphAgent()
            graph_structure = langgraph_agent_default._get_default_graph_structure()
            return jsonify(graph_structure), 200
        except:
            return jsonify({'error': str(e), 'message': 'Erro ao obter estrutura do grafo'}), 500

@configuracoes_bp.route('/api/configuracoes/graph', methods=['POST'])
def salvar_grafo():
    """Salva a estrutura do grafo editado"""
    try:
        # Tentar extrair user_id do token JWT no header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id_from_token = get_user_id_from_token(token) if token else None
        user_id = user_id_from_token or request.args.get('user_id', 'default')
        
        data = request.get_json()
        if not data or 'graph_structure' not in data:
            return jsonify({'error': 'graph_structure é obrigatório'}), 400
        
        graph_structure = data['graph_structure']
        
        # Validar estrutura básica
        if 'nodes' not in graph_structure or 'edges' not in graph_structure:
            return jsonify({'error': 'Estrutura do grafo inválida'}), 400
        
        # Garantir config atual e mesclar
        _get_config_for_user(user_id)
        if user_id not in configuracoes_usuario:
            configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
        if 'agent_builder' not in configuracoes_usuario[user_id]:
            configuracoes_usuario[user_id]['agent_builder'] = {}
        configuracoes_usuario[user_id]['agent_builder']['graph_structure'] = graph_structure

        put_config_to_s3(user_id, configuracoes_usuario[user_id])

        return jsonify({
            'message': 'Grafo salvo com sucesso',
            'graph_structure': graph_structure
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500




