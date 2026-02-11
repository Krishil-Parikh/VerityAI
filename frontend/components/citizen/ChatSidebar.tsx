'use client';

import { Conversation } from '@/types';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete?: (id: string) => void;
}

export function ChatSidebar({ 
  conversations, 
  activeId, 
  onSelect, 
  onNewChat,
  onDelete 
}: ChatSidebarProps) {
  return (
    <div className="w-64 flex flex-col bg-muted/30 border-r border-border h-full">
      <div className="p-4">
        <Button 
          onClick={onNewChat}
          className="w-full justify-start gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Plus size={18} />
          New Chat
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No conversations yet
          </div>
        ) : (
          conversations.map((conv) => (
            <div 
              key={conv.id}
              className={cn(
                "group relative flex items-center w-full rounded-md px-3 py-2 text-sm transition-colors cursor-pointer",
                activeId === conv.id 
                  ? "bg-primary/10 text-primary" 
                  : "hover:bg-accent text-muted-foreground hover:text-accent-foreground"
              )}
              onClick={() => onSelect(conv.id)}
            >
              <div className="flex flex-col flex-1 overflow-hidden">
                <div className="flex items-center gap-2">
                  <MessageSquare size={14} className="flex-shrink-0" />
                  <span className="truncate font-medium">
                    {conv.messages[0]?.content || 'New Conversation'}
                  </span>
                </div>
                <span className="text-[10px] opacity-60 ml-5">
                  {formatDistanceToNow(new Date(conv.updatedAt), { addSuffix: true })}
                </span>
              </div>
              
              {onDelete && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-destructive transition-opacity"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
