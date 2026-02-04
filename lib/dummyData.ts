import { Conversation, Message, DepartmentProfile, AlertSettings } from '@/types';

const dimensionScoresSample = [
  { name: 'Bias & Fairness', score: 88, status: 'safe' as const },
  { name: 'Data Grounding & Drift', score: 94, status: 'safe' as const },
  { name: 'Explainability & Transparency', score: 90, status: 'safe' as const },
  { name: 'Ethical Alignment', score: 92, status: 'safe' as const },
  { name: 'Human Control', score: 85, status: 'safe' as const },
  { name: 'Legal Compliance', score: 96, status: 'safe' as const },
  { name: 'Security & Robustness', score: 83, status: 'safe' as const },
  { name: 'Response Quality', score: 89, status: 'safe' as const },
];

const metricBreakdownSample = {
  statisticalParity: 0.02,
  equalOpportunity: 0.98,
  disparateImpact: 0.97,
  f1Score: 0.93,
  taskCompletionRate: 1.0,
  lawfulnessAssessment: 'Pass',
  piiDisclosure: 0,
};

export const dummyConversations: Conversation[] = [
  {
    id: 'conv-001',
    citizenId: 'User #123',
    messages: [
      {
        id: 'msg-001',
        role: 'user',
        content:
          'Please provide the total expenditure incurred by the Department on external IT consultants during FY 2022–23, along with the names of vendors engaged.',
        timestamp: new Date(Date.now() - 3600000),
      },
      {
        id: 'msg-002',
        role: 'assistant',
        content:
          'Based on the Annual Financial Statement 2022–23 and Procurement Register, the total expenditure on external IT consultants was ₹18.6 crore during FY 2022–23. Key vendors included TechCorp Solutions (₹6.2 crore), DataFlow Systems (₹5.1 crore), and CloudInfra Partners (₹7.3 crore). Detailed breakdowns by project are available in the departmental archives.',
        timestamp: new Date(Date.now() - 3590000),
        ethicalScore: 86,
        dimensionScores: dimensionScoresSample,
        metricBreakdown: metricBreakdownSample,
      },
    ],
    overallEthicalScore: 86,
    status: 'safe',
    createdAt: new Date(Date.now() - 3600000),
    updatedAt: new Date(Date.now() - 3590000),
    dimensionScores: dimensionScoresSample,
  },
  {
    id: 'conv-002',
    citizenId: 'User #456',
    messages: [
      {
        id: 'msg-003',
        role: 'user',
        content:
          'What are the recruitment patterns and diversity metrics for the department over the last 3 years?',
        timestamp: new Date(Date.now() - 7200000),
      },
      {
        id: 'msg-004',
        role: 'assistant',
        content:
          'According to our HR records, we have recruited 342 individuals over the past 3 years. Diversity breakdown: 58% women, 42% men. SC/ST representation: 28%, OBC: 35%, General: 37%. Average retention rate: 91%. Detailed breakdowns by department and level available upon request.',
        timestamp: new Date(Date.now() - 7195000),
        ethicalScore: 92,
        dimensionScores: [
          { name: 'Bias & Fairness', score: 91, status: 'safe' },
          { name: 'Data Grounding & Drift', score: 96, status: 'safe' },
          { name: 'Explainability & Transparency', score: 93, status: 'safe' },
          { name: 'Ethical Alignment', score: 94, status: 'safe' },
          { name: 'Human Control', score: 90, status: 'safe' },
          { name: 'Legal Compliance', score: 98, status: 'safe' },
          { name: 'Security & Robustness', score: 88, status: 'safe' },
          { name: 'Response Quality', score: 92, status: 'safe' },
        ],
        metricBreakdown: metricBreakdownSample,
      },
    ],
    overallEthicalScore: 92,
    status: 'safe',
    createdAt: new Date(Date.now() - 7200000),
    updatedAt: new Date(Date.now() - 7195000),
    dimensionScores: [
      { name: 'Bias & Fairness', score: 91, status: 'safe' },
      { name: 'Data Grounding & Drift', score: 96, status: 'safe' },
      { name: 'Explainability & Transparency', score: 93, status: 'safe' },
      { name: 'Ethical Alignment', score: 94, status: 'safe' },
      { name: 'Human Control', score: 90, status: 'safe' },
      { name: 'Legal Compliance', score: 98, status: 'safe' },
      { name: 'Security & Robustness', score: 88, status: 'safe' },
      { name: 'Response Quality', score: 92, status: 'safe' },
    ],
  },
  {
    id: 'conv-003',
    citizenId: 'User #789',
    messages: [
      {
        id: 'msg-005',
        role: 'user',
        content:
          'Show me procurement decisions made by the department in the last quarter.',
        timestamp: new Date(Date.now() - 14400000),
      },
      {
        id: 'msg-006',
        role: 'assistant',
        content:
          'In Q4 FY 2022–23, we made 47 procurement decisions. The total value was ₹23.5 crore. Note: Some sensitive vendor information is redacted for security. General categories included office supplies (₹2.1 crore), IT services (₹11.2 crore), and infrastructure (₹10.2 crore).',
        timestamp: new Date(Date.now() - 14395000),
        ethicalScore: 71,
        dimensionScores: [
          { name: 'Bias & Fairness', score: 72, status: 'needs_review' },
          { name: 'Data Grounding & Drift', score: 85, status: 'safe' },
          { name: 'Explainability & Transparency', score: 68, status: 'needs_review' },
          { name: 'Ethical Alignment', score: 75, status: 'needs_review' },
          { name: 'Human Control', score: 70, status: 'needs_review' },
          { name: 'Legal Compliance', score: 78, status: 'needs_review' },
          { name: 'Security & Robustness', score: 62, status: 'needs_review' },
          { name: 'Response Quality', score: 71, status: 'needs_review' },
        ],
        metricBreakdown: metricBreakdownSample,
      },
    ],
    overallEthicalScore: 71,
    status: 'needs_review',
    createdAt: new Date(Date.now() - 14400000),
    updatedAt: new Date(Date.now() - 14395000),
    dimensionScores: [
      { name: 'Bias & Fairness', score: 72, status: 'needs_review' },
      { name: 'Data Grounding & Drift', score: 85, status: 'safe' },
      { name: 'Explainability & Transparency', score: 68, status: 'needs_review' },
      { name: 'Ethical Alignment', score: 75, status: 'needs_review' },
      { name: 'Human Control', score: 70, status: 'needs_review' },
      { name: 'Legal Compliance', score: 78, status: 'needs_review' },
      { name: 'Security & Robustness', score: 62, status: 'needs_review' },
      { name: 'Response Quality', score: 71, status: 'needs_review' },
    ],
  },
  {
    id: 'conv-004',
    citizenId: 'User #234',
    messages: [
      {
        id: 'msg-007',
        role: 'user',
        content: 'Provide internal communications regarding policy changes.',
        timestamp: new Date(Date.now() - 21600000),
      },
      {
        id: 'msg-008',
        role: 'assistant',
        content:
          'Unable to provide internal communications as they fall under confidential category per RTI Act Section 8(1)(i). However, final policy decisions and their public impact summaries are available. Recent policy change: Leave policy revision effective from April 2023.',
        timestamp: new Date(Date.now() - 21595000),
        ethicalScore: 63,
        dimensionScores: [
          { name: 'Bias & Fairness', score: 65, status: 'violation' },
          { name: 'Data Grounding & Drift', score: 72, status: 'needs_review' },
          { name: 'Explainability & Transparency', score: 59, status: 'violation' },
          { name: 'Ethical Alignment', score: 68, status: 'needs_review' },
          { name: 'Human Control', score: 60, status: 'violation' },
          { name: 'Legal Compliance', score: 85, status: 'safe' },
          { name: 'Security & Robustness', score: 55, status: 'violation' },
          { name: 'Response Quality', score: 64, status: 'violation' },
        ],
        metricBreakdown: metricBreakdownSample,
      },
    ],
    overallEthicalScore: 63,
    status: 'violation',
    createdAt: new Date(Date.now() - 21600000),
    updatedAt: new Date(Date.now() - 21595000),
    dimensionScores: [
      { name: 'Bias & Fairness', score: 65, status: 'violation' },
      { name: 'Data Grounding & Drift', score: 72, status: 'needs_review' },
      { name: 'Explainability & Transparency', score: 59, status: 'violation' },
      { name: 'Ethical Alignment', score: 68, status: 'needs_review' },
      { name: 'Human Control', score: 60, status: 'violation' },
      { name: 'Legal Compliance', score: 85, status: 'safe' },
      { name: 'Security & Robustness', score: 55, status: 'violation' },
      { name: 'Response Quality', score: 64, status: 'violation' },
    ],
  },
];

export const dummyDepartments: DepartmentProfile[] = [
  {
    id: 'dept-1',
    name: 'Finance & Expenditure',
    weights: {
      bias: 10,
      dataGrounding: 20,
      explainability: 15,
      ethicalAlignment: 12,
      humanControl: 8,
      legal: 20,
      security: 10,
      quality: 5,
    },
  },
  {
    id: 'dept-2',
    name: 'Procurement',
    weights: {
      bias: 15,
      dataGrounding: 15,
      explainability: 12,
      ethicalAlignment: 12,
      humanControl: 12,
      legal: 18,
      security: 12,
      quality: 4,
    },
  },
  {
    id: 'dept-3',
    name: 'HR & Staffing',
    weights: {
      bias: 25,
      dataGrounding: 12,
      explainability: 15,
      ethicalAlignment: 15,
      humanControl: 10,
      legal: 12,
      security: 8,
      quality: 3,
    },
  },
];

export const defaultAlertSettings: AlertSettings = {
  minEthicalScore: 70,
  redThreshold: 70,
  enableEmailAlerts: true,
  enableSlackAlerts: false,
};
