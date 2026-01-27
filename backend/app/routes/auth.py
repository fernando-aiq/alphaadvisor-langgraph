from flask import Blueprint, request, jsonify
from app.utils.jwt_utils import create_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login: aceita {email, password} e retorna {token}. Em produção, integrar com auth real."""
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip()
        password = (data.get('password') or data.get('senha') or '').strip()

        if not email or not password:
            return jsonify({'message': 'Email e senha são obrigatórios'}), 400

        # Gera token. Em produção: validar contra base de usuários ou IdP.
        user_id = email
        token = create_token(user_id=user_id, email=email)
        return jsonify({'token': token}), 200
    except Exception as e:
        print(f"[Auth] Erro no login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Erro ao processar login'}), 500
