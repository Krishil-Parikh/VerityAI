export type UserRole = 'citizen' | 'admin';

export type ConversationStatus = 'safe' | 'needs_review' | 'violation' | 'evaluating';

// RAG source from backend
export interface RagSource {
  doc: string;
  page: number;
  score: number;
}

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
  ragSources?: RagSource[];  // Citations from RAG
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

// Full backend response interface
export interface BackendResponse {
  success: boolean;
  ai_response: string;
  bot_model: string;
  metrics: {
    overall_ethical_score: number;
    s_llm_score: number;
    risk_band: string;
    final_label: string;
    l1_pass_rate: number;
    l1_pass_count: number;
    layer2_risk_score: number;
    failed_dimensions: string[];
    highest_risk_dim: [string, number];
    spd: number;
    di: number;
    eop: number;
    aod: number;
    psi: number;
    ks: number;
    accuracy: number;
    recall: number;
    lawfulness: number;
  };
  tokens: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    latency_ms: number;
  };
  grounding: {
    score: number;
    hallucination_rate: number;
    l1_citation_coverage: number;
    l2_cosine_similarity: number;
    l3_support_ratio: number;
  };
  ethics: {
    l1_pass_rate: number;
    layer2_risk_score: number;
    required_action: string;
  };
  dimensions: {
    [key: string]: {
      name: string;
      weight: number;
      l1_status: string;
      l2_risk: number;
      overall_score: number;
      raw_metrics?: Record<string, unknown>;
    };
  };
  rag_sources: RagSource[];
  timestamp?: string;
}
