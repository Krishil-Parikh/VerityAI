'use client';

import { useState, useEffect } from 'react';
import { Conversation } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { truncateText, formatDate, getStatusLabel } from '@/lib/formatters';
import { conversationStore } from '@/store/conversationStore';
import { CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';

export default function HistoryPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    setConversations(conversationStore.getConversations());

    const unsubscribe = conversationStore.subscribe(() => {
      setConversations(conversationStore.getConversations());
    });

    return unsubscribe;
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'safe':
        return <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-500" />;
      case 'review':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-500" />;
      case 'violation':
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'safe':
        return 'bg-green-100 text-green-900 dark:bg-green-900/30 dark:text-green-300';
      case 'review':
        return 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'violation':
        return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-300';
      default:
        return 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">History</h1>
        <p className="text-muted-foreground mt-1">
          View your previous RTI inquiries and their evaluation results
        </p>
      </div>

      <div className="space-y-3">
        {conversations.length === 0 ? (
          <Card className="border-border p-12 text-center">
            <p className="text-muted-foreground">No inquiries yet. Start by asking a question!</p>
          </Card>
        ) : (
          conversations.map((conv) => (
            <Card key={conv.id} className="border-border p-4 hover:bg-accent/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(conv.status)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-foreground">
                      {truncateText(
                        conv.messages[0]?.content || 'No content',
                        100
                      )}
                    </h3>
                    <Badge
                      className={`${getStatusBadgeColor(
                        conv.status
                      )} border-0 flex-shrink-0`}
                    >
                      {getStatusLabel(conv.status)}
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground mb-2">
                    {formatDate(conv.createdAt)}
                  </p>

                  <div className="flex items-center gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Ethical Score</p>
                      <p className="text-sm font-semibold text-foreground">
                        {conv.overallEthicalScore}/100
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Dimensions</p>
                      <p className="text-sm font-semibold text-foreground">
                        {conv.dimensionScores.filter((d) => d.score >= 85)
                          .length}/{conv.dimensionScores.length} Strong
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
