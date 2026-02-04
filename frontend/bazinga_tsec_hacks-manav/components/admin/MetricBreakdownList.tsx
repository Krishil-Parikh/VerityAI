'use client';

import { MetricBreakdown } from '@/types';
import { Card } from '@/components/ui/card';
import { formatNumber } from '@/lib/formatters';

interface MetricBreakdownListProps {
  breakdown: MetricBreakdown;
}

export function MetricBreakdownList({ breakdown }: MetricBreakdownListProps) {
  const metrics = [
    {
      label: 'Statistical Parity',
      value: formatNumber(breakdown.statisticalParity, 4),
    },
    {
      label: 'Equal Opportunity',
      value: formatNumber(breakdown.equalOpportunity, 2),
    },
    {
      label: 'Disparate Impact',
      value: formatNumber(breakdown.disparateImpact, 2),
    },
    {
      label: 'F1 Score',
      value: formatNumber(breakdown.f1Score, 2),
    },
    {
      label: 'Task Completion Rate',
      value: formatNumber(breakdown.taskCompletionRate, 2),
    },
    {
      label: 'Lawfulness Assessment',
      value: breakdown.lawfulnessAssessment,
    },
    {
      label: 'PII Disclosure',
      value: breakdown.piiDisclosure.toString(),
    },
  ];

  return (
    <Card className="border-border p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">
        Detailed Metrics
      </h3>
      <div className="space-y-3">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
          >
            <span className="text-sm font-medium text-muted-foreground">
              {metric.label}
            </span>
            <span className="text-sm font-semibold text-foreground">
              {metric.value}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
