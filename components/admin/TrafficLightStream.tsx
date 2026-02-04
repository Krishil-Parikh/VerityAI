'use client';

import { Conversation } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { truncateText, formatDate, getStatusLabel } from '@/lib/formatters';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';

interface TrafficLightStreamProps {
  conversations: Conversation[];
  onSelectConversation?: (conversation: Conversation) => void;
}

export function TrafficLightStream({
  conversations,
  onSelectConversation,
}: TrafficLightStreamProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'safe':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'needs_review':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'violation':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'evaluating':
        return (
          <div className="h-5 w-5 rounded-full border-2 border-slate-400 border-t-slate-600 animate-spin" />
        );
      default:
        return null;
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'safe':
        return 'bg-green-100 text-green-900';
      case 'needs_review':
        return 'bg-yellow-100 text-yellow-900';
      case 'violation':
        return 'bg-red-100 text-red-900';
      case 'evaluating':
        return 'bg-slate-200 text-slate-700 animate-pulse';
      default:
        return 'bg-slate-100 text-slate-900';
    }
  };

  const sortedConversations = [...conversations].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );

  return (
    <Card className="border-slate-200 mb-6">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Real-Time Conversation Stream
        </h2>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {sortedConversations.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-8">
              No conversations yet
            </p>
          ) : (
            sortedConversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelectConversation?.(conv)}
                className="flex items-center gap-4 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                <div className="flex-shrink-0">
                  {getStatusIcon(conv.status)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-slate-900">
                      {conv.citizenId}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatDate(conv.updatedAt)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 truncate">
                    {truncateText(
                      conv.messages[conv.messages.length - 1]?.content ||
                        'No content',
                      80
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  {conv.status !== 'evaluating' && (
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900">
                        {conv.overallEthicalScore}
                      </p>
                      <p className="text-xs text-slate-500">/100</p>
                    </div>
                  )}
                  {conv.status === 'evaluating' && (
                    <div className="text-right">
                      <p className="text-xs text-slate-600 animate-pulse">Evaluating…</p>
                    </div>
                  )}
                  <Badge
                    className={`${getStatusBadgeColor(
                      conv.status
                    )} border-0`}
                  >
                    {conv.status === 'evaluating'
                      ? 'Evaluating'
                      : getStatusLabel(conv.status)}
                  </Badge>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );
}
