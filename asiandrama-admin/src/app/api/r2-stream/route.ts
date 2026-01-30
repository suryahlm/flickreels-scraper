/**
 * R2 Stream API - Direct S3 Access
 * 
 * Serves video files directly from R2 using S3 API (bypasses SSL issues with public URL).
 * 
 * Usage:
 *   GET /api/r2-stream?path=dramas/Tak%20Bisa%20Melepasmu%20(2858)/ep_001.m3u8
 *   GET /api/r2-stream?path=dramas/Tak%20Bisa%20Melepasmu%20(2858)/ep_001_0000.ts
 */

import { NextRequest, NextResponse } from 'next/server';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';

// R2 configuration
const R2_CONFIG = {
    accountId: process.env.R2_ACCOUNT_ID || '',
    accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
    bucketName: process.env.R2_BUCKET_NAME || 'asiandrama-cdn',
};

// Content types for file extensions
const CONTENT_TYPES: { [key: string]: string } = {
    '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t',
    '.json': 'application/json',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
};

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Range',
    'Access-Control-Expose-Headers': 'Content-Length, Content-Range',
};

// Create S3 client for R2
function getS3Client() {
    return new S3Client({
        region: 'auto',
        endpoint: `https://${R2_CONFIG.accountId}.r2.cloudflarestorage.com`,
        credentials: {
            accessKeyId: R2_CONFIG.accessKeyId,
            secretAccessKey: R2_CONFIG.secretAccessKey,
        },
    });
}

function getContentType(path: string): string {
    const ext = path.substring(path.lastIndexOf('.')).toLowerCase();
    return CONTENT_TYPES[ext] || 'application/octet-stream';
}

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const path = searchParams.get('path');

    if (!path) {
        return NextResponse.json(
            { error: 'path parameter is required' },
            { status: 400, headers: corsHeaders }
        );
    }

    // Security: prevent path traversal
    if (path.includes('..')) {
        return NextResponse.json(
            { error: 'Invalid path' },
            { status: 400, headers: corsHeaders }
        );
    }

    console.log(`[R2 Stream] Fetching: ${path}`);

    try {
        const s3 = getS3Client();

        const command = new GetObjectCommand({
            Bucket: R2_CONFIG.bucketName,
            Key: path,
        });

        const response = await s3.send(command);

        if (!response.Body) {
            return NextResponse.json(
                { error: 'File not found' },
                { status: 404, headers: corsHeaders }
            );
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

            // Get base path (directory of the m3u8 file)
            const basePath = path.substring(0, path.lastIndexOf('/') + 1);

            // Get the base URL for the API - use Railway domain or request host
            const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
            const host = request.headers.get('host');
            const protocol = request.headers.get('x-forwarded-proto') || 'https';
            const baseUrl = railwayDomain
                ? `https://${railwayDomain}`
                : `${protocol}://${host}`;

            // Rewrite .ts segment references to absolute URLs
            content = content.replace(/^([^#\n][^\n]*\.ts)$/gm, (match, filename) => {
                const segmentPath = basePath + filename;
                return `${baseUrl}/api/r2-stream?path=${encodeURIComponent(segmentPath)}`;
            });

            buffer = Buffer.from(content, 'utf-8');
            console.log(`[R2 Stream] Rewrote m3u8 with absolute URLs for: ${path}`);
        }

        console.log(`[R2 Stream] Success: ${path} (${buffer.length} bytes)`);

        return new NextResponse(buffer, {
            status: 200,
            headers: {
                ...corsHeaders,
                'Content-Type': contentType,
                'Content-Length': buffer.length.toString(),
                'Cache-Control': 'public, max-age=31536000', // 1 year cache
            },
        });

    } catch (error: any) {
        console.error('[R2 Stream] Error:', error);

        if (error.name === 'NoSuchKey') {
            return NextResponse.json(
                { error: 'File not found' },
                { status: 404, headers: corsHeaders }
            );
        }

        return NextResponse.json(
            { error: 'Failed to fetch from R2' },
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
