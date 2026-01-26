from flask import Blueprint, jsonify

cliente_bp = Blueprint('cliente', __name__)

# Dados mockados - Persona João (Conservador)
CARTEIRA = {
    'total': 157432.85,
    'dinheiroParado': 150000,
    'aporteMensal': 23715.36,
    'objetivo': {
        'valor': 1000000,
        'prazo': 5,
        'unidade': 'anos',
        'descricao': 'Atingir R$ 1.000.000 em 5 anos'
    },
    'distribuicao': {
        'rendaFixa': 100000,  # ~63%
        'rendaVariavel': 45000,  # ~29% (acima do ideal ~10-15%)
        'liquidez': 12432.85  # ~8% (abaixo do ideal ~15-20%)
    },
    'distribuicaoPercentual': {
        'rendaFixa': 63.5,
        'rendaVariavel': 28.6,
        'liquidez': 7.9
    },
    'investimentos': [
        {
            'id': 1,
            'nome': 'CDB XP 110% CDI',
            'tipo': 'CDB',
            'valor': 50000,
            'rentabilidade': '110% CDI',
            'vencimento': '2026-01-25',
            'classe': 'rendaFixa'
        },
        {
            'id': 2,
            'nome': 'LCI Banco do Brasil 95% CDI',
            'tipo': 'LCI',
            'valor': 30000,
            'rentabilidade': '95% CDI',
            'vencimento': '2027-03-15',
            'classe': 'rendaFixa'
        },
        {
            'id': 3,
            'nome': 'Tesouro IPCA+ 2029',
            'tipo': 'Tesouro Direto',
            'valor': 20000,
            'rentabilidade': 'IPCA + 5,5%',
            'vencimento': '2029-01-01',
            'classe': 'rendaFixa'
        },
        {
            'id': 4,
            'nome': 'Ações Petrobras (PETR4)',
            'tipo': 'Ações',
            'valor': 25000,
            'rentabilidade': 'Variável',
            'classe': 'rendaVariavel'
        },
        {
            'id': 5,
            'nome': 'Fundo Multimercado XP',
            'tipo': 'Fundo',
            'valor': 20000,
            'rentabilidade': 'Variável',
            'classe': 'rendaVariavel'
        },
        {
            'id': 6,
            'nome': 'Poupança',
            'tipo': 'Liquidez',
            'valor': 12432.85,
            'rentabilidade': '0%',
            'classe': 'liquidez'
        }
    ],
    'adequacaoPerfil': {
        'rendaVariavelAlta': True,  # Problema: 28.6% vs ideal 10-15%
        'liquidezBaixa': True,  # Problema: 7.9% vs ideal 15-20%
        'scoreAdequacao': 65,  # Score de 0-100
        'alertas': [
            {
                'tipo': 'risco',
                'severidade': 'media',
                'mensagem': 'Exposição a renda variável acima do recomendado para perfil conservador'
            },
            {
                'tipo': 'liquidez',
                'severidade': 'alta',
                'mensagem': 'Liquidez abaixo do ideal. Recomenda-se manter 15-20% em ativos líquidos'
            }
        ]
    },
    'instituicoes': [
        {
            'nome': 'XP Investimentos',
            'total': 100000,
            'rendaFixa': 80000,
            'rendaVariavel': 20000
        },
        {
            'nome': 'Banco do Brasil',
            'total': 30000,
            'rendaFixa': 30000,
            'rendaVariavel': 0
        },
        {
            'nome': 'Tesouro Direto',
            'total': 20000,
            'rendaFixa': 20000,
            'rendaVariavel': 0
        },
        {
            'nome': 'B3 (Ações)',
            'total': 25000,
            'rendaFixa': 0,
            'rendaVariavel': 25000
        },
        {
            'nome': 'Poupança',
            'total': 12432.85,
            'rendaFixa': 0,
            'rendaVariavel': 0
        }
    ]
}

PERFIL_JOAO = {
    'nome': 'João',
    'idade': 38,
    'profissao': 'Profissional de Tecnologia',
    'perfilInvestidor': 'conservador',
    'patrimonioInvestido': 157432.85,
    'dinheiroParado': 150000,
    'aporteMensal': 23715.36,
    'objetivo': {
        'valor': 1000000,
        'prazo': 5,
        'unidade': 'anos',
        'descricao': 'Atingir R$ 1.000.000 em 5 anos'
    },
    'comportamento': {
        'prefereEstabilidade': True,
        'naoGostaVolatilidade': True,
        'querClareza': True,
        'seSenteInseguro': True,
        'procuraEntender': True
    }
}

VENCIMENTOS = [
    {
        'id': 1,
        'nome': 'CDB XP 110% CDI',
        'valor': 50000,
        'dias': 12,
        'tipo': 'CDB',
        'vencimento': '2026-01-25'
    },
    {
        'id': 2,
        'nome': 'LCI Banco do Brasil 95% CDI',
        'valor': 30000,
        'dias': 425,
        'tipo': 'LCI',
        'vencimento': '2027-03-15'
    }
]

@cliente_bp.route('/api/cliente/carteira', methods=['GET'])
def obter_carteira():
    """Obtém carteira do cliente"""
    return jsonify(CARTEIRA), 200

@cliente_bp.route('/api/cliente/saldo', methods=['GET'])
def obter_saldo():
    """Obtém saldo do cliente"""
    return jsonify({
        'saldo': 150000,  # Dinheiro parado
        'saldoInvestido': 157432.85,
        'saldoTotal': 307432.85,
        'moeda': 'BRL'
    }), 200

@cliente_bp.route('/api/cliente/perfil', methods=['GET'])
def obter_perfil():
    """Obtém perfil completo do cliente"""
    return jsonify(PERFIL_JOAO), 200

@cliente_bp.route('/api/cliente/vencimentos', methods=['GET'])
def obter_vencimentos():
    """Obtém vencimentos próximos"""
    return jsonify({
        'vencimentos': VENCIMENTOS,
        'total': len(VENCIMENTOS)
    }), 200




