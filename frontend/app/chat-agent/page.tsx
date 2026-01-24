"use client";

import { Thread } from "@/app/components/chat-agent/thread";
import { StreamProvider } from "@/app/providers/Stream";
import { ThreadProvider } from "@/app/providers/Thread";
import { Toaster } from "@/app/components/chat-agent/ui/sonner";
import React from "react";

export default function ChatAgentPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <ThreadProvider>
        <StreamProvider>
          <Thread />
        </StreamProvider>
      </ThreadProvider>
    </React.Suspense>
  );
}
