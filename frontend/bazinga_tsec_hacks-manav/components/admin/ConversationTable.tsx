'use client';

import { Conversation } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate, truncateText, getStatusLabel } from '@/lib/formatters';
import { Eye } from 'lucide-react';

interface ConversationTableProps {
  conversations: Conversation[];
  onViewDetails: (conv: Conversation) => void;
}

export function ConversationTable({
  conversations,
  onViewDetails,
}: ConversationTableProps) {
  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'safe':
        return 'bg-green-100 text-green-900 dark:bg-green-900/30 dark:text-green-300';
      case 'needs_review':
        return 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'violation':
        return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-300';
      case 'evaluating':
        return 'bg-muted text-muted-foreground animate-pulse';
      default:
        return 'bg-muted text-foreground';
    }
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 85) return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-950/30';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-950/30';
    return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/30';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Conversation ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Citizen ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Question
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Ethical Score
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Date/Time
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Action
            </th>
          </tr>
        </thead>
        <tbody>
          {conversations.map((conv) => (
            <tr
              key={conv.id}
              className="border-b border-border hover:bg-accent/50 transition-colors"
            >
              <td className="px-4 py-3 text-sm text-foreground font-mono">
                {conv.id.substring(0, 8)}...
              </td>
              <td className="px-4 py-3 text-sm text-foreground">
                {conv.citizenId}
              </td>
              <td className="px-4 py-3 text-sm text-muted-foreground max-w-xs truncate">
                {truncateText(
                  conv.messages[0]?.content || 'No content',
                  50
                )}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block px-2 py-1 rounded text-sm font-semibold ${getScoreBadgeColor(
                    conv.overallEthicalScore
                  )}`}
                >
                  {conv.overallEthicalScore}
                </span>
              </td>
              <td className="px-4 py-3">
                <Badge
                  className={`${getStatusBadgeColor(
                    conv.status
                  )} border-0`}
                >
                  {getStatusLabel(conv.status)}
                </Badge>
              </td>
              <td className="px-4 py-3 text-sm text-muted-foreground">
                {formatDate(conv.createdAt)}
              </td>
              <td className="px-4 py-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewDetails(conv)}
                  className="gap-2"
                >
                  <Eye className="h-4 w-4" />
                  View
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
