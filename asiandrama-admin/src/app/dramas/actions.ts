'use server';

import { supabaseAdmin, type Drama, type Category } from '@/lib/supabase';

export async function fetchDramasCatalogAdmin() {
    try {
        const [dramasRes, catsRes] = await Promise.all([
            supabaseAdmin
                .from('dramas')
                .select('id, title, r2_folder, category_id, total_episodes, view_count, is_published, release_status, created_at, cover_url, thumbnail_url')
                .order('created_at', { ascending: false }),
            supabaseAdmin.from('categories').select('id, name, slug, display_order').order('display_order'),
        ]);

        return {
            success: true,
            dramas: (dramasRes.data || []) as unknown as Drama[],
            categories: (catsRes.data || []) as Category[],
            error: dramasRes.error?.message || catsRes.error?.message || null,
        };
    } catch (err: any) {
        return {
            success: false,
            dramas: [],
            categories: [],
            error: err.message,
        };
    }
}
