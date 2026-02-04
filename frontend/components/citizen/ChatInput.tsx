'use client';

import React from "react"

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, ChevronDown } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Available models
const MODELS = [
  { value: 'llama3', label: 'Llama 3 (Default)' },
  { value: 'deepseek-coder:6.7b', label: 'DeepSeek Coder 6.7B' },
  { value: 'qwen2.5:3b', label: 'Qwen 2.5 3B' },
  { value: 'tinyllama:latest', label: 'TinyLlama' },
  { value: 'gemma3:12b', label: 'Gemma 3 12B' },
  { value: 'all', label: '🔄 Evaluate All Models' },
];

interface ChatInputProps {
  onSend: (message: string, model: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('llama3');

  const handleSubmit = () => {
    if (message.trim()) {
      onSend(message, selectedModel);
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
    <div className="border-t border-border bg-background p-4">
      {/* Model selector */}
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Model:</span>
        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            {MODELS.map((model) => (
              <SelectItem key={model.value} value={model.value}>
                {model.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedModel === 'all' && (
          <span className="text-xs text-amber-600 dark:text-amber-400">
            Will evaluate query with all models
          </span>
        )}
      </div>
      
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
          className="bg-primary hover:bg-primary/90 text-primary-foreground h-full"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Ctrl+Enter to send
      </p>
    </div>
  );
}

