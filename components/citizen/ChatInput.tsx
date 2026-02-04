'use client';

import React from "react"

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    if (message.trim()) {
      onSend(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <div className="flex gap-2">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about government information..."
          disabled={isLoading}
          className="resize-none"
          rows={3}
        />
        <Button
          onClick={handleSubmit}
          disabled={isLoading || !message.trim()}
          size="lg"
          className="bg-blue-600 hover:bg-blue-700 text-white h-full"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-slate-500 mt-2">
        Ctrl+Enter to send
      </p>
    </div>
  );
}
