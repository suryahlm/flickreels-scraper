/**
 * FlickReels Language Test API
 * 
 * Tests if different language_id returns different drama_ids.
 * 
 * Usage: GET /api/test-language
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
    device_id: "0d209b4d4009b44c",
    device_sign: "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    os: "android",
    device_brand: "samsung",
    device_number: "9",
    device_model: "SM-X710N",
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
    const bodyJson = JSON.stringify(body);
    if (!bodyJson || bodyJson === '{}') return '';

    const sortedEntries = Object.entries(body).sort(([a], [b]) => a.localeCompare(b));
    const parts: string[] = [];

    for (const [key, value] of sortedEntries) {
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
    const sign = crypto.createHmac('sha256', FLICKREELS_CONFIG.secret_key)
        .update(message)
        .digest('hex');
    return sign;
}

async function flickreelsRequest(endpoint: string, extraBody: Record<string, any> = {}, languageId: string = '6'): Promise<any> {
    const body = { ...DEFAULT_DEVICE_PARAMS, ...extraBody, language_id: languageId };
    const timestamp = String(Math.floor(Date.now() / 1000));
    const nonce = generateNonce(32);
    const sign = generateSign(body, timestamp, nonce);

    const url = `${FLICKREELS_CONFIG.base_url}${endpoint}`;

    console.log(`[Test] POST ${endpoint}, language_id=${languageId}`);

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

    return response.json();
}

async function getHotRankDramas(languageId: string): Promise<any[]> {
    const result = await flickreelsRequest("/app/playlet/hotRank", {
        rank_type: 0
    }, languageId);

    const dramas: any[] = [];
    if (result?.status_code === 1 && result?.data) {
        for (const rank of result.data) {
            for (const drama of rank?.data || []) {
                dramas.push({
                    playlet_id: drama.playlet_id,
                    title: drama.title,
                    chapter_total: drama.chapter_total
                });
            }
        }
    }
    return dramas;
}

export async function GET(request: NextRequest) {
    try {
        console.log("[Test] Comparing drama lists between languages...");

        // Fetch with language_id=6 (Indonesian)
        const dramasLang6 = await getHotRankDramas("6");
        console.log(`[Test] Lang 6 (ID): ${dramasLang6.length} dramas`);

        // Wait a bit
        await new Promise(r => setTimeout(r, 500));

        // Fetch with language_id=1
        const dramasLang1 = await getHotRankDramas("1");
        console.log(`[Test] Lang 1: ${dramasLang1.length} dramas`);

        // Compare
        const idsLang6 = new Set(dramasLang6.map(d => d.playlet_id));
        const idsLang1 = new Set(dramasLang1.map(d => d.playlet_id));

        const common = [...idsLang6].filter(id => idsLang1.has(id));
        const onlyIn6 = [...idsLang6].filter(id => !idsLang1.has(id));
        const onlyIn1 = [...idsLang1].filter(id => !idsLang6.has(id));

        // Build title comparison
        const titlesLang6: Record<string, string> = {};
        const titlesLang1: Record<string, string> = {};

        dramasLang6.forEach(d => titlesLang6[d.playlet_id] = d.title);
        dramasLang1.forEach(d => titlesLang1[d.playlet_id] = d.title);

        const titleDiffs = common.slice(0, 10).map(id => ({
            playlet_id: id,
            title_lang6: titlesLang6[id],
            title_lang1: titlesLang1[id],
            different: titlesLang6[id] !== titlesLang1[id]
        }));

        return NextResponse.json({
            success: true,
            hypothesis: "Different language_id returns different drama_id",
            results: {
                lang6_count: dramasLang6.length,
                lang1_count: dramasLang1.length,
                common_ids_count: common.length,
                only_in_lang6: onlyIn6.slice(0, 10),
                only_in_lang1: onlyIn1.slice(0, 10),
                title_comparisons: titleDiffs,
                conclusion: onlyIn6.length > 0 || onlyIn1.length > 0
                    ? "CONFIRMED: Different languages have different drama_ids!"
                    : "NOT confirmed: Same drama_ids for both languages"
            },
            sample_dramas_lang6: dramasLang6.slice(0, 5),
            sample_dramas_lang1: dramasLang1.slice(0, 5)
        });
    } catch (error) {
        console.error("[Test] Error:", error);
        return NextResponse.json({
            success: false,
            error: String(error)
        }, { status: 500 });
    }
}
