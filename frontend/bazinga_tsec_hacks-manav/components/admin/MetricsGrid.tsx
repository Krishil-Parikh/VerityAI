'use client';

import { DimensionScore } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface MetricsGridProps {
  dimensionScores: DimensionScore[];
}

export function MetricsGrid({ dimensionScores }: MetricsGridProps) {
  const getScoreColor = (status: 'safe' | 'needs_review' | 'violation') => {
    switch (status) {
      case 'safe':
        return 'bg-green-100 text-green-900 dark:bg-green-900/30 dark:text-green-300';
      case 'needs_review':
        return 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'violation':
        return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-300';
    }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {dimensionScores.map((dim) => (
        <Card key={dim.name} className="border-border p-4">
          <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
            {dim.name}
          </p>
          <div className="flex items-baseline gap-1 mb-2">
            <p className="text-2xl font-bold text-foreground">{dim.score}</p>
            <p className="text-xs text-muted-foreground">/100</p>
          </div>
          <Badge className={`${getScoreColor(dim.status)} border-0 text-xs`}>
            {dim.status === 'safe' && 'Safe'}
            {dim.status === 'needs_review' && 'Needs Review'}
            {dim.status === 'violation' && 'Violation'}
          </Badge>
        </Card>
      ))}
    </div>
  );
}
