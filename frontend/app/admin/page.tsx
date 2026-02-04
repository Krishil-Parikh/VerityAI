'use client';

import { useState, useEffect } from 'react';
import { Conversation } from '@/types';
import { OverviewCards } from '@/components/admin/OverviewCards';
import { TrafficLightStream } from '@/components/admin/TrafficLightStream';
import { SimpleChart } from '@/components/admin/SimpleChart';
import { MetricsRadarCard } from '@/components/admin/MetricsRadarCard';
import { conversationStore } from '@/store/conversationStore';
import { metricsStore } from '@/store/metricsStore';

export default function AdminPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [, forceUpdate] = useState({});

  // Subscribe to conversation updates from store
  useEffect(() => {
    // Load historical conversations and metrics from backend
    const loadData = async () => {
      await Promise.all([
        conversationStore.loadConversations(),
        metricsStore.loadHistory()
      ]);
      setConversations(conversationStore.getConversations());
      forceUpdate({}); // Trigger re-render to update metrics-dependent components
    };
    
    loadData();

    // Subscribe to updates
    const unsubscribeConv = conversationStore.subscribe(() => {
      setConversations(conversationStore.getConversations());
    });
    
    const unsubscribeMetrics = metricsStore.subscribe(() => {
      forceUpdate({});
    });

    return () => {
      unsubscribeConv();
      unsubscribeMetrics();
    };
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Government Oversight & Ethical Audit Monitoring
        </p>
      </div>

      <OverviewCards conversations={conversations} />

      <TrafficLightStream
        conversations={conversations}
        onSelectConversation={setSelectedConversation}
      />

      {selectedConversation && selectedConversation.status !== 'evaluating' && selectedConversation.dimensionScores.length > 0 && (
        <div className="w-full">
          <MetricsRadarCard
            dimensionScores={selectedConversation.dimensionScores}
            overallScore={selectedConversation.overallEthicalScore}
          />
        </div>
      )}

      <SimpleChart conversations={conversations} />
    </div>
  );
}
