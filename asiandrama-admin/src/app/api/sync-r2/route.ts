import { GetObjectCommand, ListObjectsV2Command, S3Client } from '@aws-sdk/client-s3';
import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// R2 Configuration
const R2_CONFIG = {
    accountId: process.env.R2_ACCOUNT_ID || 'caa84fe6b1be065cda3836f0dac4b509',
    accessKeyId: process.env.R2_ACCESS_KEY_ID || 'a4903ea93c248388b6e295d6cdbc8617',
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    bucketName: process.env.R2_BUCKET_NAME || 'asiandrama-cdn',
};

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

function getSupabaseClient() {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

    if (!url || !key) {
        console.error('[Sync R2] Missing Supabase environment variables');
        throw new Error('Supabase not configured');
    }

    return createClient(url, key);
}

export async function OPTIONS() {
    return NextResponse.json({}, { headers: corsHeaders });
}

export async function POST() {
    try {
        console.log('[Sync R2] Starting sync from R2 to Supabase...');

        const s3 = getS3Client();
        const supabase = getSupabaseClient();

        // Get base URL for cover images
        const baseUrl = process.env.RAILWAY_PUBLIC_DOMAIN
            ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
            : 'https://tender-connection-production-246f.up.railway.app';

        // Get existing dramas from Supabase by title (continue even if fails)
        let existingTitles = new Set<string>();
        try {
            const { data: existingDramas, error: fetchError } = await supabase
                .from('dramas')
                .select('title');

            if (!fetchError && existingDramas) {
                existingTitles = new Set(existingDramas.map(d => d.title?.toLowerCase()));
                console.log(`[Sync R2] Found ${existingTitles.size} existing dramas in Supabase`);
            } else {
                console.warn('[Sync R2] Could not fetch existing dramas, will try to insert all');
            }
        } catch (err) {
            console.warn('[Sync R2] Error fetching existing dramas:', err);
        }

        // List all R2 folders
        const listCommand = new ListObjectsV2Command({
            Bucket: R2_CONFIG.bucketName,
            Prefix: 'flickreels/',
            Delimiter: '/',
        });

        const listResult = await s3.send(listCommand);
        const folders = listResult.CommonPrefixes || [];
        console.log(`[Sync R2] Found ${folders.length} folders in R2`);

        let synced = 0;
        let skipped = 0;
        let failed = 0;
        const syncedDramas: string[] = [];

        // Process each folder
        for (const folder of folders) {
            if (!folder.Prefix) continue;

            const folderName = folder.Prefix.replace('flickreels/', '').replace('/', '');
            if (!folderName || folderName === 'test' || folderName === 'dramas') continue;

            // Extract title from folder name (format: "Title (ID)")
            const folderTitle = folderName.split('(')[0].trim();

            try {
                // Read metadata
                const metaCommand = new GetObjectCommand({
                    Bucket: R2_CONFIG.bucketName,
                    Key: `flickreels/${folderName}/metadata.json`,
                });

                const metaResult = await s3.send(metaCommand);
                const metaText = await metaResult.Body?.transformToString();

                if (!metaText) {
                    failed++;
                    continue;
                }

                const metadata = JSON.parse(metaText);

                // Count episodes in R2
                let episodeCount = 0;
                try {
                    const epCommand = new ListObjectsV2Command({
                        Bucket: R2_CONFIG.bucketName,
                        Prefix: `flickreels/${folderName}/ep_`,
                        MaxKeys: 200,
                    });
                    const epResult = await s3.send(epCommand);
                    episodeCount = (epResult.Contents || []).filter(o => o.Key?.endsWith('.m3u8')).length;
                } catch {
                    episodeCount = metadata.total_episodes || metadata.chapter_total || 0;
                }

                if (episodeCount === 0) {
                    episodeCount = metadata.total_episodes || metadata.chapter_total || 0;
                }

                // Prepare drama data (matching actual Supabase schema)
                const title = metadata.title || folderTitle;

                // Skip if title already exists
                if (existingTitles.has(title.toLowerCase())) {
                    skipped++;
                    continue;
                }

                const dramaData = {
                    title: title,
                    synopsis: metadata.synopsis || '',
                    thumbnail_url: `${baseUrl}/api/stream/flickreels/${encodeURIComponent(folderName)}/cover.jpg`,
                    total_episodes: episodeCount,
                    view_count: 0,
                    is_published: true, // Auto-publish
                };

                // Insert to Supabase
                const { error: insertError } = await supabase
                    .from('dramas')
                    .insert(dramaData);

                if (insertError) {
                    console.error(`[Sync R2] Failed to insert ${title}:`, insertError);
                    failed++;
                } else {
                    console.log(`[Sync R2] Synced: ${title} (${episodeCount} eps)`);
                    synced++;
                    syncedDramas.push(title);
                }
            } catch (err) {
                console.error(`[Sync R2] Error processing ${folderName}:`, err);
                failed++;
            }
        }

        console.log(`[Sync R2] Complete: synced=${synced}, skipped=${skipped}, failed=${failed}`);

        return NextResponse.json({
            success: true,
            synced,
            skipped,
            failed,
            total: existingTitles.size + synced,
            syncedDramas,
        }, { headers: corsHeaders });

    } catch (error) {
        console.error('[Sync R2] Error:', error);
        return NextResponse.json({
            error: 'Sync failed',
            details: String(error)
        }, { status: 500, headers: corsHeaders });
    }
}

export async function GET() {
    return NextResponse.json({
        message: 'Use POST to trigger R2 to Supabase sync',
        description: 'This endpoint syncs all dramas from R2 storage to Supabase database'
    }, { headers: corsHeaders });
}
