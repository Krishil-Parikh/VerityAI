import { NextResponse } from 'next/server';
import { 
  OPENROUTER_CONFIG, 
  OPENROUTER_MODELS,
  isProduction,
  ApiMode 
} from '@/lib/api-config';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const LAMBDA_ENDPOINT = process.env.LAMBDA_ENDPOINT || '';

/**
 * IMPORTANT: For proper ethics calculations, ALL requests go through the backend.
 * 
 * In development:
 * - Offline mode: Backend uses Ollama for LLM inference
 * - Online mode: Backend uses OpenRouter for LLM inference (via /query-online endpoint)
 * 
 * In production:
 * - Online mode: Lambda handler uses OpenRouter + rti_ethics_engine
 * 
 * This ensures the rti_ethics_engine package is ALWAYS used for metric calculations.
 */

// Call local FastAPI backend (supports both Ollama and OpenRouter via inference_mode)
async function callLocalBackend(query: string, model: string, inferenceMode: 'ollama' | 'openrouter' = 'ollama') {
    const endpoint = inferenceMode === 'openrouter' ? '/query-online' : '/query';
    
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
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

// Call Lambda endpoint (production) - Lambda uses rti_ethics_engine
async function callLambda(query: string, model: string) {
    if (!LAMBDA_ENDPOINT) {
        throw new Error('Lambda endpoint not configured');
    }
    
    const response = await fetch(`${LAMBDA_ENDPOINT}/query`, {
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
        throw new Error(`Lambda error: ${error}`);
    }

    return await response.json();
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const query = body.user_query;
        const model = body.bot_model || 'llama3';
        const mode: ApiMode = body.mode || (isProduction() ? 'online' : 'offline');
        
        let data;
        
        if (mode === 'online') {
            // Online mode
            if (isProduction() && LAMBDA_ENDPOINT) {
                // Production: Use Lambda (which uses rti_ethics_engine)
                data = await callLambda(query, model);
            } else {
                // Development: Use local backend with OpenRouter inference
                // This ensures rti_ethics_engine is used for all calculations
                data = await callLocalBackend(query, model, 'openrouter');
            }
        } else {
            // Offline mode: Use local FastAPI backend with Ollama
            data = await callLocalBackend(query, model, 'ollama');
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
