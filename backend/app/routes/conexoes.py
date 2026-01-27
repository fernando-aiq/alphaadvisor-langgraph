from flask import Blueprint, request, jsonify
from app.utils.jwt_utils import get_user_id_from_token
from datetime import datetime
import uuid

conexoes_bp = Blueprint('conexoes', __name__)

# Armazenamento em memória (em produção, usar banco de dados)
conexoes_usuario = {}

def get_user_id():
    """Extrai user_id do token JWT ou query param"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_from_token = get_user_id_from_token(token) if token else None
    return user_id_from_token or request.args.get('user_id', 'default')

def get_open_finance_mock():
    """Retorna conexão Open Finance mockada com dados de conta"""
    return {
        'id': 'mock-open-finance-001',
        'nome': 'Open Finance - Banco do Brasil',
        'tipo': 'open_finance',
        'status': 'ativo',
        'configuracao': {
            'banco': 'Banco do Brasil',
            'agencia': '1234-5',
            'conta': '12345-6',
            'tipo_conta': 'Conta Corrente',
            'saldo_disponivel': 50000.00,
            'ultima_sincronizacao': datetime.now().isoformat()
        },
        'created_at': (datetime.now().replace(day=15, hour=8, minute=0, second=0, microsecond=0)).isoformat(),
        'updated_at': datetime.now().isoformat()
    }

@conexoes_bp.route('/api/conexoes', methods=['GET'])
def listar_conexoes():
    """Lista todas as conexões do usuário"""
    user_id = get_user_id()
    conexoes = conexoes_usuario.get(user_id, [])
    
    # Se não houver conexões, retornar conexão Open Finance mockada
    if len(conexoes) == 0:
        conexoes = [get_open_finance_mock()]
    
    return jsonify({
        'conexoes': conexoes,
        'total': len(conexoes)
    }), 200

@conexoes_bp.route('/api/conexoes', methods=['POST'])
def criar_conexao():
    """Cria uma nova conexão"""
    user_id = get_user_id()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados da conexão são obrigatórios'}), 400
    
    # Validar campos obrigatórios
    if 'nome' not in data or 'tipo' not in data:
        return jsonify({'error': 'Nome e tipo são obrigatórios'}), 400
    
    # Criar nova conexão
    nova_conexao = {
        'id': str(uuid.uuid4()),
        'nome': data['nome'],
        'tipo': data['tipo'],
        'status': data.get('status', 'ativo'),
        'configuracao': data.get('configuracao', {}),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Inicializar lista se não existir
    if user_id not in conexoes_usuario:
        conexoes_usuario[user_id] = []
    
    conexoes_usuario[user_id].append(nova_conexao)
    
    return jsonify({
        'message': 'Conexão criada com sucesso',
        'conexao': nova_conexao
    }), 201

@conexoes_bp.route('/api/conexoes/<conexao_id>', methods=['PUT'])
def atualizar_conexao(conexao_id):
    """Atualiza uma conexão existente"""
    user_id = get_user_id()
    data = request.get_json()
    
    if user_id not in conexoes_usuario:
        return jsonify({'error': 'Nenhuma conexão encontrada para este usuário'}), 404
    
    conexoes = conexoes_usuario[user_id]
    conexao = next((c for c in conexoes if c['id'] == conexao_id), None)
    
    if not conexao:
        return jsonify({'error': 'Conexão não encontrada'}), 404
    
    # Atualizar campos permitidos
    if 'nome' in data:
        conexao['nome'] = data['nome']
    if 'tipo' in data:
        conexao['tipo'] = data['tipo']
    if 'status' in data:
        conexao['status'] = data['status']
    if 'configuracao' in data:
        conexao['configuracao'] = {**conexao.get('configuracao', {}), **data['configuracao']}
    
    conexao['updated_at'] = datetime.now().isoformat()
    
    return jsonify({
        'message': 'Conexão atualizada com sucesso',
        'conexao': conexao
    }), 200

@conexoes_bp.route('/api/conexoes/<conexao_id>', methods=['DELETE'])
def remover_conexao(conexao_id):
    """Remove uma conexão"""
    user_id = get_user_id()
    
    if user_id not in conexoes_usuario:
        return jsonify({'error': 'Nenhuma conexão encontrada para este usuário'}), 404
    
    conexoes = conexoes_usuario[user_id]
    conexao = next((c for c in conexoes if c['id'] == conexao_id), None)
    
    if not conexao:
        return jsonify({'error': 'Conexão não encontrada'}), 404
    
    conexoes_usuario[user_id] = [c for c in conexoes if c['id'] != conexao_id]
    
    return jsonify({
        'message': 'Conexão removida com sucesso'
    }), 200

