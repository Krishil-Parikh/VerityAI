export type UserRole = 'citizen' | 'admin';

export type ConversationStatus = 'safe' | 'needs_review' | 'violation' | 'evaluating';

export interface DimensionScore {
  name: string;
  score: number;
  status: 'safe' | 'needs_review' | 'violation';
}

export interface MetricBreakdown {
  statisticalParity: number;
  equalOpportunity: number;
  disparateImpact: number;
  f1Score: number;
  taskCompletionRate: number;
  lawfulnessAssessment: string;
  piiDisclosure: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  ethicalScore?: number;
  dimensionScores?: DimensionScore[];
  metricBreakdown?: MetricBreakdown;
}

export interface Conversation {
  id: string;
  citizenId: string;
  messages: Message[];
  overallEthicalScore: number;
  status: ConversationStatus;
  createdAt: Date;
  updatedAt: Date;
  dimensionScores: DimensionScore[];
}

export interface User {
  email: string;
  role: UserRole;
}

export interface DepartmentProfile {
  id: string;
  name: string;
  weights: {
    bias: number;
    dataGrounding: number;
    explainability: number;
    ethicalAlignment: number;
    humanControl: number;
    legal: number;
    security: number;
    quality: number;
  };
}

export interface AlertSettings {
  minEthicalScore: number;
  redThreshold: number;
  enableEmailAlerts: boolean;
  enableSlackAlerts: boolean;
}
