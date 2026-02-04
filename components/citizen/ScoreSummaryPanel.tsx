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
      <Card className="border-slate-200">
        <div className="p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Answer Score Summary</h3>
          <p className="text-sm text-slate-600">
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
      ? 'text-green-600'
      : scoreStatus === 'review'
        ? 'text-yellow-600'
        : 'text-red-600';
  const bgColor =
    scoreStatus === 'safe'
      ? 'bg-green-50'
      : scoreStatus === 'review'
        ? 'bg-yellow-50'
        : 'bg-red-50';

  return (
    <Card className={`border-slate-200 ${bgColor}`}>
      <div className="p-6">
        <h3 className="font-semibold text-slate-900 mb-6">Answer Score Summary</h3>

        {/* Overall Score */}
        <div className="mb-6 text-center">
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {formatNumber(score)}
          </div>
          <p className="text-sm text-slate-600 mt-1">Overall Ethical Score</p>
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
                  <span className="text-xs font-medium text-slate-700">
                    {dim.name.split('&')[0]}
                  </span>
                  <span className="text-xs font-semibold text-slate-900">
                    {dim.score}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
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
