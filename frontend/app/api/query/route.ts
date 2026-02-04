import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        
        const response = await fetch(`${BACKEND_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_query: body.user_query,
                bot_model: body.bot_model || 'llama3'
            }),
        });

        if (!response.ok) {
            const error = await response.text();
            return NextResponse.json(
                { error: `Backend error: ${error}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Query API error:', error);
        return NextResponse.json(
            { error: 'Failed to connect to backend' },
            { status: 500 }
        );
    }
}
