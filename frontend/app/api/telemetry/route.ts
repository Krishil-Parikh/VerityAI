import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const mode = searchParams.get('mode') || 'latest';
    const limit = searchParams.get('limit') || '100';

    try {
        // Determine which endpoint to call
        const endpoint = mode === 'history' ? `/history?limit=${limit}` : '/latest';
        
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            cache: 'no-store'
        });

        if (!response.ok) {
            return NextResponse.json({
                status: 'waiting',
                message: 'Backend not ready'
            });
        }

        const data = await response.json();
        
        // For history mode, return the array directly
        if (mode === 'history') {
            return NextResponse.json(data);
        }
        
        // For latest mode, check if we have data
        if (data.error || data.status === 'waiting') {
            return NextResponse.json({
                status: 'waiting',
                message: 'No responses yet. Send a query from the citizen portal first.'
            });
        }

        return NextResponse.json(data);
    } catch (error) {
        console.error('Telemetry API error:', error);
        return NextResponse.json({
            status: 'waiting',
            message: 'Waiting for backend connection...'
        });
    }
}

