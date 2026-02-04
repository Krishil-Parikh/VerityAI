'use client';

import { Conversation } from '@/types';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatNumber } from '@/lib/formatters';
import { BarChart3, AlertTriangle, Clock, TrendingUp } from 'lucide-react';
import { metricsStore } from '@/store/metricsStore';

interface OverviewCardsProps {
    conversations: Conversation[];
}

export function OverviewCards({ conversations }: OverviewCardsProps) {
    const totalConversations = conversations.length;
    const avgScore =
        conversations.length > 0
            ? Math.round(
                conversations.reduce((sum, c) => sum + c.overallEthicalScore, 0) /
                conversations.length
            )
            : 0;
    const flaggedCount = conversations.filter(
        (c) => c.status !== 'safe'
    ).length;
    
    // Calculate average response time from metrics history
    const metricsHistory = metricsStore.getMetricsHistory();
    const avgResponseTime = metricsHistory.length > 0
        ? metricsHistory.reduce((sum, m) => sum + (m.tokens?.latency_ms || 0), 0) / metricsHistory.length / 1000
        : 0; // Convert ms to seconds

    const getScoreBadge = (score: number) => {
        if (score >= 85) return 'bg-green-100 text-green-900 dark:bg-green-900/30 dark:text-green-300';
        if (score >= 70) return 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-300';
        return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-300';
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card className="border-border">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-muted-foreground">
                            Total Conversations Today
                        </h3>
                        <BarChart3 className="h-4 w-4 text-blue-600" />
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {totalConversations}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                        {conversations.filter((c) => c.status === 'safe').length} safe
                    </p>
                </div>
            </Card>

            <Card className="border-border">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-muted-foreground">
                            Average Ethical Score
                        </h3>
                        <TrendingUp className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="flex items-baseline gap-2">
                        <p className={`text-3xl font-bold`}>
                            {avgScore}
                        </p>
                        <span className="text-xs text-muted-foreground">/100</span>
                    </div>
                </div>
            </Card>

            <Card className="border-border">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-muted-foreground">
                            Flagged Conversations
                        </h3>
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {flaggedCount}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                        {conversations.filter((c) => c.status === 'violation').length} violations
                    </p>
                </div>
            </Card>

            <Card className="border-border">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-muted-foreground">
                            Average Response Time
                        </h3>
                        <Clock className="h-4 w-4 text-blue-600" />
                    </div>
                    <p className="text-3xl font-bold text-foreground">
                        {formatNumber(avgResponseTime, 1)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">seconds</p>
                </div>
            </Card>
        </div>
    );
}
