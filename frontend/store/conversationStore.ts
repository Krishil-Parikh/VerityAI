import { Conversation, Message, DimensionScore, MetricBreakdown, RagSource, BackendResponse } from '@/types';
import { getScoreStatus } from '@/lib/formatters';
import { metricsStore } from './metricsStore';

// In-memory store for conversations - start empty (no dummy data)
let conversations: Conversation[] = [];
let subscribers: Array<() => void> = [];
let isInitialized = false;
let seenConvIds: Set<string> = new Set();

const calculateOverallScore = (scores: DimensionScore[]): number => {
  if (scores.length === 0) return 0;
  const sum = scores.reduce((acc, s) => acc + s.score, 0);
  return Math.round(sum / scores.length);
};

// Call the real backend API
const callBackendAPI = async (query: string, conversationId: string, model: string = 'llama3', mode: 'online' | 'offline' = 'offline'): Promise<{
  response: string;
  dimensionScores: DimensionScore[];
  metricBreakdown: MetricBreakdown;
  overallScore: number;
  ragSources: RagSource[];
  fullResponse: BackendResponse | null;
}> => {
  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_query: query,
        bot_model: model,
        mode: mode,
        conversation_id: conversationId
      }),
    });

    if (!res.ok) {
      throw new Error(`Backend error: ${res.status}`);
    }

    const data: BackendResponse = await res.json();

    // Add timestamp if not present
    if (!data.timestamp) {
      data.timestamp = new Date().toISOString();
    }

    // Map backend dimensions to frontend format
    const dimensionScores: DimensionScore[] = Object.keys(data.dimensions || {}).map(key => ({
      name: data.dimensions[key].name,
      score: data.dimensions[key].overall_score,
      status: getScoreStatus(data.dimensions[key].overall_score),
    }));

    // Map metrics to frontend format (scores are now 0-100 from backend)
    const metricBreakdown: MetricBreakdown = {
      statisticalParity: data.metrics?.spd || 0,
      equalOpportunity: data.metrics?.eop || 0,
      disparateImpact: data.metrics?.di || 100,
      f1Score: data.metrics?.accuracy || 90,
      taskCompletionRate: data.grounding?.score || 80,
      lawfulnessAssessment: data.metrics?.lawfulness >= 50 ? 'Pass' : 'Fail',
      piiDisclosure: 0,
    };

    return {
      response: data.ai_response,
      dimensionScores,
      metricBreakdown,
      overallScore: data.metrics?.s_llm_score || data.metrics?.overall_ethical_score || 0,
      ragSources: data.rag_sources || [],
      fullResponse: data,
    };
  } catch (error) {
    console.error('Backend API error:', error);
    // Return fallback response if backend fails
    return {
      response: 'Sorry, I am unable to process your request at the moment. Please try again later or contact support.',
      dimensionScores: [],
      metricBreakdown: {
        statisticalParity: 0,
        equalOpportunity: 95,
        disparateImpact: 100,
        f1Score: 90,
        taskCompletionRate: 80,
        lawfulnessAssessment: 'N/A',
        piiDisclosure: 0,
      },
      overallScore: 0,
      ragSources: [],
      fullResponse: null,
    };
  }
};

// Load historical conversations from backend
const loadConversationsFromBackend = async (): Promise<void> => {
  try {
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const res = await fetch(`${BACKEND_URL}/conversations?limit=50`);
    
    if (!res.ok) {
      console.error('Failed to load conversations:', res.status);
      return;
    }
    
    const data = await res.json();
    
    if (data.success && Array.isArray(data.conversations)) {
      // Convert backend format to frontend Conversation format
      const loadedConversations: Conversation[] = data.conversations.map((conv: {
        id: string;
        timestamp: string;
        user_query: string;
        ai_response: string;
        overall_ethical_score: number;
        s_llm_score: number;
        risk_band: string;
        final_label: string;
        latency_ms: number;
        grounding_score: number;
        bot_model: string;
        dimensions?: Record<string, any>;
      }) => {
        const score = conv.s_llm_score || conv.overall_ethical_score || 0;
        const status = score >= 85 ? 'safe' : score >= 70 ? 'needs_review' : 'violation';
        
        const dims = conv.dimensions;
        const dimensionScores: DimensionScore[] = dims ? Object.keys(dims).map(key => ({
            name: dims[key].name || key,
            score: dims[key].overall_score || 0,
            status: getScoreStatus(dims[key].overall_score || 0),
        })) : [];
        
        if (dimensionScores.length > 0) {
            console.log(`[Store] Mapped ${dimensionScores.length} dimensions for ${conv.id}`);
        }

        return {
          id: conv.id || `conv-${Date.now()}-${Math.random()}`,
          citizenId: 'citizen-historical',
          messages: [
            {
              id: `msg-user-${conv.id}`,
              role: 'user' as const,
              content: conv.user_query || '',
              timestamp: new Date(conv.timestamp),
            },
            {
              id: `msg-ai-${conv.id}`,
              role: 'assistant' as const,
              content: conv.ai_response || '',
              timestamp: new Date(conv.timestamp),
              ethicalScore: score,
            }
          ],
          overallEthicalScore: score,
          status: status as 'safe' | 'needs_review' | 'violation',
          createdAt: new Date(conv.timestamp),
          updatedAt: new Date(conv.timestamp),
          dimensionScores: dimensionScores,
          botModel: conv.bot_model || 'llama3',
        };
      });
      
      // Clear existing and load from backend
      conversations = [];
      seenConvIds.clear();
      
      for (const conv of loadedConversations) {
        if (!seenConvIds.has(conv.id)) {
          seenConvIds.add(conv.id);
          conversations.push(conv);
        }
      }
      
      // Sort by date (newest first)
      conversations.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      
      isInitialized = true;
      notifySubscribers();
      console.log(`✅ Loaded ${conversations.length} historical conversations`);
    }
  } catch (error) {
    console.error('Error loading conversations from backend:', error);
  }
};

export const conversationStore = {
  // Load conversations from backend
  loadConversations: loadConversationsFromBackend,

  // Check if store is initialized
  isInitialized: (): boolean => {
    return isInitialized;
  },

  // Get all conversations
  getConversations: (): Conversation[] => {
    return JSON.parse(JSON.stringify(conversations));
  },

  // Get a specific conversation
  getConversation: (id: string): Conversation | undefined => {
    return JSON.parse(
      JSON.stringify(conversations.find((c) => c.id === id))
    );
  },

  // Add a new message to a conversation
  addMessage: (
    conversationId: string,
    message: Message
  ): Conversation | undefined => {
    const conv = conversations.find((c) => c.id === conversationId);
    if (conv) {
      conv.messages.push(message);
      conv.updatedAt = new Date();
      notifySubscribers();
    }
    return conv ? JSON.parse(JSON.stringify(conv)) : undefined;
  },

  // Create a new conversation with a user message
  createConversation: (citizenId: string, userMessage: string): Conversation => {
    const newConvId = `conv-${Date.now()}`;
    const userMsg: Message = {
      id: `msg-user-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };

    const newConversation: Conversation = {
      id: newConvId,
      citizenId,
      messages: [userMsg],
      overallEthicalScore: 0,
      status: 'evaluating',
      createdAt: new Date(),
      updatedAt: new Date(),
      dimensionScores: [],
      botModel: 'llama3',
    };

    conversations.unshift(newConversation);
    notifySubscribers();
    return JSON.parse(JSON.stringify(newConversation));
  },

  // Add AI response from real backend
  addAIResponse: async (conversationId: string, model: string = 'llama3', mode: 'online' | 'offline' = 'offline'): Promise<Conversation | undefined> => {
    const conv = conversations.find((c) => c.id === conversationId);
    if (!conv) return undefined;

    const lastUserMsg = [...conv.messages]
      .reverse()
      .find((m) => m.role === 'user');

    if (!lastUserMsg) return undefined;

    // Handle 'all' model option - evaluate with all models based on mode
    if (model === 'all') {
      // Use different model lists for offline vs online
      const ALL_MODELS = mode === 'online' 
        ? ['llama-3.2-3b', 'llama-3.1-8b', 'gemma-2-9b', 'qwen2.5-7b', 'mistral-7b']  // Free online models
        : ['llama3', 'deepseek-coder:6.7b', 'qwen2.5:3b', 'tinyllama:latest', 'gemma3:12b'];  // Local Ollama models
      
      // Run all models in parallel
      const results = await Promise.all(
        ALL_MODELS.map(async (m) => {
          try {
            const result = await callBackendAPI(lastUserMsg.content, conversationId, m, mode);
            return { model: m, ...result };
          } catch (error) {
            console.error(`Error with model ${m}:`, error);
            return null;
          }
        })
      );
      
      // Filter out failed results
      const validResults = results.filter(r => r !== null);
      
      // Create a summary message with all results
      const summaryContent = validResults.map(r => 
        `**[${r!.model}]** (Score: ${r!.overallScore})\n${r!.response}`
      ).join('\n\n---\n\n');
      
      // Use the best scoring result for the main metrics
      const bestResult = validResults.reduce((best, curr) => 
        (curr!.overallScore > (best?.overallScore || 0)) ? curr : best
      , validResults[0]);
      
      const aiMsg: Message = {
        id: `msg-ai-${Date.now()}`,
        role: 'assistant',
        content: `## Multi-Model Evaluation Results\n\n${summaryContent}`,
        timestamp: new Date(),
        ethicalScore: bestResult?.overallScore || 0,
        dimensionScores: bestResult?.dimensionScores || [],
        metricBreakdown: bestResult?.metricBreakdown,
        ragSources: bestResult?.ragSources || [],
      };

      conv.messages.push(aiMsg);
      conv.overallEthicalScore = bestResult?.overallScore || 0;
      conv.dimensionScores = bestResult?.dimensionScores || [];
      conv.updatedAt = new Date();
      conv.status = (bestResult?.overallScore || 0) >= 85 ? 'safe' : (bestResult?.overallScore || 0) >= 70 ? 'needs_review' : 'violation';

      notifySubscribers();
      
      // Push all successful results to metrics store for comparison
      validResults.forEach(r => {
        if (r && r.fullResponse) {
          metricsStore.addMetricsPoint(r.fullResponse);
        }
      });

      return JSON.parse(JSON.stringify(conv));
    }

    // Single model call
    const {
      response: content,
      dimensionScores,
      metricBreakdown,
      overallScore,
      ragSources,
      fullResponse,
    } = await callBackendAPI(lastUserMsg.content, conversationId, model, mode);

    const aiMsg: Message = {
      id: `msg-ai-${Date.now()}`,
      role: 'assistant',
      content,
      timestamp: new Date(),
      ethicalScore: overallScore,
      dimensionScores,
      metricBreakdown,
      ragSources,  // Store citations in the message
    };

    conv.messages.push(aiMsg);
    conv.overallEthicalScore = overallScore;
    conv.dimensionScores = dimensionScores;
    conv.updatedAt = new Date();

    // Determine status based on score
    conv.status =
      overallScore >= 85
        ? 'safe'
        : overallScore >= 70
          ? 'needs_review'
          : 'violation';

    notifySubscribers();

    // Push to metrics store for graphs (event-driven, not polling)
    if (fullResponse) {
      metricsStore.addMetricsPoint(fullResponse);
    }

    return JSON.parse(JSON.stringify(conv));
  },

  // Get full history for a specific conversation from backend
  fetchConversationHistory: async (id: string): Promise<Conversation | undefined> => {
    try {
      const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const res = await fetch(`${BACKEND_URL}/conversation/${id}`);
      
      if (!res.ok) {
        console.error('Failed to fetch conversation history:', res.status);
        return undefined;
      }
      
      const data = await res.json();
      
      if (data.success) {
        // Map backend messages to frontend format
        const messages: Message[] = data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.timestamp),
          ethicalScore: m.ethicalScore,
        }));
        
        const score = data.overall_ethical_score || 0;
        const status = score >= 85 ? 'safe' : score >= 70 ? 'needs_review' : 'violation';
        
        const dims = data.dimensions;
        const dimensionScores: DimensionScore[] = dims ? Object.keys(dims).map(key => ({
            name: dims[key].name || key,
            score: dims[key].overall_score || 0,
            status: getScoreStatus(dims[key].overall_score || 0),
        })) : [];

        console.log(`[Store] Historical conversation ${data.id} has ${dimensionScores.length} dimension scores`);

        const updatedConv: Conversation = {
          id: data.id,
          citizenId: 'citizen-historical',
          messages: messages,
          overallEthicalScore: score,
          status: status as 'safe' | 'needs_review' | 'violation',
          createdAt: messages.length > 0 ? messages[0].timestamp : new Date(),
          updatedAt: messages.length > 1 ? messages[messages.length - 1].timestamp : new Date(),
          dimensionScores: dimensionScores,
          botModel: data.bot_model || 'llama3',
        };
        
        // Update in-memory storage
        const idx = conversations.findIndex(c => c.id === id);
        if (idx !== -1) {
          conversations[idx] = updatedConv;
        } else {
          conversations.push(updatedConv);
        }
        
        notifySubscribers();
        return updatedConv;
      }
    } catch (error) {
      console.error('Error fetching conversation history:', error);
    }
    return undefined;
  },

  // Delete a conversation
  deleteConversation: (id: string): void => {
    conversations = conversations.filter(c => c.id !== id);
    seenConvIds.delete(id);
    notifySubscribers();
  },

  // Subscribe to changes
  subscribe: (callback: () => void) => {
    subscribers.push(callback);
    return () => {
      subscribers = subscribers.filter((sub) => sub !== callback);
    };
  },
};

const notifySubscribers = () => {
  subscribers.forEach((callback) => callback());
};
