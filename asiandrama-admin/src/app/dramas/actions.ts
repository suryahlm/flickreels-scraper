'use server';

import { supabaseAdmin, type Drama, type Category } from '@/lib/supabase';

export async function fetchDramasCatalogAdmin() {
    try {
        const [dramasRes, catsRes] = await Promise.all([
            supabaseAdmin.from('dramas').select('*').order('created_at', { ascending: false }),
            supabaseAdmin.from('categories').select('*').order('display_order'),
        ]);

        return {
            success: true,
            dramas: (dramasRes.data || []) as Drama[],
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
