'use server';

import { supabaseAdmin } from '@/lib/supabase';

export async function fetchDraftDramasAdmin() {
    try {
        const { data, error } = await supabaseAdmin
            .from('dramas')
            .select('id, title, synopsis, thumbnail_url, cover_url, total_episodes, r2_folder, created_at, flickreels_id')
            .eq('is_published', false)
            .order('created_at', { ascending: false });

        if (error) {
            return { success: false, data: [], error: error.message };
        }
        return { success: true, data: data || [], error: null };
    } catch (err: any) {
        return { success: false, data: [], error: err.message };
    }
}
