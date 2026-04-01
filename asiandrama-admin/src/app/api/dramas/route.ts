import { supabaseAdmin } from '@/lib/supabase';
import { NextRequest, NextResponse } from 'next/server';
import { S3Client, ListObjectsV2Command, DeleteObjectsCommand } from '@aws-sdk/client-s3';

// Setup Cloudflare R2 Client
const r2Client = new S3Client({
    region: 'auto',
    endpoint: `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY || '',
    },
});
const BUCKET_NAME = process.env.R2_BUCKET_NAME || 'asiandrama-cdn';

// R2 Public URL
const R2_URL = 'https://pub-7e9668fd996e4d5f81b00057db79402f.r2.dev/flickreels/dramas.json';

// Cache drama data in memory (refreshed every 5 minutes)
let cachedData: any = null;
let cacheTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export async function GET() {
    try {
        const now = Date.now();

        // Return cached data if still valid
        if (cachedData && (now - cacheTime) < CACHE_DURATION) {
            return NextResponse.json(cachedData, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=300',
                    'X-Cache': 'HIT'
                }
            });
        }

        // Fetch fresh data from R2
        console.log('[API/dramas] Fetching fresh data from R2...');

        const response = await fetch(R2_URL, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            // @ts-ignore - Next.js fetch option
            next: { revalidate: 300 }
        });

        if (!response.ok) {
            throw new Error(`R2 fetch failed: ${response.status}`);
        }

        const data = await response.json();

        // Update cache
        cachedData = data;
        cacheTime = now;

        console.log(`[API/dramas] Loaded ${Object.keys(data).length} dramas from R2`);

        return NextResponse.json(data, {
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=300',
                'X-Cache': 'MISS'
            }
        });

    } catch (error) {
        console.error('[API/dramas] Error:', error);

        // Return cached data if available, even if stale
        if (cachedData) {
            return NextResponse.json(cachedData, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'X-Cache': 'STALE'
                }
            });
        }

        return NextResponse.json(
            { error: 'Failed to fetch dramas', message: String(error) },
            { status: 500 }
        );
    }
}

// Toggle publish status (server-side with service_role key)
export async function PATCH(request: NextRequest) {
    try {
        const { id, is_published } = await request.json();

        if (!id) {
            return NextResponse.json({ error: 'Drama ID required' }, { status: 400 });
        }

        const { data, error } = await supabaseAdmin
            .from('dramas')
            .update({ is_published })
            .eq('id', id)
            .select()
            .single();

        if (error) {
            console.error('[API/dramas] Toggle publish error:', error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true, drama: data });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}

// Delete drama (server-side with service_role key)
export async function DELETE(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id');

        if (!id) {
            return NextResponse.json({ error: 'Drama ID required' }, { status: 400 });
        }

        // 1. Ambil data r2_folder sebelum dihapus
        const { data: dramaTarget } = await supabaseAdmin
            .from('dramas')
            .select('title, r2_folder')
            .eq('id', id)
            .single();

        if (!dramaTarget) {
            return NextResponse.json({ error: 'Drama tidak ditemukan' }, { status: 404 });
        }

        // 2. Jika punya r2_folder yang valid, hapus semua file terkait dari R2 CDN
        if (dramaTarget.r2_folder && dramaTarget.r2_folder.length > 3) {
            let isTruncated = true;
            let continuationToken: string | undefined = undefined;
            const folderPrefix = dramaTarget.r2_folder.endsWith('/') 
                ? dramaTarget.r2_folder 
                : `${dramaTarget.r2_folder}/`;

            console.log(`[API/dramas] Mulai membersihkan R2 Bucket untuk folder: ${folderPrefix}`);
            let deletedCount = 0;

            try {
                // Loop untuk paginasi (jika file > 1000)
                while (isTruncated) {
                    const listCmd: any = new ListObjectsV2Command({
                        Bucket: BUCKET_NAME,
                        Prefix: folderPrefix,
                        ContinuationToken: continuationToken,
                    });
                    
                    const listRes: any = await r2Client.send(listCmd);
                    const objects = listRes.Contents;

                    if (objects && objects.length > 0) {
                        const deleteCmd: any = new DeleteObjectsCommand({
                            Bucket: BUCKET_NAME,
                            Delete: {
                                Objects: objects.map((obj: any) => ({ Key: obj.Key })),
                                Quiet: true, // Tidak perlu mengembalikan data file persatu-persatu
                            }
                        });
                        
                        await r2Client.send(deleteCmd);
                        deletedCount += objects.length;
                    }
                    
                    isTruncated = listRes.IsTruncated ?? false;
                    continuationToken = listRes.NextContinuationToken;
                }
                console.log(`[API/dramas] Berhasil menghapus total ${deletedCount} file dari CDN R2.`);
            } catch (r2Error) {
                console.error('[API/dramas] Gagal membersihkan Cloudflare R2:', r2Error);
                // Kita TIDAK me-return error di sini, biarkan lanjut menghapus dari DB.
            }
        }

        // 3. Eksekusi mati (Delete) dari Supabase Database (Hard Delete)
        const { error } = await supabaseAdmin
            .from('dramas')
            .delete()
            .eq('id', id);

        if (error) {
            console.error('[API/dramas] Supabase Delete error:', error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true, deletedR2Files: true });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}

// Add new drama (server-side with service_role key)
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        if (!body.title?.trim()) {
            return NextResponse.json({ error: 'Judul wajib diisi' }, { status: 400 });
        }

        const { data, error } = await supabaseAdmin
            .from('dramas')
            .insert({
                title: body.title,
                synopsis: body.synopsis || null,
                category_id: body.category_id || null,
            })
            .select()
            .single();

        if (error) {
            console.error('[API/dramas] Add error:', error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true, drama: data });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}

// Handle CORS preflight
export async function OPTIONS() {
    return new NextResponse(null, {
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PATCH, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    });
}

