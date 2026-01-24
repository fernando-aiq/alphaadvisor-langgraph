/**
 * Utilitário para decodificar JWT e extrair informações do usuário
 */

export interface JWTPayload {
  user_id?: string;
  userId?: string;
  sub?: string;
  email?: string;
  id?: string;
  [key: string]: any;
}

export function decodeJWT(token: string): JWTPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = parts[1];
    const padding = payload.length % 4;
    const paddedPayload = padding ? payload + '='.repeat(4 - padding) : payload;
    
    const decoded = atob(paddedPayload);
    return JSON.parse(decoded);
  } catch (error) {
    console.error('[JWT Utils] Erro ao decodificar token:', error);
    return null;
  }
}

export function getUserIdFromToken(): string {
  if (typeof window === 'undefined') {
    return 'default';
  }

  const token = localStorage.getItem('token');
  if (!token) {
    return 'default';
  }

  const payload = decodeJWT(token);
  if (!payload) {
    return 'default';
  }

  const userId = 
    payload.user_id || 
    payload.userId || 
    payload.sub || 
    payload.email || 
    payload.id;

  return userId ? String(userId) : 'default';
}

