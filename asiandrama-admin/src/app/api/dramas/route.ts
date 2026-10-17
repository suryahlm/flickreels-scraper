import { supabaseAdmin } from '@/lib/supabase';
import { NextRequest, NextResponse } from 'next/server';

const B2_BUCKET_NAME = process.env.B2_BUCKET_NAME || 'FreeDrama-storage';
const B2_ENDPOINT = process.env.B2_ENDPOINT || process.env.B2_ENDPOINT_URL || 'https://s3.us-west-004.backblazeb2.com';
const B2_REGION = process.env.B2_REGION || 'us-west-004';
const B2_KEY_ID = process.env.B2_KEY_ID || '004cfcc407703140000000003';
const B2_APPLICATION_KEY = process.env.B2_APPLICATION_KEY || 'K004xpsbRopcRQkfHnagxMJxYkhEZYA';

async function getB2Client() {
    try {
        const { S3Client, ListObjectVersionsCommand, ListObjectsV2Command, DeleteObjectsCommand } = await import('@aws-sdk/client-s3');
        const client = new S3Client({
            region: B2_REGION,
            endpoint: B2_ENDPOINT,
            credentials: {
                accessKeyId: B2_KEY_ID,
                secretAccessKey: B2_APPLICATION_KEY,
            },
        });
        return { client, ListObjectVersionsCommand, ListObjectsV2Command, DeleteObjectsCommand };
    } catch (err) {
        console.error('[API/dramas] Error initializing B2 S3 client:', err);
        return null;
    }
}

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

// Update drama metadata or toggle publish status (server-side with service_role key)
export async function PATCH(request: NextRequest) {
    try {
        const body = await request.json();
        const {
            id,
            title,
            synopsis,
            category_id,
            cover_url,
            thumbnail_url,
            release_status,
            view_count,
            total_episodes,
            is_published,
        } = body;

        if (!id) {
            return NextResponse.json({ error: 'Drama ID required' }, { status: 400 });
        }

        const updateData: any = {
            updated_at: new Date().toISOString(),
        };

        if (title !== undefined) updateData.title = title.trim();
        if (synopsis !== undefined) updateData.synopsis = synopsis;
        if (category_id !== undefined) updateData.category_id = category_id || null;
        if (cover_url !== undefined) updateData.cover_url = cover_url;
        if (thumbnail_url !== undefined) updateData.thumbnail_url = thumbnail_url;
        if (release_status !== undefined) updateData.release_status = release_status;
        if (view_count !== undefined) updateData.view_count = Number(view_count) || 0;
        if (total_episodes !== undefined) updateData.total_episodes = Number(total_episodes) || 0;

        if (is_published !== undefined) {
            updateData.is_published = is_published;
            // Jika statusnya dipublish (termasuk dipublish ulang), perbarui created_at agar tampil paling atas di "Serial Baru"
            if (is_published) {
                updateData.created_at = new Date().toISOString();
            }
        }

        const { data, error } = await supabaseAdmin
            .from('dramas')
            .update(updateData)
            .eq('id', id)
            .select()
            .single();

        if (error) {
            console.error('[API/dramas] Update error:', error);
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

        // 1. Ambil data r2_folder dan title sebelum dihapus
        const { data: dramaTarget, error: fetchErr } = await supabaseAdmin
            .from('dramas')
            .select('id, title, r2_folder')
            .eq('id', id)
            .single();

        if (fetchErr || !dramaTarget) {
            return NextResponse.json({ error: 'Drama tidak ditemukan di database' }, { status: 404 });
        }

        let deletedCount = 0;

        // 2. Bersihkan seluruh file terkait dari Backblaze B2 jika r2_folder ada
        const rawFolder = (dramaTarget.r2_folder || '').trim();
        if (rawFolder && rawFolder.length > 3) {
            // Normalisasi prefix folder: pastikan selalu diakhiri dengan '/'
            const folderPrefix = rawFolder.endsWith('/') ? rawFolder : `${rawFolder}/`;

            // Pengaman Mutlak (Safety Lock):
            // Minimal harus ada 2 segmen (contoh: 'netshort/Nama Drama (123)/').
            // Ini mencegah folder root provider seperti 'netshort/' terhapus secara sengaja ataupun tidak sengaja!
            const segments = folderPrefix.split('/').filter(Boolean);
            if (segments.length < 2) {
                console.error(`[API/dramas] PENGAMAN AKTIF: Ditolak menghapus prefix tidak aman: "${folderPrefix}"`);
                return NextResponse.json({
                    error: `Prefix folder tidak aman untuk dihapus: "${folderPrefix}". Minimal harus berisi nama provider dan judul folder drama.`
                }, { status: 400 });
            }

            console.log(`[API/dramas] Memulai pembersihan berkas di Backblaze B2 untuk prefix: "${folderPrefix}"`);

            const b2 = await getB2Client();
            if (!b2) {
                console.error('[API/dramas] Inisialisasi Backblaze B2 S3Client gagal. Menolak menghapus database.');
                return NextResponse.json({
                    error: 'Gagal inisialisasi koneksi Backblaze B2. Penghapusan dibatalkan demi integritas data.'
                }, { status: 500 });
            }

            try {
                // Gunakan ListObjectVersionsCommand agar semua file dan delete markers terhapus PERMANEN
                let isTruncated = true;
                let keyMarker: string | undefined = undefined;
                let versionIdMarker: string | undefined = undefined;

                while (isTruncated) {
                    const listCmd: any = new b2.ListObjectVersionsCommand({
                        Bucket: B2_BUCKET_NAME,
                        Prefix: folderPrefix,
                        KeyMarker: keyMarker,
                        VersionIdMarker: versionIdMarker,
                    });

                    const listRes: any = await b2.client.send(listCmd);
                    const objectsToDelete: Array<{ Key: string; VersionId?: string }> = [];

                    if (listRes.Versions && listRes.Versions.length > 0) {
                        for (const v of listRes.Versions) {
                            if (v.Key) objectsToDelete.push({ Key: v.Key, VersionId: v.VersionId });
                        }
                    }

                    if (listRes.DeleteMarkers && listRes.DeleteMarkers.length > 0) {
                        for (const d of listRes.DeleteMarkers) {
                            if (d.Key) objectsToDelete.push({ Key: d.Key, VersionId: d.VersionId });
                        }
                    }

                    if (objectsToDelete.length > 0) {
                        // Batch delete hingga 1000 file per panggilan
                        for (let i = 0; i < objectsToDelete.length; i += 1000) {
                            const chunk = objectsToDelete.slice(i, i + 1000);
                            const deleteCmd: any = new b2.DeleteObjectsCommand({
                                Bucket: B2_BUCKET_NAME,
                                Delete: {
                                    Objects: chunk,
                                    Quiet: true,
                                }
                            });
                            await b2.client.send(deleteCmd);
                            deletedCount += chunk.length;
                        }
                    }

                    isTruncated = listRes.IsTruncated ?? false;
                    keyMarker = listRes.NextKeyMarker;
                    versionIdMarker = listRes.NextVersionIdMarker;
                }

                console.log(`[API/dramas] Berhasil menghapus permanen total ${deletedCount} berkas/versi dari Backblaze B2 ("${folderPrefix}").`);
            } catch (storageErr: any) {
                console.error(`[API/dramas] Gagal membersihkan Backblaze B2 untuk prefix "${folderPrefix}":`, storageErr);
                return NextResponse.json({
                    error: `Gagal membersihkan berkas di Backblaze B2: ${storageErr?.message || storageErr}. Data di database TIDAK dihapus.`
                }, { status: 500 });
            }
        }

        // 3. Eksekusi mati (Delete) dari Supabase Database
        const { error: dbError } = await supabaseAdmin
            .from('dramas')
            .delete()
            .eq('id', id);

        if (dbError) {
            console.error('[API/dramas] Supabase Delete error:', dbError);
            return NextResponse.json({ error: `Gagal menghapus dari database: ${dbError.message}` }, { status: 500 });
        }

        console.log(`[API/dramas] Sukses menghapus drama "${dramaTarget.title}" (ID: ${id}) dari Database & B2 (${deletedCount} berkas dihapus).`);

        return NextResponse.json({
            success: true,
            deletedB2Files: deletedCount,
            message: `Drama "${dramaTarget.title}" dan ${deletedCount} berkas di B2 berhasil dihapus permanen.`
        });
    } catch (e: any) {
        console.error('[API/dramas] Unexpected error in DELETE:', e);
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

