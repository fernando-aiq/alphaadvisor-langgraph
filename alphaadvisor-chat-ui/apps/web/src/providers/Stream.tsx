"use client";

import { useStream } from "@langchain/langgraph-sdk/react";
import { createContext, useContext, ReactNode } from "react";
import { useQueryState } from "nuqs";
import { getApiKey } from "@/lib/api-key";

const StreamContext = createContext<ReturnType<typeof useStream> | undefined>(
  undefined,
);

// Valores padrão das variáveis de ambiente
const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL?.trim();
const DEFAULT_ASSISTANT_ID = process.env.NEXT_PUBLIC_ASSISTANT_ID?.trim();

export function StreamProvider({ children }: { children: ReactNode }) {
  const [apiUrl] = useQueryState("apiUrl");
  const [assistantId] = useQueryState("assistantId");

  // Usa query params se disponível, senão usa variáveis de ambiente
  // Remove espaços e quebras de linha para evitar erros
  const finalApiUrl = (apiUrl || DEFAULT_API_URL)?.trim();
  const finalAssistantId = (assistantId || DEFAULT_ASSISTANT_ID)?.trim();

  const stream = useStream({
    assistantId: finalAssistantId || undefined,
    apiUrl: finalApiUrl || undefined,
    apiKey: getApiKey() ?? undefined,
  });

  return (
    <StreamContext.Provider value={stream}>{children}</StreamContext.Provider>
  );
}

export function useStreamContext() {
  const context = useContext(StreamContext);
  if (context === undefined) {
    throw new Error("useStreamContext must be used within a StreamProvider");
  }
  return context;
}
