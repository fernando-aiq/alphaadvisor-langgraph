import { validate } from "uuid";
import { getApiKey } from "../lib/api-key";
import { Thread } from "@langchain/langgraph-sdk";
import { useQueryState } from "nuqs";
import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  Dispatch,
  SetStateAction,
} from "react";
import { createClient } from "./client";

// Valores padrão das variáveis de ambiente
const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL?.trim();
const DEFAULT_ASSISTANT_ID = process.env.NEXT_PUBLIC_ASSISTANT_ID?.trim();

interface ThreadContextType {
  getThreads: () => Promise<Thread[]>;
  threads: Thread[];
  setThreads: Dispatch<SetStateAction<Thread[]>>;
  threadsLoading: boolean;
  setThreadsLoading: Dispatch<SetStateAction<boolean>>;
}

const ThreadContext = createContext<ThreadContextType | undefined>(undefined);

function getThreadSearchMetadata(
  assistantId: string,
): { graph_id: string } | { assistant_id: string } {
  if (validate(assistantId)) {
    return { assistant_id: assistantId };
  } else {
    return { graph_id: assistantId };
  }
}

export function ThreadProvider({ children }: { children: ReactNode }) {
  const [apiUrl] = useQueryState("apiUrl");
  const [assistantId] = useQueryState("assistantId");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(false);

  // Usa query params se disponível, senão usa variáveis de ambiente
  // Remove espaços e quebras de linha para evitar erros
  const finalApiUrl = (apiUrl || DEFAULT_API_URL)?.trim();
  const finalAssistantId = (assistantId || DEFAULT_ASSISTANT_ID)?.trim();

  const getThreads = useCallback(async (): Promise<Thread[]> => {
    if (!finalApiUrl || !finalAssistantId) return [];
    
    try {
      // Usar endpoint da API route em vez de search direto
      const response = await fetch(`/api/studio/threads?limit=100`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.threads || [];
    } catch (error) {
      console.error('Erro ao buscar threads:', error);
      return [];
    }
  }, [finalApiUrl, finalAssistantId]);

  const value = {
    getThreads,
    threads,
    setThreads,
    threadsLoading,
    setThreadsLoading,
  };

  return (
    <ThreadContext.Provider value={value}>{children}</ThreadContext.Provider>
  );
}

export function useThreads() {
  const context = useContext(ThreadContext);
  if (context === undefined) {
    throw new Error("useThreads must be used within a ThreadProvider");
  }
  return context;
}
