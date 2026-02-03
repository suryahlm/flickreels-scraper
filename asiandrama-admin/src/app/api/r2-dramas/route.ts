/**
 * R2 Self-Hosted Dramas API
 * 
 * Lists all published dramas from Supabase + R2 bucket.
 * Priority: Supabase (Admin Portal managed) > R2 folder-based
 * 
 * Usage: GET /api/r2-dramas
 */

import { S3Client } from '@aws-sdk/client-s3';
import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

// R2 configuration
const R2_CONFIG = {
    accountId: process.env.R2_ACCOUNT_ID || '',
    accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
    bucketName: process.env.R2_BUCKET_NAME || 'asiandrama-cdn',
};

// Supabase configuration
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

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

// Create Supabase client
function getSupabaseClient() {
    return createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
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

        const dramas: any[] = [];
        const seenIds = new Set<string>();

        // Get base URL
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ||
            process.env.RAILWAY_PUBLIC_DOMAIN
            ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
            : 'https://tender-connection-production-246f.up.railway.app';

        // 1. FIRST: Fetch published dramas from Supabase (Admin Portal managed)
        console.log('[R2 Dramas] Fetching published dramas from Supabase...');
        try {
            const supabase = getSupabaseClient();
            const { data: supabaseDramas, error } = await supabase
                .from('dramas')
                .select('*')
                .eq('is_published', true);

            if (error) {
                console.error('[R2 Dramas] Supabase error:', error);
            } else if (supabaseDramas && supabaseDramas.length > 0) {
                console.log(`[R2 Dramas] Found ${supabaseDramas.length} published dramas in Supabase`);

                for (const d of supabaseDramas) {
                    const dramaId = d.flickreels_id || d.id?.toString();
                    seenIds.add(dramaId);

                    // Use thumbnail_url from Supabase if available, otherwise construct from r2_folder
                    const coverUrl = d.thumbnail_url || d.cover_url ||
                        (d.r2_folder ? `${baseUrl}/api/stream/flickreels/${encodeURIComponent(d.r2_folder)}/cover.jpg` : null);

                    dramas.push({
                        id: dramaId,
                        title: d.title,
                        synopsis: d.synopsis || '',
                        cover_url: coverUrl,
                        thumbnail_url: coverUrl,
                        total_episodes: d.total_episodes || 0,
                        language_id: 6,
                        folder_name: d.r2_folder || dramaId,
                        source: 'supabase',
                    });
                }
            }
        } catch (err) {
            console.error('[R2 Dramas] Supabase fetch failed:', err);
        }

        // NOTE: R2 folder scanning is DISABLED
        // All drama visibility is now controlled via Admin Portal (Supabase)
        // To show a drama in the app:
        //   1. Make sure it exists in Supabase 'dramas' table
        //   2. Set is_published = true
        // 
        // R2 is still used for video storage, but NOT for drama discovery
        console.log(`[R2 Dramas] Total: ${dramas.length} dramas (Supabase only - Admin Portal controlled)`);

        // Update cache
        cachedDramas = { dramas, count: dramas.length, source: 'supabase-only' };
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
