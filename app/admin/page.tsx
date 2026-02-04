'use client';

import { useState, useEffect } from 'react';
import { Conversation } from '@/types';
import { OverviewCards } from '@/components/admin/OverviewCards';
import { TrafficLightStream } from '@/components/admin/TrafficLightStream';
import { SimpleChart } from '@/components/admin/SimpleChart';
import { MetricsRadarCard } from '@/components/admin/MetricsRadarCard';
import { conversationStore } from '@/store/conversationStore';

export default function AdminPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  // Subscribe to conversation updates from store
  useEffect(() => {
    // Initial load
    setConversations(conversationStore.getConversations());

    // Subscribe to updates
    const unsubscribe = conversationStore.subscribe(() => {
      setConversations(conversationStore.getConversations());
    });

    return unsubscribe;
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrafficLightStream
            conversations={conversations}
            onSelectConversation={setSelectedConversation}
          />
        </div>

        {selectedConversation && selectedConversation.status !== 'evaluating' && selectedConversation.dimensionScores.length > 0 && (
          <MetricsRadarCard
            dimensionScores={selectedConversation.dimensionScores}
            overallScore={selectedConversation.overallEthicalScore}
          />
        )}
      </div>

      <SimpleChart conversations={conversations} />
    </div>
  );
}
