"use client";

import React, { useEffect, useState, useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BackendResponse } from '@/types';
import { metricsStore } from '@/store/metricsStore';
import { Button } from "@/components/ui/button";
import { FileText, ShieldAlert, BadgeCheck, Activity, RefreshCw, Loader2 } from 'lucide-react';

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

type ViewType = 'score' | 'tokens' | 'dimensions' | 'rag' | 'comparison';

const MODEL_COLORS: Record<string, string> = {
    'llama3': '#8884d8',
    'deepseek-coder:6.7b': '#82ca9d',
    'qwen2.5:3b': '#ffc658',
    'tinyllama:latest': '#ff8042',
    'gemma3:12b': '#0088fe',
    'all': '#8884d8'
};

const ALL_MODELS = [
    { value: 'all', label: 'All Models' },
    { value: 'llama3', label: 'Llama 3' },
    { value: 'deepseek-coder:6.7b', label: 'DeepSeek Coder' },
    { value: 'qwen2.5:3b', label: 'Qwen 2.5' },
    { value: 'tinyllama:latest', label: 'TinyLlama' },
    { value: 'gemma3:12b', label: 'Gemma 3' },
];

export function GraphsDashboard() {
    const [data, setData] = useState<BackendResponse[]>([]);
    const [view, setView] = useState<ViewType>('comparison');
    const [selectedModel, setSelectedModel] = useState<string>('all');
    const [queryCount, setQueryCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch initial data from backend AND subscribe to metricsStore
    useEffect(() => {
        const fetchInitialData = async () => {
            setIsLoading(true);
            try {
                await metricsStore.loadHistory();
            } catch (error) {
                console.error('Error fetching initial telemetry:', error);
            }

            setData(metricsStore.getMetricsHistory());
            setQueryCount(metricsStore.getHistoryCount());
            setIsLoading(false);
        };

        fetchInitialData();

        const unsubscribe = metricsStore.subscribe(() => {
            setData(metricsStore.getMetricsHistory());
            setQueryCount(metricsStore.getHistoryCount());
        });

        return () => unsubscribe();
    }, []);

    const handleRefresh = async () => {
        setIsLoading(true);
        try {
            await metricsStore.loadHistory();
        } catch (error) {
            console.error('Error refreshing:', error);
        }
        setIsLoading(false);
    };

    const handleClearData = () => {
        metricsStore.clearHistory();
    };

    // Filter data based on selected model
    const filteredData = useMemo(() => {
        if (selectedModel === 'all') return data;
        return data.filter(item => item.bot_model === selectedModel);
    }, [data, selectedModel]);

    // Transform data for comparison view
    const getComparisonData = () => {
        const groups: Record<string, any> = {};

        data.forEach(item => {
            const ts = item.timestamp || new Date().toISOString();
            if (!groups[ts]) {
                groups[ts] = { timestamp: ts };
            }
            const modelKey = item.bot_model || 'unknown';
            groups[ts][modelKey] = item.metrics.overall_ethical_score;
            groups[ts][`${modelKey}_s_llm`] = item.metrics.s_llm_score;
        });

        return Object.values(groups).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    };

    const renderContent = () => {
        if (isLoading) {
            return (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center h-[400px] text-center">
                        <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
                        <h3 className="text-lg font-semibold mb-2">Loading Data...</h3>
                    </CardContent>
                </Card>
            );
        }

        if (data.length === 0) {
            return (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center h-[400px] text-center">
                        <RefreshCw className="h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No Data Yet</h3>
                        <p className="text-muted-foreground max-w-md mb-4">
                            Send a query from the Citizen Portal to see real-time metrics here.
                        </p>
                        <Button onClick={handleRefresh} variant="outline">
                            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                        </Button>
                    </CardContent>
                </Card>
            );
        }

        const availableModels = Array.from(new Set(data.map(item => item.bot_model || 'unknown')));
        const comparisonData = getComparisonData();

        switch (view) {
            case 'comparison':
                return (
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Model Performance Comparison</CardTitle>
                                <CardDescription>Comparing Overall Ethical Scores across different LLMs.</CardDescription>
                            </CardHeader>
                            <CardContent className="h-[400px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={comparisonData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="timestamp" />
                                        <YAxis domain={[0, 100]} />
                                        <Tooltip />
                                        <Legend />
                                        {availableModels.map((model) => (
                                            <Line
                                                key={model}
                                                type="monotone"
                                                dataKey={model}
                                                name={model}
                                                stroke={MODEL_COLORS[model] || '#8884d8'}
                                                strokeWidth={3}
                                                dot={true}
                                                connectNulls={true}
                                            />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Weighted Risk comparison (S_LLM)</CardTitle>
                                <CardDescription>Comparing S_LLM Scores across different LLMs.</CardDescription>
                            </CardHeader>
                            <CardContent className="h-[400px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={comparisonData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="timestamp" />
                                        <YAxis domain={[0, 100]} />
                                        <Tooltip />
                                        <Legend />
                                        {availableModels.map((model) => (
                                            <Line
                                                key={`${model}_s_llm`}
                                                type="monotone"
                                                dataKey={`${model}_s_llm`}
                                                name={`${model} (S_LLM)`}
                                                stroke={MODEL_COLORS[model] || '#8884d8'}
                                                strokeWidth={2}
                                                strokeDasharray="5 5"
                                                dot={true}
                                                connectNulls={true}
                                            />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>
                );

            case 'score':
                return (
                    <Card>
                        <CardHeader>
                            <CardTitle>Overall Ethical Score Trend {selectedModel !== 'all' && `(${selectedModel})`}</CardTitle>
                            <CardDescription>
                                {selectedModel === 'all' ? 'Showing all models mixed.' : `Showing results only for ${selectedModel}.`}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="h-[400px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={filteredData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="metrics.overall_ethical_score" name="Ethical Score" stroke={MODEL_COLORS[selectedModel] || "#8884d8"} strokeWidth={3} dot={true} />
                                    <Line type="monotone" dataKey="metrics.s_llm_score" name="S_LLM Score" stroke="#82ca9d" strokeWidth={2} dot={true} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                );

            case 'tokens':
                return (
                    <Card>
                        <CardHeader>
                            <CardTitle>Token Usage {selectedModel !== 'all' && `(${selectedModel})`}</CardTitle>
                            <CardDescription>Monitor input and output token consumption.</CardDescription>
                        </CardHeader>
                        <CardContent className="h-[400px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={filteredData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="tokens.total_tokens" name="Total Tokens" stroke="#82ca9d" strokeWidth={2} dot={true} />
                                    <Line type="monotone" dataKey="tokens.input_tokens" name="Input Tokens" stroke="#8884d8" strokeWidth={2} dot={true} />
                                    <Line type="monotone" dataKey="tokens.output_tokens" name="Output Tokens" stroke="#ffc658" strokeWidth={2} dot={true} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                );

            case 'dimensions':
                const lastPoint = filteredData[filteredData.length - 1] || data[data.length - 1];
                const dimensionKeys = lastPoint ? Object.keys(lastPoint.dimensions) : [];

                return (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {dimensionKeys.map(key => (
                            <Card key={key}>
                                <CardHeader className="p-4 pb-2">
                                    <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                                        {lastPoint.dimensions[key].name || key}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="h-[200px] p-4 pt-0">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={filteredData} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} strokeOpacity={0.1} />
                                            <XAxis
                                                dataKey="timestamp"
                                                tick={false}
                                                label={{ value: 'Time', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#888' }}
                                                axisLine={{ stroke: '#888888', strokeOpacity: 0.3 }}
                                            />
                                            <YAxis
                                                domain={[0, 100]}
                                                tick={{ fontSize: 10, fill: '#888' }}
                                                tickCount={5}
                                                label={{ value: 'Score', angle: -90, position: 'insideLeft', offset: 15, fontSize: 10, fill: '#888' }}
                                                axisLine={{ stroke: '#888888', strokeOpacity: 0.3 }}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                                labelStyle={{ color: '#1a1a1a', fontWeight: 'bold', fontSize: '11px' }}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey={`dimensions.${key}.overall_score`}
                                                stroke={MODEL_COLORS[selectedModel] || "#f43f5e"}
                                                strokeWidth={2.5}
                                                dot={false}
                                                activeDot={{ r: 4, strokeWidth: 0 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                    <div className="flex justify-between items-center mt-2 px-2">
                                        <span className="text-xs text-muted-foreground italic">Current Score</span>
                                        <div className="text-xl font-bold text-primary">
                                            {filteredData.length > 0 ? Math.round(filteredData[filteredData.length - 1].dimensions[key].overall_score) : '-'}%
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                );

            case 'rag':
                const currentRag = filteredData.length > 0 ? filteredData[filteredData.length - 1].rag_sources : [];
                return (
                    <div className="grid gap-4">
                        <h2 className="text-xl font-semibold mb-2">Active RAG References {selectedModel !== 'all' && `(${selectedModel})`}</h2>
                        {currentRag.length === 0 && <p className="text-muted-foreground">No RAG sources in selected data.</p>}
                        {currentRag.map((source: any, idx: number) => (
                            <Card
                                key={idx}
                                className="hover:bg-muted/50 transition-colors cursor-pointer"
                                onClick={() => window.open(`/api/pdf?file=${encodeURIComponent(source.doc)}&page=${source.page}`, '_blank')}
                            >
                                <CardHeader>
                                    <CardTitle className="flex justify-between items-center text-base">
                                        <span className="flex items-center gap-2">
                                            <FileText className="h-4 w-4" />
                                            {source.doc}
                                        </span>
                                        <span className="text-sm font-normal text-muted-foreground">Score: {(source.score).toFixed(1)}%</span>
                                    </CardTitle>
                                    <CardDescription>
                                        Page {source.page} - Click to open PDF
                                    </CardDescription>
                                </CardHeader>
                            </Card>
                        ))}
                    </div>
                )
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-muted/30 p-4 rounded-lg border">
                <div className="flex flex-wrap gap-2">
                    <Button variant={view === 'comparison' ? 'default' : 'ghost'} onClick={() => setView('comparison')} className="flex items-center gap-2">
                        <RefreshCw className="h-4 w-4" /> Comparison
                    </Button>
                    <Button variant={view === 'score' ? 'default' : 'ghost'} onClick={() => setView('score')} className="flex items-center gap-2">
                        <Activity className="h-4 w-4" /> Score Trend
                    </Button>
                    <Button variant={view === 'tokens' ? 'default' : 'ghost'} onClick={() => setView('tokens')} className="flex items-center gap-2">
                        <BadgeCheck className="h-4 w-4" /> Tokens
                    </Button>
                    <Button variant={view === 'dimensions' ? 'default' : 'ghost'} onClick={() => setView('dimensions')} className="flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4" /> Dimensions
                    </Button>
                    <Button variant={view === 'rag' ? 'default' : 'ghost'} onClick={() => setView('rag')} className="flex items-center gap-2">
                        <FileText className="h-4 w-4" /> RAG Sources
                    </Button>
                </div>

                <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">Filter Model:</span>
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                        <SelectTrigger className="w-[180px] bg-background">
                            <SelectValue placeholder="Select Model" />
                        </SelectTrigger>
                        <SelectContent>
                            {ALL_MODELS.map(m => (
                                <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
                        <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            <div className="min-h-[400px]">
                {renderContent()}
            </div>
        </div>
    );
}
