from flask import Blueprint, jsonify

oportunidades_bp = Blueprint('oportunidades', __name__)

# Dados mockados de oportunidades
OPORTUNIDADES = [
    {
        'id': 1,
        'nome': 'CDB XP 110% CDI',
        'rentabilidade': '110% CDI',
        'liquidez': 'Diária',
        'valorMinimo': 1000,
        'prazo': '2 anos',
        'tipo': 'CDB',
        'destaque': True
    },
    {
        'id': 2,
        'nome': 'Tesouro Selic 2029',
        'rentabilidade': 'SELIC + 0,1%',
        'liquidez': 'Governo Federal',
        'valorMinimo': 100,
        'prazo': '01/01/2029',
        'tipo': 'Tesouro Direto',
        'destaque': False
    },
    {
        'id': 3,
        'nome': 'LCI XP 95% CDI',
        'rentabilidade': '95% CDI',
        'liquidez': 'Isenção: IR e IOF',
        'valorMinimo': 5000,
        'prazo': '3 anos',
        'tipo': 'LCI',
        'destaque': False
    },
    {
        'id': 4,
        'nome': 'Fundo XP Dividendos',
        'rentabilidade': 'IPCA + 4,5%',
        'liquidez': 'Multimercado',
        'valorMinimo': 500,
        'prazo': 'D+1',
        'tipo': 'Fundo',
        'destaque': False
    }
]

@oportunidades_bp.route('/api/oportunidades', methods=['GET'])
def listar_oportunidades():
    """Lista todas as oportunidades disponíveis"""
    return jsonify({
        'oportunidades': OPORTUNIDADES,
        'total': len(OPORTUNIDADES)
    }), 200

@oportunidades_bp.route('/api/oportunidades/<int:oportunidade_id>', methods=['GET'])
def obter_oportunidade(oportunidade_id):
    """Obtém detalhes de uma oportunidade específica"""
    oportunidade = next((o for o in OPORTUNIDADES if o['id'] == oportunidade_id), None)
    
    if not oportunidade:
        return jsonify({'error': 'Oportunidade não encontrada'}), 404
    
    return jsonify(oportunidade), 200

@oportunidades_bp.route('/api/oportunidades/destaque', methods=['GET'])
def listar_destaques():
    """Lista apenas oportunidades em destaque"""
    destaques = [o for o in OPORTUNIDADES if o.get('destaque', False)]
    return jsonify({
        'oportunidades': destaques,
        'total': len(destaques)
    }), 200




