// Valores padrão das variáveis de ambiente
const DEFAULT_API_KEY = process.env.NEXT_PUBLIC_LANGSMITH_API_KEY?.trim();

export function getApiKey(): string | null {
  try {
    if (typeof window === "undefined") {
      // No servidor, retorna a variável de ambiente se disponível
      return DEFAULT_API_KEY || null;
    }
    
    // No cliente, primeiro tenta localStorage, depois variável de ambiente
    const localStorageKey = window.localStorage.getItem("lg:chat:apiKey");
    return localStorageKey || DEFAULT_API_KEY || null;
  } catch {
    // no-op
  }

  return DEFAULT_API_KEY || null;
}
