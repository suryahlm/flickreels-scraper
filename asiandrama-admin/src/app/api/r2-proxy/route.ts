/**
 * R2 Metadata Proxy API
 * 
 * Proxies requests to Cloudflare R2 to bypass SSL issues in React Native.
 * 
 * Usage: 
 *   GET /api/r2-proxy?file=dramas.json
 *   GET /api/r2-proxy?file=dramas/1007/metadata.json
 */

import { NextRequest, NextResponse } from 'next/server';

// R2 bucket configuration
const R2_CONFIG = {
    bucket_url: process.env.R2_PUBLIC_URL || "https://pub-2f4a28c89fc84b3a82c07e5ebe6b7d73.r2.dev",
};

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Cache-Control': 's-maxage=3600, stale-while-revalidate=86400',
};

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const file = searchParams.get('file');

    if (!file) {
        return NextResponse.json(
            { error: 'file parameter is required' },
            { status: 400, headers: corsHeaders }
        );
    }

    // Construct R2 URL
    const r2Url = `${R2_CONFIG.bucket_url}/${file}`;

    console.log(`[R2 Proxy] Fetching: ${r2Url}`);

    try {
        const response = await fetch(r2Url, {
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            console.error(`[R2 Proxy] Failed: ${response.status} ${response.statusText}`);
            return NextResponse.json(
                { error: `Failed to fetch from R2: ${response.status}` },
                { status: response.status, headers: corsHeaders }
            );
        }

        // Check content type
        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('application/json')) {
            const data = await response.json();
            console.log(`[R2 Proxy] Success: JSON data fetched`);
            return NextResponse.json(data, { headers: corsHeaders });
        } else {
            // Return as text for non-JSON files
            const text = await response.text();
            console.log(`[R2 Proxy] Success: Text data fetched`);
            return new NextResponse(text, {
                headers: {
                    ...corsHeaders,
                    'Content-Type': contentType
                }
            });
        }

    } catch (error) {
        console.error('[R2 Proxy] Error:', error);
        return NextResponse.json(
            { error: 'Failed to proxy R2 request' },
            { status: 500, headers: corsHeaders }
        );
    }
}

export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: corsHeaders,
    });
}
