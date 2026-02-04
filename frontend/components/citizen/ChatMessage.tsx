'use client';

import { Message, RagSource } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate, getStatusLabel } from '@/lib/formatters';
import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

// Citation component for clickable PDF links
function CitationLink({ source, index }: { source: RagSource; index: number }) {
  const handleClick = () => {
    // Open PDF at specific page
    const url = `/api/pdf?file=${encodeURIComponent(source.doc)}&page=${source.page}`;
    window.open(url, '_blank');
  };

  return (
    <button
      onClick={handleClick}
      className="flex items-center gap-2 px-3 py-2 text-left text-sm rounded-md border border-border hover:bg-muted transition-colors w-full"
    >
      <FileText className="h-4 w-4 text-primary flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-foreground truncate">{source.doc}</div>
        <div className="text-xs text-muted-foreground">
          Page {source.page} • Relevance: {(source.score * 100).toFixed(1)}%
        </div>
      </div>
      <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0" />
    </button>
  );
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false);
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

  // AI message with citations
  const hasCitations = message.ragSources && message.ragSources.length > 0;

  return (
    <div className="mb-4 flex justify-start">
      <Card className="max-w-2xl border-border">
        <div className="p-4">
          <p className="text-sm text-foreground whitespace-pre-wrap">{message.content}</p>

          {/* Ethics Score Badge */}
          {message.ethicalScore !== undefined && (
            <div className="mt-3 flex items-center gap-2">
              <Badge 
                variant={message.ethicalScore >= 85 ? 'default' : message.ethicalScore >= 70 ? 'secondary' : 'destructive'}
              >
                Ethics Score: {message.ethicalScore}%
              </Badge>
              {message.metricBreakdown?.lawfulnessAssessment && (
                <Badge variant="outline">
                  Lawfulness: {message.metricBreakdown.lawfulnessAssessment}
                </Badge>
              )}
            </div>
          )}

          {/* Citations Section */}
          {hasCitations && (
            <div className="mt-4 border-t border-border pt-3">
              <button
                onClick={() => setShowCitations(!showCitations)}
                className="flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <FileText className="h-4 w-4" />
                <span>Sources ({message.ragSources!.length})</span>
                {showCitations ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>

              {showCitations && (
                <div className="mt-3 space-y-2">
                  {message.ragSources!.map((source, index) => (
                    <CitationLink key={index} source={source} index={index} />
                  ))}
                </div>
              )}
            </div>
          )}

          <p className="mt-3 text-xs text-muted-foreground">{formatDate(message.timestamp)}</p>
        </div>
      </Card>
    </div>
  );
}
