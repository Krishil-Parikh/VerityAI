"use client";

import React, { useEffect, useState } from 'react';
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

type ViewType = 'score' | 'tokens' | 'dimensions' | 'rag';

export function GraphsDashboard() {
    const [data, setData] = useState<BackendResponse[]>([]);
    const [view, setView] = useState<ViewType>('score');
    const [queryCount, setQueryCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch initial data from backend AND subscribe to metricsStore
    useEffect(() => {
        const fetchInitialData = async () => {
            setIsLoading(true);
            try {
                // Load historical data from backend (this is the key fix!)
                await metricsStore.loadHistory();
            } catch (error) {
                console.error('Error fetching initial telemetry:', error);
            }
            
            // Load from store
            setData(metricsStore.getMetricsHistory());
            setQueryCount(metricsStore.getHistoryCount());
            setIsLoading(false);
        };

        fetchInitialData();

        // Subscribe to store changes for future updates
        const unsubscribe = metricsStore.subscribe(() => {
            setData(metricsStore.getMetricsHistory());
            setQueryCount(metricsStore.getHistoryCount());
        });

        return () => unsubscribe();
    }, []);

    const handleRefresh = async () => {
        setIsLoading(true);
        try {
            // Reload full history from backend
            await metricsStore.loadHistory();
        } catch (error) {
            console.error('Error refreshing:', error);
        }
        setIsLoading(false);
    };

    const handleClearData = () => {
        metricsStore.clearHistory();
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
                            Graphs update automatically when new queries are processed.
                        </p>
                        <Button onClick={handleRefresh} variant="outline">
                            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                        </Button>
                    </CardContent>
                </Card>
            );
        }

        switch (view) {
            case 'score':
                return (
                    <Card>
                        <CardHeader>
                            <CardTitle>Overall Ethical Score</CardTitle>
                            <CardDescription>Updates automatically when new queries are processed. {queryCount} queries recorded.</CardDescription>
                        </CardHeader>
                        <CardContent className="h-[400px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" />
                                    <YAxis domain={[0, 100]} />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="metrics.overall_ethical_score" name="Ethical Score" stroke="#8884d8" strokeWidth={3} dot={true} isAnimationActive={true} />
                                    <Line type="monotone" dataKey="metrics.s_llm_score" name="S_LLM Score" stroke="#82ca9d" strokeWidth={2} dot={true} isAnimationActive={true} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                );

            case 'tokens':
                return (
                    <Card>
                        <CardHeader>
                            <CardTitle>Token Usage</CardTitle>
                            <CardDescription>Monitor input and output token consumption per query.</CardDescription>
                        </CardHeader>
                        <CardContent className="h-[400px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Line type="monotone" dataKey="tokens.total_tokens" name="Total Tokens" stroke="#82ca9d" strokeWidth={2} dot={true} isAnimationActive={true} />
                                    <Line type="monotone" dataKey="tokens.input_tokens" name="Input Tokens" stroke="#8884d8" strokeWidth={2} dot={true} isAnimationActive={true} />
                                    <Line type="monotone" dataKey="tokens.output_tokens" name="Output Tokens" stroke="#ffc658" strokeWidth={2} dot={true} isAnimationActive={true} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                );

            case 'dimensions':
                // Get keys from the last data point or default if empty
                const lastPoint = data[data.length - 1];
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
                                <CardContent className="h-[150px] p-4 pt-0">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={data}>
                                            <XAxis dataKey="timestamp" hide />
                                            <YAxis domain={[0, 100]} hide />
                                            <Tooltip labelStyle={{ color: 'black' }} />
                                            <Line
                                                type="monotone"
                                                dataKey={`dimensions.${key}.overall_score`}
                                                stroke="#f43f5e"
                                                strokeWidth={2}
                                                dot={true}
                                                isAnimationActive={true}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                    <div className="text-2xl font-bold mt-2 text-right">
                                        {lastPoint ? Math.round(lastPoint.dimensions[key].overall_score) : '-'}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                );

            case 'rag':
                const currentRag = data.length > 0 ? data[data.length - 1].rag_sources : [];
                return (
                    <div className="grid gap-4">
                        <h2 className="text-xl font-semibold mb-2">Active RAG References (Latest Response)</h2>
                        {currentRag.length === 0 && <p className="text-muted-foreground">No RAG sources in recent response.</p>}
                        {currentRag.map((source, idx) => (
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
                                        <span className="text-sm font-normal text-muted-foreground">Score: {(source.score * 100).toFixed(1)}%</span>
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
            {/* Navigation */}
            <div className="flex flex-wrap gap-2 items-center justify-between">
                <div className="flex flex-wrap gap-2">
                    <Button
                        variant={view === 'score' ? 'default' : 'outline'}
                        onClick={() => setView('score')}
                        className="flex items-center gap-2"
                    >
                        <Activity className="h-4 w-4" /> Overall Score
                    </Button>
                    <Button
                        variant={view === 'tokens' ? 'default' : 'outline'}
                        onClick={() => setView('tokens')}
                        className="flex items-center gap-2"
                    >
                        <BadgeCheck className="h-4 w-4" /> Tokens
                    </Button>
                    <Button
                        variant={view === 'dimensions' ? 'default' : 'outline'}
                        onClick={() => setView('dimensions')}
                        className="flex items-center gap-2"
                    >
                        <ShieldAlert className="h-4 w-4" /> Dimensions
                    </Button>
                    <Button
                        variant={view === 'rag' ? 'default' : 'outline'}
                        onClick={() => setView('rag')}
                        className="flex items-center gap-2"
                    >
                        <FileText className="h-4 w-4" /> RAG Sources
                    </Button>
                </div>
                
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
                    </Button>
                    {data.length > 0 && (
                        <Button variant="outline" size="sm" onClick={handleClearData}>
                            Clear Data
                        </Button>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="min-h-[400px]">
                {renderContent()}
            </div>
        </div>
    );
}
