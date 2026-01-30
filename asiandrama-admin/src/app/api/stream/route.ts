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
    googleAdId: "783978b6-0d30-438d-a58d-faf171eed978",
    device_id: "0d209b4d4009b44c",
    device_sign: "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    apps_flyer_uid: "1769621528308-5741215934785896746",
    os: "android",
    device_brand: "samsung",
    device_number: "9",
    device_model: "SM-X710N",
    language_id: "6", // 6 = Indonesian (ID), 1 = English
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

/**
 * Port of Python _method_d function
 * Converts body dict to sorted key_value string
 */
function methodD(body: Record<string, any>): string {
    if (!body || Object.keys(body).length === 0) {
        return "";
    }

    // Sort keys alphabetically
    const sortedKeys = Object.keys(body).sort();
    const parts: string[] = [];

    for (const key of sortedKeys) {
        const value = body[key];
        if (value !== null && value !== undefined) {
            let valueStr: string;
            if (typeof value === 'boolean') {
                // Java uses lowercase true/false
                valueStr = value ? 'true' : 'false';
            } else if (typeof value === 'object') {
                // Nested objects as JSON
                valueStr = JSON.stringify(value);
            } else {
                valueStr = String(value);
            }
            parts.push(`${key}_${valueStr}`);
        }
    }

    return parts.join('_');
}

/**
 * Generate sign for FlickReels API
 * Algorithm from APK class sb.b method f:
 * sign = HmacSHA256(d(body) + "_" + timestamp + "_" + nonce + "_" + md5(d(body)), secret_key)
 */
function generateSign(body: Record<string, any>, timestamp: string, nonce: string): string {
    // Method d: process body to sorted string
    const strD = methodD(body);

    // Method b: MD5 hash of d(body)
    const strB = crypto.createHash('md5').update(strD).digest('hex');

    // Build message: d(body) + "_" + timestamp + "_" + nonce + "_" + md5(d(body))
    const message = `${strD}_${timestamp}_${nonce}_${strB}`;

    // Generate HMAC-SHA256
    const sign = crypto
        .createHmac('sha256', FLICKREELS_CONFIG.secret_key)
        .update(message)
        .digest('hex');

    return sign;
}

async function flickreelsRequest(endpoint: string, extraBody: Record<string, any> = {}, languageId: string = '6'): Promise<any> {
    // IMPORTANT: language_id must be set LAST to override any value from DEFAULT_DEVICE_PARAMS
    const body = { ...DEFAULT_DEVICE_PARAMS, ...extraBody, language_id: languageId };
    const timestamp = String(Math.floor(Date.now() / 1000));
    const nonce = generateNonce(32);
    const sign = generateSign(body, timestamp, nonce);

    const url = `${FLICKREELS_CONFIG.base_url}${endpoint}`;

    console.log(`[FlickReels] POST ${endpoint}, language_id=${languageId}`);

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept-Encoding': 'gzip',
            'User-Agent': FLICKREELS_CONFIG.user_agent,
            'Cache-Control': 'no-cache',
            'version': FLICKREELS_CONFIG.version,
            'token': FLICKREELS_CONFIG.token,
            'sign': sign,
            'timestamp': timestamp,
            'nonce': nonce,
        },
        body: JSON.stringify(body),
    });

    const responseText = await response.text();

    try {
        const data = JSON.parse(responseText);
        console.log(`[FlickReels] Response:`, data?.status_code, data?.msg);
        return data;
    } catch {
        console.log(`[FlickReels] Failed to parse response:`, responseText.substring(0, 200));
        return { status_code: -1, msg: 'Invalid JSON response' };
    }
}

async function getEpisodeStream(dramaId: string, episodeNum: number, languageId: string = '6'): Promise<{
    hls_url: string;
    cover_url: string;
    duration: number;
    title: string;
} | null> {
    try {
        // Get episodes list using correct endpoint
        console.log(`[Stream] Getting episodes for drama ${dramaId}, lang=${languageId}...`);
        const chaptersData = await flickreelsRequest('/app/playlet/chapterList', {
            playlet_id: String(dramaId),
            chapter_type: -1,
            auto_unlock: false,
            fragmentPosition: 0,
            show_type: 0,
            source: 1,
            vip_btn_scene: '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        }, languageId);

        if (chaptersData?.status_code !== 1 || !chaptersData?.data) {
            console.error('[Stream] Failed to get chapters:', chaptersData);
            return null;
        }

        const episodes = chaptersData.data.list || chaptersData.data || [];
        console.log(`[Stream] Found ${episodes.length} episodes`);

        // Find the episode by number
        const episode = episodes.find((ep: any) =>
            ep.chapter_num === episodeNum ||
            ep.chapter_number === episodeNum
        );

        if (!episode) {
            console.error(`[Stream] Episode ${episodeNum} not found`);
            return null;
        }

        const chapterId = episode.chapter_id;
        console.log(`[Stream] Found episode:`, chapterId);

        // Get stream URL using correct endpoint
        const streamData = await flickreelsRequest('/app/playlet/play', {
            playlet_id: String(dramaId),
            chapter_id: String(chapterId),
            chapter_type: 0,
            auto_unlock: false,
            fragmentPosition: 0,
            show_type: 0,
            source: 1,
            vip_btn_scene: '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        }, languageId);

        if (streamData?.status_code !== 1 || !streamData?.data) {
            console.error('[Stream] Failed to get stream URL:', streamData);
            return null;
        }

        const hlsUrl = streamData.data.hls_url || streamData.data.hls;

        if (!hlsUrl) {
            console.error('[Stream] No HLS URL in response');
            return null;
        }

        console.log(`[Stream] Got HLS URL: ${hlsUrl.substring(0, 60)}...`);

        return {
            hls_url: hlsUrl,
            cover_url: episode.chapter_cover || episode.cover_url || '',
            duration: episode.chapter_duration || episode.duration || 0,
            title: episode.chapter_title || episode.title || `Episode ${episodeNum}`
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
    const languageId = searchParams.get('language_id') || '6'; // Default: Indonesian (6)

    if (!dramaId) {
        return NextResponse.json(
            { error: 'drama_id is required' },
            { status: 400, headers: corsHeaders }
        );
    }

    try {
        console.log(`[API] Stream request: drama=${dramaId}, episode=${episodeNum}, lang=${languageId}`);

        const streamData = await getEpisodeStream(dramaId, episodeNum, languageId);

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
