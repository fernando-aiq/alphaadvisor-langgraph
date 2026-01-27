"""
Utilitários para JWT: criar, decodificar e extrair informações do usuário
"""
import base64
import json
import os
from typing import Optional, Dict

def _get_jwt_secret() -> str:
    return os.getenv('JWT_SECRET', 'dev-secret-change-in-production')

def create_token(user_id: str, email: str = '') -> str:
    """Cria um JWT com user_id e email no payload. Uso: login."""
    try:
        import jwt
        payload = {'sub': email or user_id, 'user_id': user_id, 'email': email or user_id}
        return jwt.encode(
            payload,
            _get_jwt_secret(),
            algorithm='HS256'
        )
    except Exception as e:
        print(f"[JWT Utils] Erro ao criar token: {e}")
        raise

def decode_jwt_payload(token: str) -> Optional[Dict]:
    """
    Decodifica o payload de um JWT sem verificar assinatura.
    Retorna None se o token for inválido.
    """
    try:
        # JWT tem formato: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decodificar payload (segunda parte)
        payload = parts[1]
        # Adicionar padding se necessário
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"[JWT Utils] Erro ao decodificar token: {e}")
        return None

def get_user_id_from_token(token: Optional[str]) -> str:
    """
    Extrai user_id de um token JWT.
    Retorna 'default' se não conseguir decodificar.
    """
    if not token:
        return 'default'
    
    payload = decode_jwt_payload(token)
    if not payload:
        return 'default'
    
    # Tentar diferentes campos comuns
    user_id = (
        payload.get('user_id') or
        payload.get('userId') or
        payload.get('sub') or  # Subject (padrão JWT)
        payload.get('email') or
        payload.get('id')
    )
    
    return str(user_id) if user_id else 'default'

