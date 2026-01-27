from flask import Blueprint, request, jsonify
from app.utils.jwt_utils import get_user_id_from_token

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

# Armazenamento em memória (em produção, usar banco de dados)
configuracoes_usuario = {}

@configuracoes_bp.route('/api/configuracoes', methods=['GET'])
def obter_configuracoes():
    """Obtém todas as configurações do usuário"""
    # Tentar extrair user_id do token JWT no header
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    
    # Priorizar user_id do token, depois query param, depois default
    user_id = user_id_from_token or request.args.get('user_id', 'default')
    
    config = configuracoes_usuario.get(user_id, CONFIGURACOES_PADRAO.copy())
    return jsonify(config), 200

@configuracoes_bp.route('/api/configuracoes', methods=['POST'])
def salvar_configuracoes():
    """Salva configurações do usuário"""
    # Tentar extrair user_id do token JWT no header
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    
    # Priorizar user_id do token, depois query param, depois default
    user_id = user_id_from_token or request.args.get('user_id', 'default')
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados de configuração são obrigatórios'}), 400
    
    # Mesclar com configurações existentes
    if user_id not in configuracoes_usuario:
        import copy
        configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
    
    # Atualizar configurações
    for secao, valores in data.items():
        if secao in configuracoes_usuario[user_id]:
            if isinstance(configuracoes_usuario[user_id][secao], dict) and isinstance(valores, dict):
                configuracoes_usuario[user_id][secao].update(valores)
            else:
                configuracoes_usuario[user_id][secao] = valores
        else:
            configuracoes_usuario[user_id][secao] = valores
    
    return jsonify({
        'message': 'Configurações salvas com sucesso',
        'configuracoes': configuracoes_usuario[user_id]
    }), 200

@configuracoes_bp.route('/api/configuracoes/reset', methods=['POST'])
def resetar_configuracoes():
    """Reseta configurações para padrão"""
    # Tentar extrair user_id do token JWT no header
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    
    # Priorizar user_id do token, depois query param, depois default
    user_id = user_id_from_token or request.args.get('user_id', 'default')
    
    import copy
    configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
    
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
        
        # Obter configurações do usuário
        user_config = configuracoes_usuario.get(user_id, CONFIGURACOES_PADRAO.copy())
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
        
        # Mesclar com configurações existentes
        if user_id not in configuracoes_usuario:
            import copy
            configuracoes_usuario[user_id] = copy.deepcopy(CONFIGURACOES_PADRAO)
        
        # Atualizar graph_structure no agent_builder
        if 'agent_builder' not in configuracoes_usuario[user_id]:
            configuracoes_usuario[user_id]['agent_builder'] = {}
        
        configuracoes_usuario[user_id]['agent_builder']['graph_structure'] = graph_structure
        
        return jsonify({
            'message': 'Grafo salvo com sucesso',
            'graph_structure': graph_structure
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500




