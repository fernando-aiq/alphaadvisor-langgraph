from flask import Blueprint, jsonify, request

assessor_bp = Blueprint('assessor', __name__)

# Dados mockados
CLIENTES = [
    {
        'id': 1,
        'nome': 'João Silva',
        'cpf': '***.***.***-12',
        'status': 'ativo',
        'carteira': {
            'total': 350000,
            'rendaFixa': 200000,
            'rendaVariavel': 150000
        }
    },
    {
        'id': 2,
        'nome': 'Maria Santos',
        'cpf': '***.***.***-34',
        'status': 'ativo',
        'carteira': {
            'total': 250000,
            'rendaFixa': 180000,
            'rendaVariavel': 70000
        }
    }
]

METRICAS = {
    'ofertas': {
        'change': '+12%',
        'value': 156,
        'amount': 8700000,
        'label': 'ofertas'
    },
    'alertas': {
        'change': '+8%',
        'value': 89,
        'conversao': 57.1,
        'label': 'alertas'
    },
    'tempo': {
        'change': '+15%',
        'horas': 22,
        'clientes': 55,
        'label': 'tempo economizado'
    }
}

@assessor_bp.route('/api/assessor/clientes', methods=['GET'])
def listar_clientes():
    """Lista todos os clientes do assessor"""
    return jsonify({
        'clientes': CLIENTES,
        'total': len(CLIENTES)
    }), 200

@assessor_bp.route('/api/assessor/clientes/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    """Obtém detalhes de um cliente específico"""
    cliente = next((c for c in CLIENTES if c['id'] == cliente_id), None)
    
    if not cliente:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    
    return jsonify(cliente), 200

@assessor_bp.route('/api/assessor/metricas', methods=['GET'])
def obter_metricas():
    """Obtém métricas de performance do assessor"""
    periodo = request.args.get('periodo', 'hoje')
    
    return jsonify({
        'metricas': METRICAS,
        'periodo': periodo
    }), 200

@assessor_bp.route('/api/assessor/comparacao', methods=['GET'])
def obter_comparacao():
    """Obtém comparação com equipe"""
    return jsonify({
        'conversao': {
            'voce': 85,
            'equipe': 65,
            'diferenca': 33
        }
    }), 200

