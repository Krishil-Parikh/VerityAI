'use client';

import { Card } from '@/components/ui/card';
import { Conversation } from '@/types';

interface SimpleChartProps {
    conversations: Conversation[];
}

export function SimpleChart({ conversations }: SimpleChartProps) {
    // Calculate average score per dimension
    const dimensionScores: { [key: string]: number[] } = {};

    conversations.forEach((conv) => {
        conv.dimensionScores.forEach((dim) => {
            if (!dimensionScores[dim.name]) {
                dimensionScores[dim.name] = [];
            }
            dimensionScores[dim.name].push(dim.score);
        });
    });

    const averageScores = Object.entries(dimensionScores).map(([name, scores]) => ({
        name,
        average: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
    }));

    // Count conversations per hour (dummy data)
    const hoursData = [
        { hour: '00:00', count: 2 },
        { hour: '04:00', count: 1 },
        { hour: '08:00', count: 3 },
        { hour: '12:00', count: 4 },
        { hour: '16:00', count: 2 },
        { hour: '20:00', count: 1 },
    ];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Dimension Scores */}
            <Card className="border-border">
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-6">
                        Average Score per Dimension
                    </h3>
                    <div className="space-y-4">
                        {averageScores.map((item) => {
                            const percentage = item.average;
                            const color =
                                percentage >= 85
                                    ? 'bg-green-500'
                                    : percentage >= 70
                                        ? 'bg-yellow-500'
                                        : 'bg-red-500';

                            return (
                                <div key={item.name}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm text-muted-foreground font-medium">
                                            {item.name.split('&')[0]}
                                        </span>
                                        <span className="text-sm font-semibold text-foreground">
                                            {item.average}
                                        </span>
                                    </div>
                                    <div className="h-3 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${color} transition-all`}
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </Card>

            {/* Hourly Conversations */}
            <Card className="border-border">
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-6">
                        Conversations per Hour
                    </h3>
                    <div className="flex items-end justify-between gap-2 h-40">
                        {hoursData.map((item) => {
                            const maxCount = Math.max(...hoursData.map((h) => h.count));
                            const heightPercent = (item.count / maxCount) * 100;

                            return (
                                <div key={item.hour} className="flex-1 flex flex-col items-center">
                                    <div
                                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                                        style={{ height: `${heightPercent}%`, minHeight: '4px' }}
                                    />
                                    <p className="text-xs text-muted-foreground mt-2">{item.hour}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </Card>
        </div>
    );
}
