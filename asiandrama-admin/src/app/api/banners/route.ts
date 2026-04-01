import { supabaseAdmin } from '@/lib/supabase';
import { NextRequest, NextResponse } from 'next/server';

export interface AppBanners {
    banner_1: string[];
    banner_2: string[];
    banner_3: string[];
    banner_1_links?: string[];
    banner_2_links?: string[];
    banner_3_links?: string[];
    telegram_link?: string;
}

const DEFAULT_BANNERS: AppBanners = {
    banner_1: [],
    banner_2: [],
    banner_3: [],
    banner_1_links: [],
    banner_2_links: [],
    banner_3_links: [],
    telegram_link: 'https://t.me/asiandrama_id',
};

// GET Banners
export async function GET() {
    try {
        const { data, error } = await supabaseAdmin
            .from('app_settings')
            .select('value')
            .eq('key', 'app_banners')
            .single();

        if (error || !data) {
            return NextResponse.json(DEFAULT_BANNERS);
        }

        try {
            const parsed = JSON.parse(data.value) as AppBanners;
            return NextResponse.json(parsed);
        } catch (e) {
            return NextResponse.json(DEFAULT_BANNERS);
        }
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

// POST (Save) Banners
export async function POST(request: NextRequest) {
    try {
        const body = await request.json() as AppBanners;

        // Validasi sederhana
        if (!body || typeof body !== 'object') {
            return NextResponse.json({ error: 'Payload tidak valid' }, { status: 400 });
        }

        // Pastikan masing-masing maksimal 5 URL dan ada link telegram
        const sanitizePayload: AppBanners = {
            banner_1: (body.banner_1 || []).slice(0, 5),
            banner_2: (body.banner_2 || []).slice(0, 5),
            banner_3: (body.banner_3 || []).slice(0, 5),
            banner_1_links: (body.banner_1_links || []).slice(0, 5),
            banner_2_links: (body.banner_2_links || []).slice(0, 5),
            banner_3_links: (body.banner_3_links || []).slice(0, 5),
            telegram_link: body.telegram_link || 'https://t.me/asiandrama_id',
        };

        const { error } = await supabaseAdmin
            .from('app_settings')
            .upsert({
                key: 'app_banners',
                value: JSON.stringify(sanitizePayload),
                updated_at: new Date().toISOString()
            }, { onConflict: 'key' });

        if (error) {
            console.error('[API/banners] Update error:', error);
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ success: true, banners: sanitizePayload });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}
