'use client';

import { Conversation } from '@/types';
import { Card } from '@/components/ui/card';
import { formatNumber } from '@/lib/formatters';

interface ScoreSummaryPanelProps {
  conversation: Conversation | null;
}

export function ScoreSummaryPanel({
  conversation,
}: ScoreSummaryPanelProps) {
  if (!conversation || conversation.dimensionScores.length === 0) {
    return (
      <Card className="border-border">
        <div className="p-6">
          <h3 className="font-semibold text-foreground mb-4">Answer Score Summary</h3>
          <p className="text-sm text-muted-foreground">
            Latest answer scores will appear here
          </p>
        </div>
      </Card>
    );
  }

  const score = conversation.overallEthicalScore;
  const scoreStatus =
    score >= 85 ? 'safe' : score >= 70 ? 'review' : 'violation';
  const scoreColor =
    scoreStatus === 'safe'
      ? 'text-green-600 dark:text-green-500'
      : scoreStatus === 'review'
        ? 'text-yellow-600 dark:text-yellow-500'
        : 'text-red-600 dark:text-red-500';
  const bgColor =
    scoreStatus === 'safe'
      ? 'bg-green-50 dark:bg-green-950/20'
      : scoreStatus === 'review'
        ? 'bg-yellow-50 dark:bg-yellow-950/20'
        : 'bg-red-50 dark:bg-red-950/20';

  return (
    <Card className={`border-border ${bgColor}`}>
      <div className="p-6">
        <h3 className="font-semibold text-foreground mb-6">Answer Score Summary</h3>

        {/* Overall Score */}
        <div className="mb-6 text-center">
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {formatNumber(score)}
          </div>
          <p className="text-sm text-muted-foreground mt-1">Overall Ethical Score</p>
        </div>

        {/* Dimension Bars */}
        <div className="space-y-3">
          {conversation.dimensionScores.map((dim) => {
            const dimStatusColor =
              dim.score >= 85
                ? 'bg-green-500'
                : dim.score >= 70
                  ? 'bg-yellow-500'
                  : 'bg-red-500';

            return (
              <div key={dim.name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-foreground">
                    {dim.name.split('&')[0]}
                  </span>
                  <span className="text-xs font-semibold text-foreground">
                    {dim.score}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full ${dimStatusColor} transition-all`}
                    style={{ width: `${dim.score}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
