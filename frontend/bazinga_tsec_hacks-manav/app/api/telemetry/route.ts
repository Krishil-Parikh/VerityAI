import { NextResponse } from 'next/server';
import { generateMockAiMetric } from '../../admin/graphs/lib/ai_data';

export async function GET(request: Request) {
    // Generate a random data point simulating a live event
    const data = generateMockAiMetric();
    return NextResponse.json(data);
}
