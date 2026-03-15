import { supabaseAdmin } from '@/lib/supabase';
import { NextRequest, NextResponse } from 'next/server';

// GET — Fetch featured dramas with drama details
export async function GET() {
    try {
        const { data, error } = await supabaseAdmin
            .from('featured_dramas')
            .select('*')
            .eq('is_active', true)
            .order('display_order', { ascending: true });

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        // Join with dramas table to get titles
        const dramaIds = (data || []).map(f => f.drama_id);
        let dramasMap: Record<string, any> = {};

        if (dramaIds.length > 0) {
            const { data: dramas } = await supabaseAdmin
                .from('dramas')
                .select('flickreels_id, title, total_episodes, r2_folder, cover_url')
                .in('flickreels_id', dramaIds);

            if (dramas) {
                dramasMap = Object.fromEntries(dramas.map(d => [d.flickreels_id, d]));
            }
        }

        const result = (data || []).map(f => ({
            ...f,
            drama: dramasMap[f.drama_id] || null,
        }));

        return NextResponse.json({ featured: result });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}

// PUT — Replace entire featured list
export async function PUT(request: NextRequest) {
    try {
        const { items } = await request.json();

        if (!Array.isArray(items)) {
            return NextResponse.json({ error: 'items must be an array' }, { status: 400 });
        }

        // Validate: max 18
        if (items.length > 18) {
            return NextResponse.json({ error: 'Maximum 18 featured dramas' }, { status: 400 });
        }

        // Delete all existing featured
        await supabaseAdmin
            .from('featured_dramas')
            .delete()
            .neq('id', '00000000-0000-0000-0000-000000000000'); // delete all

        // Insert new featured list
        if (items.length > 0) {
            const rows = items.map((dramaId: string, index: number) => ({
                drama_id: dramaId,
                display_order: index + 1,
                is_active: true,
            }));

            const { error } = await supabaseAdmin
                .from('featured_dramas')
                .insert(rows);

            if (error) {
                return NextResponse.json({ error: error.message }, { status: 500 });
            }
        }

        return NextResponse.json({ success: true, count: items.length });
    } catch (e: any) {
        return NextResponse.json({ error: e.message }, { status: 500 });
    }
}
