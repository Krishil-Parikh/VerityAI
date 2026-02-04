'use client';

import { Conversation } from '@/types';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChatMessage } from '@/components/citizen/ChatMessage';
import { MetricsGrid } from './MetricsGrid';
import { MetricBreakdownList } from './MetricBreakdownList';
import { X, Download } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ConversationDetailProps {
  conversation: Conversation;
  onClose: () => void;
}

export function ConversationDetail({
  conversation,
  onClose,
}: ConversationDetailProps) {
  const { toast } = useToast();

  const handleDownloadReport = () => {
    toast({
      title: 'Report Generated',
      description: 'Audit report has been generated and downloaded.',
    });
  };

  const lastAIMessage = [...conversation.messages]
    .reverse()
    .find((m) => m.role === 'assistant');

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-end">
      <div className="bg-background w-full max-w-2xl h-full overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-background border-b border-border p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-foreground">
              Conversation Details
            </h2>
            <p className="text-sm text-muted-foreground mt-1">{conversation.id}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="gap-2"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <Card className="border-border p-4">
              <p className="text-xs font-medium text-muted-foreground uppercase">User ID</p>
              <p className="text-sm font-semibold text-foreground mt-1">
                {conversation.citizenId}
              </p>
            </Card>
            <Card className="border-border p-4">
              <p className="text-xs font-medium text-muted-foreground uppercase">
                Timestamp
              </p>
              <p className="text-sm font-semibold text-foreground mt-1">
                {new Date(conversation.createdAt).toLocaleString()}
              </p>
            </Card>
          </div>

          {/* Transcript */}
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Conversation Transcript
            </h3>
            <Card className="border-border p-4">
              <div className="space-y-3">
                {conversation.messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
              </div>
            </Card>
          </div>

          {/* Metrics Section */}
          {conversation.status === 'evaluating' ? (
            <Card className="border-border p-6 text-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground animate-spin" />
                <p className="text-sm text-muted-foreground font-medium">
                  Metrics are being computed…
                </p>
              </div>
            </Card>
          ) : (
            <>
              {/* Overall Score with Gradient */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  Overall Ethical Score
                </h3>
                <Card className="border-border p-8 text-center bg-gradient-to-b from-muted/50 to-background">
                  <div className="flex justify-center items-end gap-3">
                    <div>
                      <div
                        className={`text-6xl font-bold ${conversation.overallEthicalScore >= 85
                            ? 'text-green-600 dark:text-green-500'
                            : conversation.overallEthicalScore >= 70
                              ? 'text-amber-600 dark:text-amber-500'
                              : 'text-red-600 dark:text-red-500'
                          }`}
                      >
                        {conversation.overallEthicalScore}
                      </div>
                    </div>
                    <div className="text-sm font-medium text-muted-foreground mb-2">
                      /100
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mt-4 font-medium">
                    {conversation.status === 'safe'
                      ? '✓ Ethical standards met'
                      : conversation.status === 'needs_review'
                        ? '⚠ Requires review'
                        : '✗ Policy violation'}
                  </p>
                </Card>
              </div>

              {/* Dimension Scores Grid - 2x4 */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  Ethical Dimensions
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {conversation.dimensionScores.map((dim) => {
                    const isHighScore = dim.score >= 85;
                    const isMediumScore =
                      dim.score >= 70 && dim.score < 85;
                    const isLowScore = dim.score < 70;

                    const bgColor = isHighScore
                      ? 'bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-800/30'
                      : isMediumScore
                        ? 'bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-800/30'
                        : 'bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-800/30';

                    const progressColor = isHighScore
                      ? 'bg-green-500'
                      : isMediumScore
                        ? 'bg-amber-500'
                        : 'bg-red-500';

                    const scoreColor = isHighScore
                      ? 'text-green-600 dark:text-green-500'
                      : isMediumScore
                        ? 'text-amber-600 dark:text-amber-500'
                        : 'text-red-600 dark:text-red-500';

                    return (
                      <Card
                        key={dim.name}
                        className={`border ${bgColor} p-4`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <p className="text-xs font-semibold text-foreground leading-tight">
                            {dim.name}
                          </p>
                          <span className={`text-lg font-bold ${scoreColor}`}>
                            {dim.score}
                          </span>
                        </div>

                        <div className="h-2 rounded-full bg-muted overflow-hidden mb-2">
                          <div
                            className={`h-full ${progressColor} transition-all rounded-full`}
                            style={{ width: `${dim.score}%` }}
                          />
                        </div>

                        <p className="text-xs font-medium text-muted-foreground capitalize">
                          {dim.status}
                        </p>
                      </Card>
                    );
                  })}
                </div>
              </div>

              {/* Detailed Metrics */}
              {lastAIMessage?.metricBreakdown && (
                <MetricBreakdownList
                  breakdown={lastAIMessage.metricBreakdown}
                />
              )}

              {/* Download Report */}
              <Button
                onClick={handleDownloadReport}
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
              >
                <Download className="h-4 w-4" />
                Download Audit Report (PDF)
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
