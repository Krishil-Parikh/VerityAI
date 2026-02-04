import { NextResponse } from 'next/server';
import { getTelemetryData } from '../../admin/graphs/lib/data';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const indexParam = searchParams.get('index');
    const index = indexParam ? parseInt(indexParam, 10) : 0;

    const allData = await getTelemetryData();

    if (index >= 0 && index < allData.length) {
        return NextResponse.json(allData[index]);
    } else {
        // Return null or specific status if out of bounds
        return NextResponse.json(null, { status: 404 });
    }
}
