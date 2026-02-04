'use client';

import { DimensionScore } from '@/types';
import { Card } from '@/components/ui/card';
import {
  Shield,
  Scale,
  BookOpen,
  Target,
  Users,
  Lock,
  TrendingUp,
  CheckCircle2,
} from 'lucide-react';

interface MetricsRadarCardProps {
  dimensionScores: DimensionScore[];
  overallScore: number;
}

export function MetricsRadarCard({
  dimensionScores,
  overallScore,
}: MetricsRadarCardProps) {
  // Map dimension names to icons
  const iconMap: Record<string, typeof Shield> = {
    'Bias & Fairness': Scale,
    'Data Grounding & Drift': TrendingUp,
    'Explainability & Transparency': BookOpen,
    'Ethical Alignment': Target,
    'Human Control': Users,
    'Legal Compliance': CheckCircle2,
    'Security & Robustness': Lock,
    'Response Quality': CheckCircle2,
  };

  const getScoreColor = (score: number): string => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number): string => {
    if (score >= 85) return 'bg-green-50 border-green-200';
    if (score >= 70) return 'bg-amber-50 border-amber-200';
    return 'bg-red-50 border-red-200';
  };

  const getProgressBarColor = (score: number): string => {
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <Card className="border-slate-200">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6">
          Ethical Dimensions Assessment
        </h2>

        {/* Overall Score */}
        <div className="mb-8 flex items-center justify-center">
          <div className="relative h-40 w-40 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-8 border-slate-100" />
            <div
              className="absolute inset-0 rounded-full border-8 transition-all"
              style={{
                borderColor:
                  overallScore >= 85
                    ? '#16a34a'
                    : overallScore >= 70
                      ? '#b45309'
                      : '#dc2626',
                borderTopColor: 'transparent',
                borderRightColor: 'transparent',
                borderBottomColor: 'transparent',
                transform: `rotate(${(overallScore / 100) * 360}deg)`,
              }}
            />
            <div className="relative flex flex-col items-center justify-center">
              <span
                className={`text-5xl font-bold ${getScoreColor(overallScore)}`}
              >
                {overallScore}
              </span>
              <span className="text-xs font-medium text-slate-600 mt-1">
                Overall Score
              </span>
            </div>
          </div>
        </div>

        {/* Dimension Grid */}
        <div className="grid grid-cols-2 gap-4">
          {dimensionScores.map((dim) => {
            const Icon = iconMap[dim.name] || Shield;

            return (
              <div
                key={dim.name}
                className={`p-4 rounded-lg border ${getScoreBgColor(dim.score)}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-slate-600" />
                    <p className="text-xs font-medium text-slate-700 leading-tight">
                      {dim.name.split('&')[0]}
                    </p>
                  </div>
                  <span
                    className={`text-sm font-bold ${getScoreColor(dim.score)}`}
                  >
                    {dim.score}
                  </span>
                </div>

                <div className="h-1.5 rounded-full bg-slate-200 overflow-hidden">
                  <div
                    className={`h-full ${getProgressBarColor(dim.score)} transition-all`}
                    style={{ width: `${dim.score}%` }}
                  />
                </div>

                <p className="text-xs text-slate-500 mt-2 capitalize">
                  {dim.status}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
