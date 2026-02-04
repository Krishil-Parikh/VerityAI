import { Conversation, Message, DimensionScore, MetricBreakdown } from '@/types';
import { dummyConversations } from '@/lib/dummyData';
import { getScoreStatus } from '@/lib/formatters';

// In-memory store for conversations
let conversations: Conversation[] = JSON.parse(
  JSON.stringify(dummyConversations)
);
let subscribers: Array<() => void> = [];

const calculateOverallScore = (scores: DimensionScore[]): number => {
  if (scores.length === 0) return 0;
  const sum = scores.reduce((acc, s) => acc + s.score, 0);
  return Math.round(sum / scores.length);
};

// Dummy AI response generator
const generateDummyResponse = (question: string): string => {
  const responses: { [key: string]: string } = {
    default:
      'Thank you for your inquiry. Based on available public records, here is the information: This response is generated based on verified departmental data and public records. For more detailed information, please refer to the official departmental portal.',
  };

  return responses['default'];
};

// Dummy metrics generator
const generateDummyMetrics = (): {
  dimensionScores: DimensionScore[];
  metricBreakdown: MetricBreakdown;
} => {
  const baseScores = [
    { name: 'Bias & Fairness', base: 85 },
    { name: 'Data Grounding & Drift', base: 90 },
    { name: 'Explainability & Transparency', base: 87 },
    { name: 'Ethical Alignment', base: 88 },
    { name: 'Human Control', base: 82 },
    { name: 'Legal Compliance', base: 92 },
    { name: 'Security & Robustness', base: 80 },
    { name: 'Response Quality', base: 85 },
  ];

  const variance = Math.random() * 10 - 5;
  const dimensionScores = baseScores.map((item) => ({
    name: item.name,
    score: Math.max(50, Math.min(100, Math.round(item.base + variance))),
    status: getScoreStatus(Math.max(50, Math.min(100, Math.round(item.base + variance)))),
  }));

  return {
    dimensionScores,
    metricBreakdown: {
      statisticalParity: Math.random() * 0.1,
      equalOpportunity: 0.95 + Math.random() * 0.05,
      disparateImpact: 0.93 + Math.random() * 0.07,
      f1Score: 0.90 + Math.random() * 0.1,
      taskCompletionRate: 0.98 + Math.random() * 0.02,
      lawfulnessAssessment: 'Pass',
      piiDisclosure: 0,
    },
  };
};

export const conversationStore = {
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
    };

    conversations.unshift(newConversation);
    notifySubscribers();
    return JSON.parse(JSON.stringify(newConversation));
  },

  // Add AI response with dummy evaluation
  addAIResponse: (conversationId: string): Promise<Conversation | undefined> => {
    return new Promise((resolve) => {
      const conv = conversations.find((c) => c.id === conversationId);
      if (conv) {
        const lastUserMsg = [...conv.messages]
          .reverse()
          .find((m) => m.role === 'user');

        if (lastUserMsg) {
          const content = generateDummyResponse(lastUserMsg.content);
          const { dimensionScores, metricBreakdown } =
            generateDummyMetrics();
          const overallScore = calculateOverallScore(dimensionScores);

          const aiMsg: Message = {
            id: `msg-ai-${Date.now()}`,
            role: 'assistant',
            content,
            timestamp: new Date(),
            ethicalScore: overallScore,
            dimensionScores,
            metricBreakdown,
          };

          conv.messages.push(aiMsg);
          conv.overallEthicalScore = overallScore;
          conv.dimensionScores = dimensionScores;
          conv.updatedAt = new Date();
          notifySubscribers();

          // Simulate evaluation delay before updating status
          setTimeout(() => {
            if (conv) {
              conv.status =
                overallScore >= 85
                  ? 'safe'
                  : overallScore >= 70
                    ? 'needs_review'
                    : 'violation';
              conv.updatedAt = new Date();
              notifySubscribers();
            }
            resolve(conv ? JSON.parse(JSON.stringify(conv)) : undefined);
          }, 1000);
        }
      } else {
        resolve(undefined);
      }
    });
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
