import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { NextRequest, NextResponse } from 'next/server';

// R2 Client configuration
const R2 = new S3Client({
    region: 'auto',
    endpoint: `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
    },
});

const BUCKET_NAME = process.env.R2_BUCKET_NAME || 'flickreels';

// Get content type based on file extension
function getContentType(path: string): string {
    if (path.endsWith('.m3u8')) return 'application/vnd.apple.mpegurl';
    if (path.endsWith('.ts')) return 'video/mp2t';
    if (path.endsWith('.jpg') || path.endsWith('.jpeg')) return 'image/jpeg';
    if (path.endsWith('.png')) return 'image/png';
    if (path.endsWith('.webp')) return 'image/webp';
    if (path.endsWith('.json')) return 'application/json';
    return 'application/octet-stream';
}

// GET /api/stream/[...path] - Stream files from R2 with clean URLs
// Example: /api/stream/dramas/Tak%20Bisa%20Melepasmu%20(2858)/ep_001.m3u8
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    try {
        const resolvedParams = await params;
        const pathSegments = resolvedParams.path;

        if (!pathSegments || pathSegments.length === 0) {
            return NextResponse.json({ error: 'Path is required' }, { status: 400 });
        }

        // Join path segments back together
        const path = pathSegments.join('/');
        console.log(`[Stream API] Fetching: ${path}`);

        // Fetch from R2
        const command = new GetObjectCommand({
            Bucket: BUCKET_NAME,
            Key: path,
        });

        const response = await R2.send(command);

        if (!response.Body) {
            return NextResponse.json({ error: 'File not found' }, { status: 404 });
        }

        // Convert stream to buffer
        const chunks: Uint8Array[] = [];
        const reader = response.Body.transformToWebStream().getReader();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
        }

        let buffer = Buffer.concat(chunks);
        const contentType = getContentType(path);

        // For m3u8 files: rewrite relative paths to absolute URLs
        if (path.endsWith('.m3u8')) {
            let content = buffer.toString('utf-8');

            // CRITICAL: Normalize line endings to LF only (Android ExoPlayer requires this)
            content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

            // Get base path (directory of the m3u8 file)
            const basePath = path.substring(0, path.lastIndexOf('/') + 1);

            // Get the base URL for the API - use Railway domain or request host
            const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
            const host = request.headers.get('host');
            const protocol = request.headers.get('x-forwarded-proto') || 'https';
            const baseUrl = railwayDomain
                ? `https://${railwayDomain}`
                : `${protocol}://${host}`;

            // Rewrite .ts segment references to absolute URLs using the new clean path format
            const lines = content.split('\n');
            const rewrittenLines = lines.map(line => {
                const trimmed = line.trim();
                // If line ends with .ts and doesn't start with #, it's a segment file
                if (trimmed.endsWith('.ts') && !trimmed.startsWith('#')) {
                    const segmentPath = basePath + trimmed;
                    // Use clean URL format: /api/stream/path/to/file.ts
                    return `${baseUrl}/api/stream/${segmentPath}`;
                }
                return line;
            });
            content = rewrittenLines.join('\n');

            buffer = Buffer.from(content, 'utf-8');
            console.log(`[Stream API] Rewrote m3u8 with absolute URLs for: ${path}`);
        }

        console.log(`[Stream API] Success: ${path} (${buffer.length} bytes)`);

        return new NextResponse(buffer, {
            status: 200,
            headers: {
                'Content-Type': contentType,
                'Content-Length': buffer.length.toString(),
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Range',
                'Cache-Control': 'public, max-age=31536000',
            },
        });

    } catch (error: any) {
        console.error('[Stream API] Error:', error);

        if (error.name === 'NoSuchKey') {
            return NextResponse.json({ error: 'File not found' }, { status: 404 });
        }

        return NextResponse.json(
            { error: 'Failed to fetch file', details: error.message },
            { status: 500 }
        );
    }
}

// Handle OPTIONS for CORS preflight
export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
        },
    });
}
