'use client';

import { useState, useEffect, useMemo } from 'react';
import { Conversation } from '@/types';
import { ConversationTable } from '@/components/admin/ConversationTable';
import { ConversationDetail } from '@/components/admin/ConversationDetail';
import { FiltersPanel, FilterValues } from '@/components/admin/FiltersPanel';
import { MetricsRadarCard } from '@/components/admin/MetricsRadarCard';
import { Card } from '@/components/ui/card';
import { conversationStore } from '@/store/conversationStore';

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [filters, setFilters] = useState<FilterValues>({
    status: 'all',
    minScore: 0,
    maxScore: 100,
  });

  // Subscribe to conversation updates
  useEffect(() => {
    // Load historical conversations from backend
    const loadData = async () => {
      await conversationStore.loadConversations();
      setConversations(conversationStore.getConversations());
    };
    
    loadData();

    const unsubscribe = conversationStore.subscribe(() => {
      setConversations(conversationStore.getConversations());
    });

    return unsubscribe;
  }, []);

  // Apply filters
  const filteredConversations = useMemo(() => {
    return conversations.filter((conv) => {
      if (
        filters.status !== 'all' &&
        conv.status !== filters.status
      ) {
        return false;
      }

      if (
        conv.overallEthicalScore < filters.minScore ||
        conv.overallEthicalScore > filters.maxScore
      ) {
        return false;
      }

      return true;
    });
  }, [conversations, filters]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Conversations
        </h1>
        <p className="text-muted-foreground mt-1">
          View and audit all citizen-assistant conversations
        </p>
      </div>

      <FiltersPanel onFilterChange={setFilters} />

      <div className="space-y-6">
        <Card className="border-border overflow-hidden">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              All Conversations ({filteredConversations.length})
            </h2>
            <ConversationTable
              conversations={filteredConversations}
              onViewDetails={setSelectedConversation}
            />
          </div>
        </Card>

        {selectedConversation && selectedConversation.status !== 'evaluating' && selectedConversation.dimensionScores.length > 0 && (
          <div className="max-w-md ml-auto">
            <MetricsRadarCard
              dimensionScores={selectedConversation.dimensionScores}
              overallScore={selectedConversation.overallEthicalScore}
            />
          </div>
        )}
      </div>

      {selectedConversation && (
        <ConversationDetail
          conversation={selectedConversation}
          onClose={() => setSelectedConversation(null)}
        />
      )}
    </div>
  );
}
