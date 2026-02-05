'use client';

import { useState, useEffect, useCallback } from 'react';
import { Conversation, Message } from '@/types';
import { ChatWindow } from '@/components/citizen/ChatWindow';
import { ChatInput } from '@/components/citizen/ChatInput';
import { conversationStore } from '@/store/conversationStore';
import { ApiMode } from '@/lib/api-config';

export default function CitizenPage() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Subscribe to conversation updates from store
  useEffect(() => {
    const unsubscribe = conversationStore.subscribe(() => {
      // This will re-render when the store updates
    });

    return unsubscribe;
  }, []);

  const handleSendMessage = useCallback(async (message: string, model: string = 'llama3', mode: ApiMode = 'offline') => {
    // Create new conversation if none exists
    if (!conversation) {
      const newConv = conversationStore.createConversation('current-citizen', message);
      setConversation(newConv);
      setIsLoading(true);

      // Get AI response with selected model and mode
      const response = await conversationStore.addAIResponse(newConv.id, model, mode);
      if (response) {
        setConversation(response);
      }
      setIsLoading(false);
    } else {
      // Add message to existing conversation
      conversationStore.addMessage(conversation.id, {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
      });

      // Update local state
      const updated = conversationStore.getConversation(conversation.id);
      if (updated) {
        setConversation(updated);
      }

      setIsLoading(true);

      // Get AI response with selected model and mode
      const response = await conversationStore.addAIResponse(conversation.id, model, mode);
      if (response) {
        setConversation(response);
      }
      setIsLoading(false);
    }
  }, [conversation]);

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      {/* Main chat area */}
      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Chat window */}
        <div className="flex-1 flex flex-col bg-card rounded-lg border border-border overflow-hidden">
          <ChatWindow
            messages={conversation?.messages || []}
            isLoading={isLoading}
          />
          <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
