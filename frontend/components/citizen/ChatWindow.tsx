'use client';

import { useEffect, useRef } from 'react';
import { Message } from '@/types';
import { ChatMessage } from './ChatMessage';
import { Loader2 } from 'lucide-react';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-4 space-y-4"
    >
      {messages.length === 0 ? (
      <div className="flex h-full items-center justify-center">
        <div className="text-center flex flex-col items-center">
          <img
            src="/icon.png"
            alt="VerityAI Logo"
            className="h-16 w-auto object-contain mb-6"
          />
          <p className="text-lg font-medium text-foreground mb-2">
            Welcome to VerityAI RTI Portal
          </p>
          <p className="text-sm text-muted-foreground">
            Ask a question to get started
          </p>
        </div>
      </div>
      ) : (
      <>
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="rounded-lg bg-muted px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">
                  Evaluating response...
                </span>
              </div>
            </div>
          </div>
        )}
      </>
      )}
    </div>
  );
}
