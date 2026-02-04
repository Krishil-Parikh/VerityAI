'use client';

import { DimensionScore } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface MetricsGridProps {
  dimensionScores: DimensionScore[];
}

export function MetricsGrid({ dimensionScores }: MetricsGridProps) {
  const getScoreColor = (status: 'safe' | 'review' | 'violation') => {
    switch (status) {
      case 'safe':
        return 'bg-green-100 text-green-900';
      case 'review':
        return 'bg-yellow-100 text-yellow-900';
      case 'violation':
        return 'bg-red-100 text-red-900';
    }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {dimensionScores.map((dim) => (
        <Card key={dim.name} className="border-slate-200 p-4">
          <p className="text-xs text-slate-600 mb-2 line-clamp-2">
            {dim.name}
          </p>
          <div className="flex items-baseline gap-1 mb-2">
            <p className="text-2xl font-bold text-slate-900">{dim.score}</p>
            <p className="text-xs text-slate-500">/100</p>
          </div>
          <Badge className={`${getScoreColor(dim.status)} border-0 text-xs`}>
            {dim.status === 'safe' && 'Safe'}
            {dim.status === 'review' && 'Review'}
            {dim.status === 'violation' && 'Violation'}
          </Badge>
        </Card>
      ))}
    </div>
  );
}
