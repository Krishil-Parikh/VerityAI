import { NextResponse } from 'next/server';
import { 
  LAMBDA_ENDPOINT,
  ONLINE_MODELS,
  isProduction,
  ApiMode 
} from '@/lib/api-config';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

/**
 * IMPORTANT: For proper ethics calculations, ALL requests go through the appropriate backend.
 * 
 * - Offline mode: Local FastAPI backend uses Ollama for LLM inference
 * - Online mode: AWS Lambda endpoint uses OpenRouter for LLM inference
 * 
 * This ensures the rti_ethics_engine package is ALWAYS used for metric calculations.
 */

// Call local FastAPI backend (offline mode - Ollama)
async function callLocalBackend(query: string, model: string) {
    const response = await fetch(`${BACKEND_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_query: query,
            bot_model: model
        }),
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Backend error: ${error}`);
    }

    return await response.json();
}

// Call AWS Lambda endpoint (online mode)
async function callLambda(query: string, model: string) {
    // Map frontend model value to OpenRouter model ID
    const modelMapping = ONLINE_MODELS.find(m => m.value === model);
    const modelId = modelMapping?.id || model;
    
    const response = await fetch(LAMBDA_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_query: query,
            bot_model: modelId
        }),
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Lambda error: ${error}`);
    }

    const data = await response.json();
    
    // Lambda returns body as string, need to parse it
    if (typeof data.body === 'string') {
        return JSON.parse(data.body);
    }
    return data;
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const query = body.user_query;
        const model = body.bot_model || 'llama3';
        const mode: ApiMode = body.mode || (isProduction() ? 'online' : 'offline');
        
        let data;
        
        if (mode === 'online') {
            // Online mode: Use AWS Lambda endpoint
            data = await callLambda(query, model);
        } else {
            // Offline mode: Use local FastAPI backend with Ollama
            data = await callLocalBackend(query, model);
        }
        
        return NextResponse.json(data);
    } catch (error) {
        console.error('Query API error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to process query' },
            { status: 500 }
        );
    }
}

