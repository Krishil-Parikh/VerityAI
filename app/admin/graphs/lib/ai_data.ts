export interface AiMetricsResponse {
    success: boolean;
    ai_response: string;
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
        };
    };
    rag_sources: {
        doc: string;
        page: number;
        score: number;
    }[];
    timestamp: string; // Added for graphing purposes
}

const BASE_RESPONSE = {
    success: true,
    ai_response: "Mock response...",
    metrics: {
        overall_ethical_score: 70,
        s_llm_score: 0.7605,
        risk_band: "MEDIUM",
        final_label: "CONDITIONALLY_ETHICAL",
        l1_pass_rate: 0.8889,
        l1_pass_count: 8,
        layer2_risk_score: 0.2395,
        failed_dimensions: ["Explainability & Transparency"],
        highest_risk_dim: ["Explainability & Transparency", 1] as [string, number],
        spd: 0,
        di: 1,
        eop: 0,
        aod: 0,
        psi: 0,
        ks: 0,
        accuracy: 1,
        recall: 1,
        lawfulness: 1
    },
    tokens: {
        input_tokens: 638,
        output_tokens: 146,
        total_tokens: 784,
        latency_ms: 3709
    },
    grounding: {
        score: 0.588,
        hallucination_rate: 0.412,
        l1_citation_coverage: 1,
        l2_cosine_similarity: 0.627,
        l3_support_ratio: 0
    },
    ethics: {
        l1_pass_rate: 0.889,
        layer2_risk_score: 0.240,
        required_action: "REVIEW_FAILED_DIMS"
    },
    dimensions: {
        legal: { name: "Legal Compliance", weight: 0.2, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        fairness: { name: "Bias & Fairness", weight: 0.2, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        explainability: { name: "Explainability & Transparency", weight: 0.16, l1_status: "FAIL", l2_risk: 1, overall_score: 0 },
        security: { name: "Security & Robustness", weight: 0.16, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        monitoring: { name: "Monitoring & Compliance", weight: 0.16, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        performance: { name: "Model Performance", weight: 0.12, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        ux: { name: "Human-AI UX", weight: 0.12, l1_status: "PASS", l2_risk: 0.329, overall_score: 67.1 },
        drift: { name: "Data & Model Drift", weight: 0.08, l1_status: "PASS", l2_risk: 0, overall_score: 100 },
        environmental: { name: "Environmental & Cost", weight: 0.04, l1_status: "PASS", l2_risk: 1, overall_score: 0 }
    },
    rag_sources: [
        { doc: "MainReport_1_0.pdf", page: 63, score: 0.7752 },
        { doc: "MainReport_1_0.pdf", page: 53, score: 0.7085 },
        { doc: "MainReport_1_0.pdf", page: 65, score: 0.7038 },
    ]
};

export function generateMockAiMetric(): AiMetricsResponse {
    const variation = (base: number, range: number) => {
        return base + (Math.random() * range * 2 - range);
    };

    const clamp = (val: number, min: number, max: number) => Math.min(Math.max(val, min), max);

    // Generate deeper random data structure
    const metrics = { ...BASE_RESPONSE.metrics };
    metrics.overall_ethical_score = clamp(variation(70, 15), 0, 100);
    metrics.s_llm_score = clamp(variation(0.76, 0.1), 0, 1);

    const tokens = { ...BASE_RESPONSE.tokens };
    tokens.input_tokens = Math.floor(variation(638, 100));
    tokens.output_tokens = Math.floor(variation(146, 50));
    tokens.total_tokens = tokens.input_tokens + tokens.output_tokens;
    tokens.latency_ms = Math.floor(variation(3700, 500));

    const dimensions = { ...BASE_RESPONSE.dimensions };
    // Randomize dimension scores somewhat around their baselines
    for (const key of Object.keys(dimensions)) {
        const typedKey = key as keyof typeof dimensions;
        const dim = { ...dimensions[typedKey] };
        // More variation for non-100 scores
        const range = dim.overall_score === 100 ? 5 : 20;
        dim.overall_score = clamp(variation(dim.overall_score, range), 0, 100);
        dimensions[typedKey] = dim;
    }

    // Randomize RAG sources slightly
    const rag_sources = BASE_RESPONSE.rag_sources.map(s => ({
        ...s,
        score: clamp(variation(s.score, 0.05), 0, 1)
    }));


    return {
        ...BASE_RESPONSE,
        metrics,
        tokens,
        dimensions,
        rag_sources,
        timestamp: new Date().toLocaleTimeString()
    };
}
