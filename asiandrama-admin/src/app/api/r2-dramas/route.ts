/**
 * R2 Self-Hosted Dramas API
 * 
 * Lists all dramas available in our self-hosted R2 bucket.
 * Reads the dramas.json file uploaded during the scraping process.
 * 
 * Usage: GET /api/r2-dramas
 */

import { NextResponse } from 'next/server';
import { S3Client, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';

// R2 configuration
const R2_CONFIG = {
    accountId: process.env.R2_ACCOUNT_ID || '',
    accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
    bucketName: process.env.R2_BUCKET_NAME || 'asiandrama-cdn',
};

// Cache
let cachedDramas: any = null;
let cacheTime = 0;
const CACHE_DURATION = 0; // TEMPORARILY DISABLED - set back to 60*60*1000 after drama count stabilizes

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
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

export async function GET() {
    try {
        const now = Date.now();

        // Return cached data if still valid
        if (cachedDramas && (now - cacheTime) < CACHE_DURATION) {
            return NextResponse.json(cachedDramas, {
                headers: { ...corsHeaders, 'X-Cache': 'HIT' }
            });
        }

        console.log('[R2 Dramas] Fetching drama list from R2...');

        const s3 = getS3Client();

        // List all folders in dramas/ prefix
        const listCommand = new ListObjectsV2Command({
            Bucket: R2_CONFIG.bucketName,
            Prefix: 'flickreels/',
            Delimiter: '/',
        });

        const listResult = await s3.send(listCommand);
        const folders = listResult.CommonPrefixes || [];

        console.log(`[R2 Dramas] Found ${folders.length} drama folders`);

        // For each folder, read metadata.json
        const dramas: any[] = [];

        for (const folder of folders) {
            if (!folder.Prefix) continue;

            const folderName = folder.Prefix.replace('flickreels/', '').replace('/', '');
            if (!folderName) continue;

            try {
                // Read metadata.json from folder
                const metaCommand = new GetObjectCommand({
                    Bucket: R2_CONFIG.bucketName,
                    Key: `flickreels/${folderName}/metadata.json`,
                });

                const metaResult = await s3.send(metaCommand);

                if (metaResult.Body) {
                    const bodyText = await metaResult.Body.transformToString();
                    const metadata = JSON.parse(bodyText);

                    // Get base URL (Railway deployment URL or localhost)
                    const baseUrl = process.env.NEXT_PUBLIC_API_URL ||
                        process.env.RAILWAY_PUBLIC_DOMAIN
                        ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
                        : 'https://tender-connection-production-246f.up.railway.app';

                    // Build drama object with R2 stream URLs (ABSOLUTE URLs for mobile)
                    dramas.push({
                        id: metadata.id || extractIdFromFolder(folderName),
                        title: metadata.title || folderName,
                        synopsis: metadata.synopsis || '',
                        cover_url: `${baseUrl}/api/stream/flickreels/${encodeURIComponent(folderName)}/cover.jpg`,
                        thumbnail_url: `${baseUrl}/api/stream/flickreels/${encodeURIComponent(folderName)}/cover.jpg`,
                        total_episodes: metadata.total_episodes || metadata.chapter_total || 0,
                        language_id: metadata.language_id || 6,
                        folder_name: folderName,
                    });
                }
            } catch (err) {
                console.log(`[R2 Dramas] Skipping ${folderName}: no metadata`);
            }
        }

        console.log(`[R2 Dramas] Loaded ${dramas.length} dramas with metadata`);

        // Update cache
        cachedDramas = { dramas, count: dramas.length, source: 'r2-self-hosted' };
        cacheTime = now;

        return NextResponse.json(cachedDramas, {
            headers: { ...corsHeaders, 'X-Cache': 'MISS' }
        });

    } catch (error) {
        console.error('[R2 Dramas] Error:', error);

        // Return cached if available
        if (cachedDramas) {
            return NextResponse.json(cachedDramas, {
                headers: { ...corsHeaders, 'X-Cache': 'STALE' }
            });
        }

        return NextResponse.json(
            { error: 'Failed to fetch dramas', dramas: [], count: 0 },
            { status: 500, headers: corsHeaders }
        );
    }
}

// Extract drama ID from folder name like "Tak Bisa Melepasmu (2858)"
function extractIdFromFolder(folderName: string): string {
    const match = folderName.match(/\((\d+)\)$/);
    return match ? match[1] : folderName;
}

export async function OPTIONS() {
    return new NextResponse(null, {
        status: 200,
        headers: corsHeaders,
    });
}
