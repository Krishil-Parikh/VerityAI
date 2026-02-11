'use client';

import React from "react"

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Wifi, WifiOff, Globe, Server } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getAvailableModes,
  getDefaultMode,
  getModelsForMode,
  isProduction,
  ApiMode
} from '@/lib/api-config';

interface ChatInputProps {
  onSend: (message: string, model: string, mode: ApiMode) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [selectedMode, setSelectedMode] = useState<ApiMode>(getDefaultMode());
  const [selectedModel, setSelectedModel] = useState('');
  const [availableModes, setAvailableModes] = useState<ApiMode[]>([]);

  // Initialize modes and default model on mount
  useEffect(() => {
    const modes = getAvailableModes();
    setAvailableModes(modes);
    
    const defaultMode = getDefaultMode();
    setSelectedMode(defaultMode);
    
    // Set default model based on mode
    const models = getModelsForMode(defaultMode);
    if (models.length > 0) {
      setSelectedModel(models[0].value);
    }
  }, []);

  // Update model selection when mode changes
  useEffect(() => {
    const models = getModelsForMode(selectedMode);
    if (models.length > 0) {
      setSelectedModel(models[0].value);
    }
  }, [selectedMode]);

  const handleModeChange = (mode: ApiMode) => {
    setSelectedMode(mode);
  };

  const handleSubmit = () => {
    if (message.trim()) {
      onSend(message, selectedModel, selectedMode);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const models = getModelsForMode(selectedMode);
  const showModeSelector = availableModes.length > 1;

  return (
    <div className="border-t border-border bg-background p-4">
      {/* Mode and Model selectors */}
      <div className="mb-3 flex flex-wrap items-center gap-3">
        {/* Mode selector - only show in development */}
        {showModeSelector && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Mode:</span>
            <div className="flex rounded-lg border border-border overflow-hidden">
              <button
                onClick={() => handleModeChange('offline')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors ${
                  selectedMode === 'offline'
                    ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                <Server className="h-3.5 w-3.5" />
                Offline
              </button>
              <button
                onClick={() => handleModeChange('online')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors ${
                  selectedMode === 'online'
                    ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                <Globe className="h-3.5 w-3.5" />
                Online
              </button>
            </div>
          </div>
        )}

        {/* Production mode indicator */}
        {isProduction() && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-green-500/10 text-green-600 dark:text-green-400 text-xs">
            <Globe className="h-3 w-3" />
            <span>Online Mode</span>
          </div>
        )}

        {/* Model selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Model:</span>
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {models.map((model) => (
                <SelectItem key={model.value} value={model.value}>
                  {model.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Mode indicator badge */}
        {selectedMode === 'online' && !isProduction() && (
          <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
            <Wifi className="h-3 w-3" />
            Using AWS Lambda API
          </span>
        )}
        {selectedMode === 'offline' && (
          <span className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
            <WifiOff className="h-3 w-3" />
            Using local Ollama
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
          className="resize-none min-h-[44px] py-3"
          rows={1}
        />
        <Button
          onClick={handleSubmit}
          disabled={isLoading || !message.trim()}
          className="bg-primary hover:bg-primary/90 text-primary-foreground h-[44px] w-[44px] rounded-lg shrink-0 flex items-center justify-center"
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
