'use server';

import { supabaseAdmin, type Drama, type Category } from '@/lib/supabase';
import { revalidatePath } from 'next/cache';

export async function fetchDramasCatalogAdmin() {
    try {
        const [dramasRes, catsRes] = await Promise.all([
            supabaseAdmin
                .from('dramas')
                .select('id, title, r2_folder, category_id, total_episodes, view_count, is_published, release_status, created_at, cover_url, thumbnail_url, source_data')
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

export async function fetchDramaForEdit(id: string) {
    try {
        const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
        const query = isUuid
            ? supabaseAdmin.from('dramas').select('*').eq('id', id)
            : supabaseAdmin.from('dramas').select('*').eq('flickreels_id', id);

        const [dramaRes, catsRes] = await Promise.all([
            query.maybeSingle(),
            supabaseAdmin
                .from('categories')
                .select('id, name, slug, display_order')
                .order('display_order'),
        ]);

        if (dramaRes.error) {
            return {
                success: false,
                drama: null,
                categories: [],
                error: dramaRes.error.message,
            };
        }

        if (!dramaRes.data) {
            return {
                success: false,
                drama: null,
                categories: (catsRes.data || []) as Category[],
                error: 'Drama tidak ditemukan',
            };
        }

        return {
            success: true,
            drama: dramaRes.data,
            categories: (catsRes.data || []) as Category[],
            error: null,
        };
    } catch (err: any) {
        return {
            success: false,
            drama: null,
            categories: [],
            error: err.message,
        };
    }
}

export async function updateDramaAdminAction(id: string, updates: Record<string, any>) {
    try {
        const cleanUpdates: Record<string, any> = {
            updated_at: new Date().toISOString(),
        };

        if (updates.title !== undefined) cleanUpdates.title = updates.title.trim();
        if (updates.synopsis !== undefined) cleanUpdates.synopsis = updates.synopsis;
        if (updates.category_id !== undefined) cleanUpdates.category_id = updates.category_id || null;
        if (updates.cover_url !== undefined) cleanUpdates.cover_url = updates.cover_url;
        if (updates.thumbnail_url !== undefined) cleanUpdates.thumbnail_url = updates.thumbnail_url;
        if (updates.release_status !== undefined) cleanUpdates.release_status = updates.release_status;
        if (updates.view_count !== undefined) cleanUpdates.view_count = Number(updates.view_count) || 0;
        if (updates.total_episodes !== undefined) cleanUpdates.total_episodes = Number(updates.total_episodes) || 0;
        if (updates.is_published !== undefined) {
            cleanUpdates.is_published = updates.is_published;
            if (updates.is_published) {
                cleanUpdates.created_at = new Date().toISOString();
            }
        }

        const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
        const query = isUuid
            ? supabaseAdmin.from('dramas').update(cleanUpdates).eq('id', id)
            : supabaseAdmin.from('dramas').update(cleanUpdates).eq('flickreels_id', id);

        const { data, error } = await query
            .select()
            .single();

        if (error) {
            return { success: false, error: error.message };
        }

        try {
            revalidatePath('/dramas');
            revalidatePath(`/dramas/${id}/edit`);
            revalidatePath('/draft-dramas');
            revalidatePath('/');
        } catch (e) {}

        return { success: true, drama: data };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}

