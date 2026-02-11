'use client';

import { DimensionScore } from '@/types';
import { Card } from '@/components/ui/card';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip,
} from 'recharts';

interface MetricsRadarCardProps {
    dimensionScores: DimensionScore[];
    overallScore: number;
}

// All 9 dimension short labels for the radar axes
const DIMENSION_SHORT_LABELS: Record<string, string> = {
    'Legal Compliance': 'Legal',
    'Bias & Fairness': 'Fairness',
    'Explainability & Transparency': 'Explainability',
    'Security & Robustness': 'Security',
    'Monitoring & Compliance': 'Monitoring',
    'Model Performance': 'Performance',
    'Human-AI UX': 'UX',
    'Data & Model Drift': 'Drift',
    'Environmental & Cost': 'Environmental',
    // Fallback matches for partial names
    'Explainability': 'Explainability',
    'Human Control': 'Human Control',
    'Data Grounding & Drift': 'Drift',
    'Ethical Alignment': 'Ethical',
    'Response Quality': 'Quality',
};

export function MetricsRadarCard({
    dimensionScores,
    overallScore,
}: MetricsRadarCardProps) {
    const getScoreColor = (score: number): string => {
        if (score >= 85) return 'text-green-600 dark:text-green-500';
        if (score >= 70) return 'text-yellow-600 dark:text-yellow-500';
        return 'text-red-600 dark:text-red-500';
    };

    const getRadarFill = (score: number): string => {
        if (score >= 85) return 'rgba(22, 163, 74, 0.3)';
        if (score >= 70) return 'rgba(234, 179, 8, 0.3)';
        return 'rgba(220, 38, 38, 0.3)';
    };

    const getRadarStroke = (score: number): string => {
        if (score >= 85) return '#16a34a';
        if (score >= 70) return '#eab308';
        return '#dc2626';
    };

    // Map dimension scores to radar data — use short labels
    const radarData = dimensionScores.map((dim) => ({
        dimension: DIMENSION_SHORT_LABELS[dim.name] || dim.name.split('&')[0].trim(),
        score: dim.score,
        fullName: dim.name,
        status: dim.status,
    }));

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            const statusColor =
                data.status === 'safe' ? 'text-green-500' :
                data.status === 'needs_review' ? 'text-yellow-500' :
                'text-red-500';

            return (
                <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                    <p className="text-sm font-semibold text-foreground">{data.fullName}</p>
                    <p className="text-lg font-bold text-foreground">{data.score}<span className="text-xs text-muted-foreground">/100</span></p>
                    <p className={`text-xs font-medium uppercase ${statusColor}`}>{data.status?.replace('_', ' ')}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <Card className="border-border">
            <div className="p-6">
                <h2 className="text-lg font-semibold text-foreground mb-2">
                    Ethical Dimensions — Spider Web Assessment
                </h2>
                <p className="text-sm text-muted-foreground mb-6">
                    All 9 dimensions scored 0–100. Larger polygon = better compliance.
                </p>

                {/* Overall Score */}
                <div className="mb-6 flex items-center justify-center">
                    <div className="relative h-28 w-28 flex items-center justify-center">
                        <svg className="absolute inset-0" viewBox="0 0 120 120">
                            <circle cx="60" cy="60" r="52" fill="none" strokeWidth="8"
                                className="stroke-muted" />
                            <circle cx="60" cy="60" r="52" fill="none" strokeWidth="8"
                                strokeDasharray={`${(overallScore / 100) * 326.7} 326.7`}
                                strokeLinecap="round"
                                style={{
                                    stroke: overallScore >= 85 ? '#16a34a' : overallScore >= 70 ? '#eab308' : '#dc2626',
                                    transform: 'rotate(-90deg)',
                                    transformOrigin: '50% 50%',
                                    transition: 'stroke-dasharray 0.6s ease',
                                }}
                            />
                        </svg>
                        <div className="relative flex flex-col items-center justify-center">
                            <span className={`text-3xl font-bold ${getScoreColor(overallScore)}`}>
                                {overallScore}
                            </span>
                            <span className="text-[10px] font-medium text-muted-foreground">
                                Overall
                            </span>
                        </div>
                    </div>
                </div>

                {/* Spider Web Radar Chart */}
                {radarData.length > 0 && (
                    <div className="w-full h-[380px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                                <PolarGrid
                                    gridType="polygon"
                                    stroke="hsl(var(--border))"
                                    strokeOpacity={0.4}
                                />
                                <PolarAngleAxis
                                    dataKey="dimension"
                                    tick={{
                                        fill: 'hsl(var(--muted-foreground))',
                                        fontSize: 11,
                                        fontWeight: 500,
                                    }}
                                />
                                <PolarRadiusAxis
                                    angle={90}
                                    domain={[0, 100]}
                                    tick={{
                                        fill: 'hsl(var(--muted-foreground))',
                                        fontSize: 9,
                                    }}
                                    tickCount={5}
                                    axisLine={false}
                                />
                                <Radar
                                    name="Score"
                                    dataKey="score"
                                    stroke={getRadarStroke(overallScore)}
                                    fill={getRadarFill(overallScore)}
                                    strokeWidth={2}
                                    dot={{
                                        r: 4,
                                        fill: getRadarStroke(overallScore),
                                        strokeWidth: 0,
                                    }}
                                    animationDuration={800}
                                    animationEasing="ease-out"
                                />
                                <Tooltip content={<CustomTooltip />} />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Compact Dimension Legend */}
                <div className="mt-4 grid grid-cols-3 gap-2">
                    {dimensionScores.map((dim) => {
                        const label = DIMENSION_SHORT_LABELS[dim.name] || dim.name.split('&')[0].trim();
                        const color =
                            dim.score >= 85 ? 'bg-green-500' :
                            dim.score >= 70 ? 'bg-amber-500' :
                            'bg-red-500';

                        return (
                            <div key={dim.name} className="flex items-center gap-2">
                                <div className={`h-2.5 w-2.5 rounded-full ${color}`} />
                                <span className="text-xs text-muted-foreground truncate">{label}</span>
                                <span className="text-xs font-semibold text-foreground ml-auto">{dim.score}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </Card>
    );
}
