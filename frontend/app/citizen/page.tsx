'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Conversation, Message } from '@/types';
import { ChatWindow } from '@/components/citizen/ChatWindow';
import { ChatInput } from '@/components/citizen/ChatInput';
import { ChatSidebar } from '@/components/citizen/ChatSidebar';
import { conversationStore } from '@/store/conversationStore';
import { ApiMode } from '@/lib/api-config';

export default function CitizenPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Use a ref to always have the latest activeId in async handlers (avoids stale closures)
  const activeIdRef = useRef<string | null>(null);
  useEffect(() => {
    activeIdRef.current = activeId;
  }, [activeId]);

  // Subscribe to conversation updates from store
  useEffect(() => {
    // Initial load
    const loadData = async () => {
      if (!conversationStore.isInitialized()) {
        await conversationStore.loadConversations();
      }
      const all = conversationStore.getConversations();
      setConversations(all);
      if (all.length > 0 && !activeId) {
        setActiveId(all[0].id);
      }
    };
    
    loadData();

    const unsubscribe = conversationStore.subscribe(() => {
      const all = conversationStore.getConversations();
      setConversations(all);
    });

    return unsubscribe;
  }, []);

  const handleSelectConversation = async (id: string) => {
    setActiveId(id);
    await conversationStore.fetchConversationHistory(id);
  };

  const activeConversation = useMemo(() => {
    return conversations.find(c => c.id === activeId) || null;
  }, [conversations, activeId]);

  const handleSendMessage = useCallback(async (message: string, model: string = 'llama3', mode: ApiMode = 'offline') => {
    // ALWAYS use the ref to get the absolute latest activeId
    let currentId = activeIdRef.current;

    // Create new conversation if none exists or active
    if (!currentId) {
      const newConv = conversationStore.createConversation('current-citizen', message);
      setActiveId(newConv.id);
      currentId = newConv.id;
    } else {
      // Add message to existing conversation
      conversationStore.addMessage(currentId, {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
      });
    }

    setIsLoading(true);

    // Get AI response with selected model and mode
    await conversationStore.addAIResponse(currentId, model, mode);
    
    setIsLoading(false);
  }, []); // Dependencies removed as we now use activeIdRef

  const handleNewChat = () => {
    setActiveId(null);
  };

  const handleDeleteConversation = (id: string) => {
    conversationStore.deleteConversation(id);
    if (activeId === id) {
      setActiveId(null);
    }
  };

  return (
    <div className="flex h-full bg-background overflow-hidden">
      {/* Sidebar */}
      <ChatSidebar 
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDeleteConversation}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col overflow-hidden p-4">
        <div className="flex flex-1 flex-col bg-card rounded-lg border border-border overflow-hidden">
          <ChatWindow
            messages={activeConversation?.messages || []}
            isLoading={isLoading}
          />
          <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
