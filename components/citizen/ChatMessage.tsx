'use client';

import { Message } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate, getStatusLabel } from '@/lib/formatters';
import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="mb-4 flex justify-end">
        <div className="max-w-xs rounded-lg bg-primary px-4 py-2 text-primary-foreground">
          <p className="text-sm">{message.content}</p>
          <p className="mt-1 text-xs opacity-75">{formatDate(message.timestamp)}</p>
        </div>
      </div>
    );
  }

  // AI message
  return (
    <div className="mb-4 flex justify-start">
      <Card className="max-w-md border-border">
        <div className="p-4">
          <p className="text-sm text-foreground">{message.content}</p>

          <div className="mt-3 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-muted-foreground/50" />
            <span className="text-xs font-medium text-muted-foreground">
              Quality checked
            </span>
          </div>

          <p className="mt-3 text-xs text-muted-foreground">{formatDate(message.timestamp)}</p>
        </div>
      </Card>
    </div>
  );
}
