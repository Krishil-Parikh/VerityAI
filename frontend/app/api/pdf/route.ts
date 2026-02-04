import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const file = searchParams.get('file');
    const page = searchParams.get('page') || '1';

    if (!file) {
        return NextResponse.json({ error: 'Missing file parameter' }, { status: 400 });
    }

    // Construct the URL to the backend PDF endpoint
    // The backend will serve the PDF, and we redirect with page anchor
    const pdfUrl = `${BACKEND_URL}/pdf/${encodeURIComponent(file)}#page=${page}`;
    
    // Redirect to the backend PDF with page anchor
    return NextResponse.redirect(pdfUrl);
}
