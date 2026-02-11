'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Conversation } from '@/types';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell
} from 'recharts';

interface SimpleChartProps {
    conversations: Conversation[];
}

export function SimpleChart({ conversations }: SimpleChartProps) {
    const [selectedModel, setSelectedModel] = useState<string>('All');

    // Get unique models
    const models = ['All', ...Array.from(new Set(conversations.map(c => c.botModel).filter(Boolean)))];

    // Calculate average score per dimension, optionally filtered by model
    const dimensionData: { [dim: string]: { [model: string]: number[] } } = {};

    conversations.forEach((conv) => {
        const model = conv.botModel || 'Unknown';
        conv.dimensionScores.forEach((dim) => {
            if (!dimensionData[dim.name]) {
                dimensionData[dim.name] = {};
            }
            if (!dimensionData[dim.name][model]) {
                dimensionData[dim.name][model] = [];
            }
            dimensionData[dim.name][model].push(dim.score);
        });
    });

    const chartData = Object.entries(dimensionData).map(([name, modelScores]) => {
        const entry: any = { name: name.split('&')[0].trim() };
        
        if (selectedModel === 'All') {
            // Calculate aggregate across all models
            const allScores = Object.values(modelScores).flat();
            entry.average = Math.round(allScores.reduce((a, b) => a + b, 0) / allScores.length);
        } else {
            // Use specific model score
            const scores = modelScores[selectedModel] || [];
            entry.average = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
        }
        return entry;
    });

    // Color mapper for bars
    const getBarColor = (score: number) => {
        if (score >= 85) return '#16a34a';
        if (score >= 70) return '#eab308';
        return '#dc2626';
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Dimension Analytics */}
            <Card className="border-border">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-semibold text-foreground">
                            Ethical Performance per Dimension
                        </h3>
                        <select 
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="text-xs bg-muted border-none rounded p-1 outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            {models.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                    </div>

                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} layout="vertical" margin={{ left: -10, right: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} strokeOpacity={0.2} />
                                <XAxis type="number" domain={[0, 100]} hide />
                                <YAxis 
                                    dataKey="name" 
                                    type="category" 
                                    width={100} 
                                    tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                                />
                                <Tooltip 
                                    cursor={{ fill: 'transparent' }}
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            return (
                                                <div className="bg-popover border border-border p-2 rounded shadow-sm text-xs">
                                                    <p className="font-bold">{payload[0].payload.name}</p>
                                                    <p className="text-blue-500">Avg Score: {payload[0].value}</p>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Bar dataKey="average" radius={[0, 4, 4, 0]} barSize={20}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={getBarColor(entry.average)} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </Card>

            {/* Model Comparison Table */}
            <Card className="border-border">
                <div className="p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-6">
                        Model Comparison Matrix
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left border-collapse">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="pb-2 font-medium text-muted-foreground">Model</th>
                                    <th className="pb-2 font-medium text-muted-foreground text-right">Avg Score</th>
                                    <th className="pb-2 font-medium text-muted-foreground text-right">Count</th>
                                    <th className="pb-2 font-medium text-muted-foreground text-right">Health</th>
                                </tr>
                            </thead>
                            <tbody>
                                {models.filter(m => m !== 'All').map(model => {
                                    const convs = conversations.filter(c => c.botModel === model);
                                    const avg = Math.round(convs.reduce((a, b) => a + b.overallEthicalScore, 0) / convs.length);
                                    const health = avg >= 85 ? 'text-green-500' : avg >= 70 ? 'text-yellow-500' : 'text-red-500';
                                    return (
                                        <tr key={model} className="border-b border-border/50 hover:bg-muted/50 transition-colors">
                                            <td className="py-2 text-foreground font-medium">{model}</td>
                                            <td className={`py-2 text-right font-bold ${health}`}>{avg}</td>
                                            <td className="py-2 text-right text-muted-foreground">{convs.length}</td>
                                            <td className="py-2 text-right uppercase font-bold tracking-tighter">
                                                <div className="flex justify-end gap-1 items-center">
                                                    <div className={`h-2 w-2 rounded-full ${avg >= 85 ? 'bg-green-500' : avg >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                                                    {avg >= 85 ? 'Safe' : avg >= 70 ? 'Review' : 'Alert'}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </Card>
        </div>
    );
}
