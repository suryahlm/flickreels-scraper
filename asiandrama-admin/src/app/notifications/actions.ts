'use server';

import { supabaseAdmin } from '@/lib/supabase';
import { revalidatePath } from 'next/cache';

export async function fetchNotificationsAdmin() {
    try {
        const { data, error } = await supabaseAdmin
            .from('admin_notifications')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(20);

        if (error) {
            return { success: false, data: [], error: error.message };
        }
        return { success: true, data: data || [], error: null };
    } catch (err: any) {
        return { success: false, data: [], error: err.message };
    }
}

export async function createNotificationAdmin(title: string, message: string, type: 'info' | 'warning' | 'maintenance') {
    try {
        // Deactivate previous active ones first
        await supabaseAdmin
            .from('admin_notifications')
            .update({ is_active: false })
            .eq('is_active', true);

        const { data, error } = await supabaseAdmin
            .from('admin_notifications')
            .insert({
                title: title.trim(),
                message: message.trim(),
                type,
                is_active: true,
            })
            .select()
            .single();

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/notifications');
        return { success: true, data };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}

export async function deactivateNotificationAdmin(id: string) {
    try {
        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .update({ is_active: false, updated_at: new Date().toISOString() })
            .eq('id', id);

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/notifications');
        return { success: true };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}

export async function deleteNotificationAdmin(id: string) {
    try {
        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .delete()
            .eq('id', id);

        if (error) {
            return { success: false, error: error.message };
        }
        revalidatePath('/notifications');
        return { success: true };
    } catch (err: any) {
        return { success: false, error: err.message };
    }
}
