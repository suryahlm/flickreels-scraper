'use server';

import { supabaseAdmin, type Category } from '@/lib/supabase';
import { revalidatePath } from 'next/cache';

export async function fetchCategoriesAdmin() {
    try {
        const { data, error } = await supabaseAdmin
            .from('categories')
            .select('*')
            .order('display_order');

        if (error) {
            return { success: false, data: [], error: error.message };
        }
        return { success: true, data: data || [], error: null };
    } catch (err: any) {
        return { success: false, data: [], error: err.message };
    }
}

export async function addCategoryAdmin(name: string, displayOrder: number) {
    try {
        const slug = name.toLowerCase().trim().replace(/\s+/g, '-');
        const { data, error } = await supabaseAdmin
            .from('categories')
            .insert({
                name: name.trim(),
                slug,
                display_order: displayOrder,
            })
            .select()
            .single();

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/categories');
        return { success: true, data };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}

export async function updateCategoryAdmin(id: string, name: string) {
    try {
        const slug = name.toLowerCase().trim().replace(/\s+/g, '-');
        const { error } = await supabaseAdmin
            .from('categories')
            .update({ name: name.trim(), slug })
            .eq('id', id);

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/categories');
        return { success: true };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}

export async function deleteCategoryAdmin(id: string) {
    try {
        const { error } = await supabaseAdmin
            .from('categories')
            .delete()
            .eq('id', id);

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/categories');
        return { success: true };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}
