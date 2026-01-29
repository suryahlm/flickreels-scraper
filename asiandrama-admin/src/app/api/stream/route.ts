/**
 * FlickReels HLS Stream API
 * 
 * Fetches fresh HLS URLs from FlickReels API on-demand.
 * 
 * Usage: GET /api/stream?drama_id=1007&episode=1
 */

import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

// FlickReels API Configuration
const FLICKREELS_CONFIG = {
    base_url: "https://api.farsunpteltd.com",
    secret_key: "tsM5SnqFayhX7c2HfRxm",
    token: process.env.FLICKREELS_TOKEN || "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU",
    version: "2.2.3.0",
    user_agent: "MyUserAgent"
};

const DEFAULT_DEVICE_PARAMS = {
    main_package_id: 100,
    googleAdId: "",
    device_id: "0d209b4d4009b44c",
    device_sign: "3af3b323830984d797d4d623af999126f3ec0d3071f69532c2c4a27b67b89e74",
    apps_flyer_uid: "1769621528308-5741215934785896746",
    os: "android",
    device_brand: "samsung",
    device_number: "9",
    device_model: "SM-X710N",
    language_id: "6",
    countryCode: "ID"
};

function generateNonce(length: number = 32): string {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function methodD(body: Record<string, any>): string {
    // Sort keys and create underscore-separated string
    const sortedKeys = Object.keys(body).sort();
    const parts: string[] = [];

    for (const key of sortedKeys) {
        const value = body[key];
        if (value !== null && value !== undefined) {
            let valueStr: string;
            if (typeof value === 'boolean') {
                valueStr = value ? 'true' : 'false';
            } else if (typeof value === 'object') {
                valueStr = JSON.stringify(value);
            } else {
                valueStr = String(value);
            }
            parts.push(`${key}_${valueStr}`);
        }
    }

    return parts.join('_');
}

function generateSign(body: Record<string, any>, timestamp: string, nonce: string): string {
    const strD = methodD(body);
    const strB = crypto.createHash('md5').update(strD).digest('hex');
    const message = `${strD}_${timestamp}_${nonce}_${strB}`;

    const sign = crypto
        .createHmac('sha256', FLICKREELS_CONFIG.secret_key)
        .update(message)
        .digest('hex');

    return sign;
}

async function flickreelsRequest(endpoint: string, extraBody: Record<string, any> = {}): Promise<any> {
    const body = { ...DEFAULT_DEVICE_PARAMS, ...extraBody };
    const timestamp = String(Math.floor(Date.now() / 1000));
    const nonce = generateNonce(32);
    const sign = generateSign(body, timestamp, nonce);

    const url = `${FLICKREELS_CONFIG.base_url}${endpoint}`;

    console.log(`[FlickReels] POST ${endpoint}`);

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept-Encoding': 'gzip',
            'User-Agent': FLICKREELS_CONFIG.user_agent,
            'version': FLICKREELS_CONFIG.version,
            'token': FLICKREELS_CONFIG.token,
            'sign': sign,
            'timestamp': timestamp,
            'nonce': nonce,
        },
        body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log(`[FlickReels] Response:`, data?.status_code, data?.msg);

    return data;
}

async function getEpisodeStream(dramaId: string, episodeNum: number): Promise<{
    hls_url: string;
    cover_url: string;
    duration: number;
    title: string;
} | null> {
    try {
        // Get episodes list
        console.log(`[Stream] Getting chapters for drama ${dramaId}...`);
        const chaptersData = await flickreelsRequest('/app/chapter/catalog', {
            playlet_id: parseInt(dramaId),
        });

        if (chaptersData?.status_code !== 0 || !chaptersData?.data?.list) {
            console.error('[Stream] Failed to get chapters:', chaptersData);
            return null;
        }

        const episodes = chaptersData.data.list;
        console.log(`[Stream] Found ${episodes.length} episodes`);

        // Find the episode
        const episode = episodes.find((ep: any) =>
            ep.sort === episodeNum ||
            ep.chapter_number === episodeNum ||
            ep.number === episodeNum
        );

        if (!episode) {
            console.error(`[Stream] Episode ${episodeNum} not found`);
            return null;
        }

        console.log(`[Stream] Found episode:`, episode.id || episode.chapter_id);

        // Get fresh HLS URL for this episode
        const streamData = await flickreelsRequest('/app/chapter/video', {
            chapter_id: episode.id || episode.chapter_id,
        });

        if (streamData?.status_code !== 0 || !streamData?.data) {
            console.error('[Stream] Failed to get stream URL:', streamData);
            return null;
        }

        const hlsUrl = streamData.data.filepath ||
            streamData.data.auto_filepath ||
            streamData.data.hls_url ||
            streamData.data.url;

        console.log(`[Stream] Got HLS URL: ${hlsUrl?.substring(0, 50)}...`);

        return {
            hls_url: hlsUrl,
            cover_url: episode.snapshot_url || episode.cover_url || '',
            duration: episode.duration || 0,
            title: episode.name || `Episode ${episodeNum}`
        };
    } catch (error) {
        console.error('[Stream] Error:', error);
        return null;
    }
}

// CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const dramaId = searchParams.get('drama_id');
    const episodeNum = parseInt(searchParams.get('episode') || '1');

    if (!dramaId) {
        return NextResponse.json(
            { error: 'drama_id is required' },
            { status: 400, headers: corsHeaders }
        );
    }

    try {
        console.log(`[API] Stream request: drama=${dramaId}, episode=${episodeNum}`);

        const streamData = await getEpisodeStream(dramaId, episodeNum);

        if (!streamData || !streamData.hls_url) {
            return NextResponse.json(
                { error: 'Failed to get stream URL' },
                { status: 404, headers: corsHeaders }
            );
        }

        return NextResponse.json({
            success: true,
            data: streamData
        }, { headers: corsHeaders });

    } catch (error) {
        console.error('[API] Stream error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
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
