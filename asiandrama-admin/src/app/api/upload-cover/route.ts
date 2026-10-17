import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

const B2_KEY_ID = process.env.B2_KEY_ID || process.env.R2_ACCESS_KEY_ID || '004cfcc407703140000000003';
const B2_APPLICATION_KEY = process.env.B2_APPLICATION_KEY || process.env.R2_SECRET_ACCESS_KEY || 'K004xpsbRopcRQkfHnagxMJxYkhEZYA';
const B2_BUCKET_ID = process.env.B2_BUCKET_ID || 'fcaf5c5c948027f7a0130114';

interface B2AuthCache {
    apiUrl: string;
    authToken: string;
    expiresAt: number;
}

let cachedB2Auth: B2AuthCache | null = null;

async function getB2Auth(): Promise<{ apiUrl: string; authToken: string }> {
    if (cachedB2Auth && Date.now() < cachedB2Auth.expiresAt) {
        return { apiUrl: cachedB2Auth.apiUrl, authToken: cachedB2Auth.authToken };
    }

    const authHeader = 'Basic ' + Buffer.from(`${B2_KEY_ID}:${B2_APPLICATION_KEY}`).toString('base64');
    const authRes = await fetch('https://api.backblazeb2.com/b2api/v2/b2_authorize_account', {
        headers: { Authorization: authHeader },
        cache: 'no-store',
    });

    if (!authRes.ok) {
        const errorText = await authRes.text();
        throw new Error(`B2 Authorize failed [${authRes.status}]: ${errorText}`);
    }

    const authData = await authRes.json();
    cachedB2Auth = {
        apiUrl: authData.apiUrl,
        authToken: authData.authorizationToken,
        expiresAt: Date.now() + 2 * 3600 * 1000, // cache for 2 hours
    };

    return { apiUrl: cachedB2Auth.apiUrl, authToken: cachedB2Auth.authToken };
}

async function getB2UploadUrl(apiUrl: string, authToken: string, bucketId: string): Promise<{ uploadUrl: string; uploadToken: string }> {
    const res = await fetch(`${apiUrl}/b2api/v2/b2_get_upload_url`, {
        method: 'POST',
        headers: {
            Authorization: authToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ bucketId }),
        cache: 'no-store',
    });

    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`B2 get_upload_url failed [${res.status}]: ${errorText}`);
    }

    const data = await res.json();
    return { uploadUrl: data.uploadUrl, uploadToken: data.authorizationToken };
}

async function uploadSingleFile(
    uploadUrl: string,
    uploadToken: string,
    fileName: string,
    buffer: Buffer,
    contentType: string
) {
    const sha1 = crypto.createHash('sha1').update(buffer).digest('hex');
    const encodedCacheControl = encodeURIComponent('public, max-age=31536000, immutable');

    const res = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
            Authorization: uploadToken,
            'X-Bz-File-Name': encodeURI(fileName),
            'Content-Type': contentType,
            'Content-Length': buffer.length.toString(),
            'X-Bz-Content-Sha1': sha1,
            'X-Bz-Info-b2-cache-control': encodedCacheControl,
        },
        body: new Uint8Array(buffer),
    });

    if (!res.ok) {
        const errText = await res.text();
        throw new Error(`B2 upload failed for ${fileName} [${res.status}]: ${errText}`);
    }

    return await res.json();
}

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();
        const file = formData.get('file') as File | null;
        const dramaId = formData.get('dramaId') as string | null;
        const r2Folder = formData.get('r2Folder') as string | null;

        if (!file) {
            return NextResponse.json({ error: 'File gambar wajib diunggah' }, { status: 400 });
        }

        // Validate MIME type
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            return NextResponse.json(
                { error: 'Format file tidak didukung. Harap gunakan format JPG, PNG, atau WebP.' },
                { status: 400 }
            );
        }

        // Limit size to 10MB
        if (file.size > 10 * 1024 * 1024) {
            return NextResponse.json(
                { error: 'Ukuran file terlalu besar. Maksimum 10MB.' },
                { status: 400 }
            );
        }

        const arrayBuffer = await file.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);

        // Determine destination folder prefix
        let folderPrefix = '';
        if (r2Folder && r2Folder.trim().length > 2) {
            folderPrefix = r2Folder.trim().replace(/\/+$/, '');
        } else if (dramaId) {
            folderPrefix = `custom_covers/${dramaId}`;
        } else {
            folderPrefix = `custom_covers/${Date.now()}`;
        }

        // Key paths per project SOP:
        // Always upload cover.jpg for legacy app compatibility, and cover.webp
        const jpgKey = `${folderPrefix}/cover.jpg`;
        const webpKey = `${folderPrefix}/cover.webp`;

        // Authenticate with Backblaze B2
        const { apiUrl, authToken } = await getB2Auth();

        // 1. Upload cover.jpg
        const upload1 = await getB2UploadUrl(apiUrl, authToken, B2_BUCKET_ID);
        await uploadSingleFile(
            upload1.uploadUrl,
            upload1.uploadToken,
            jpgKey,
            buffer,
            'image/jpeg'
        );

        // 2. Upload cover.webp (backward & forward compatibility per SOP)
        const upload2 = await getB2UploadUrl(apiUrl, authToken, B2_BUCKET_ID);
        await uploadSingleFile(
            upload2.uploadUrl,
            upload2.uploadToken,
            webpKey,
            buffer,
            file.type === 'image/webp' ? 'image/webp' : 'image/jpeg'
        );

        const timestamp = Date.now();
        // Return stream gateway URL so all web & app clients can render it immediately
        const publicUrl = `https://api.asiandrama.cc/stream/${encodeURI(jpgKey)}?t=${timestamp}`;

        return NextResponse.json({
            success: true,
            url: publicUrl,
            key: jpgKey,
            r2Folder: folderPrefix,
        });
    } catch (error: any) {
        console.error('[API/upload-cover] Upload error:', error);
        return NextResponse.json(
            { error: error?.message || 'Gagal mengunggah cover ke Storage' },
            { status: 500 }
        );
    }
}
