from flask import Blueprint, jsonify
from datetime import datetime, timedelta

alertas_bp = Blueprint('alertas', __name__)

# Dados mockados de alertas
ALERTAS = [
    {
        'id': 1,
        'tipo': 'vencimento',
        'titulo': 'Vencimento de CDB em 3 dias',
        'mensagem': 'Seu CDB XP 110% CDI vence em 3 dias. Considere renovar ou resgatar para não perder a liquidez.',
        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
        'urgente': True,
        'acoes': ['Renovar', 'Resgatar']
    },
    {
        'id': 2,
        'tipo': 'queda',
        'titulo': 'Queda significativa na carteira',
        'mensagem': 'Sua carteira teve uma queda de -2,3% hoje. Considere rebalancear seus investimentos.',
        'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
        'urgente': True,
        'acoes': ['Rebalancear', 'Ver Análise']
    },
    {
        'id': 3,
        'tipo': 'oportunidade',
        'titulo': 'Novo CDB com taxa especial',
        'mensagem': 'CDB XP 115% CDI disponível apenas hoje com taxa promocional. Aproveite!',
        'timestamp': datetime.now().isoformat(),
        'urgente': False,
        'acoes': ['Investir Agora', 'Simular']
    },
    {
        'id': 4,
        'tipo': 'recomendacao',
        'titulo': 'Diversificação da carteira',
        'mensagem': 'Sua carteira está muito concentrada em renda fixa. Considere diversificar com fundos multimercado.',
        'timestamp': (datetime.now() - timedelta(days=2)).isoformat(),
        'urgente': False,
        'acoes': ['Ver Sugestões', 'Ignorar']
    },
    {
        'id': 5,
        'tipo': 'mercado',
        'titulo': 'Selic pode subir na próxima reunião',
        'mensagem': 'Analistas preveem alta de 0,25% na Selic. CDBs e Tesouro Selic podem ficar mais atrativos.',
        'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
        'urgente': False,
        'acoes': ['Ver Impacto', 'Aguardar']
    }
]

@alertas_bp.route('/api/alertas', methods=['GET'])
def listar_alertas():
    """Lista todos os alertas"""
    tipo = request.args.get('tipo')
    urgente = request.args.get('urgente')
    
    alertas = ALERTAS.copy()
    
    if tipo:
        alertas = [a for a in alertas if a['tipo'] == tipo]
    
    if urgente:
        urgente_bool = urgente.lower() == 'true'
        alertas = [a for a in alertas if a['urgente'] == urgente_bool]
    
    return jsonify({
        'alertas': alertas,
        'total': len(alertas)
    }), 200

@alertas_bp.route('/api/alertas/<int:alerta_id>', methods=['GET'])
def obter_alerta(alerta_id):
    """Obtém detalhes de um alerta específico"""
    alerta = next((a for a in ALERTAS if a['id'] == alerta_id), None)
    
    if not alerta:
        return jsonify({'error': 'Alerta não encontrado'}), 404
    
    return jsonify(alerta), 200

@alertas_bp.route('/api/alertas/urgentes', methods=['GET'])
def listar_urgentes():
    """Lista apenas alertas urgentes"""
    urgentes = [a for a in ALERTAS if a['urgente']]
    return jsonify({
        'alertas': urgentes,
        'total': len(urgentes)
    }), 200




