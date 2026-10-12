'use server';

import { supabaseAdmin } from '@/lib/supabase';
import { revalidatePath } from 'next/cache';

export async function updateUserCoinsAdmin(userId: string, amount: number, reason: string, isAdd: boolean) {
    if (!userId || !amount || amount <= 0 || !reason) {
        return { success: false, error: 'Invalid input' };
    }

    try {
        const finalAmount = isAdd ? amount : -amount;

        // Get current balance from profiles to calculate new balance
        const { data: profile } = await supabaseAdmin
            .from('profiles')
            .select('coin_balance')
            .eq('id', userId)
            .single();

        const currentBalance = profile?.coin_balance || 0;
        const newBalance = Math.max(0, currentBalance + finalAmount);

        // 1. Update profiles table
        await supabaseAdmin
            .from('profiles')
            .update({ coin_balance: newBalance })
            .eq('id', userId);

        // 2. Update or insert into user_coins table
        const { data: existingCoins } = await supabaseAdmin
            .from('user_coins')
            .select('balance, total_earned')
            .eq('user_id', userId)
            .single();

        if (existingCoins) {
            await supabaseAdmin
                .from('user_coins')
                .update({ 
                    balance: newBalance,
                    total_earned: isAdd ? (existingCoins.total_earned || 0) + amount : existingCoins.total_earned 
                })
                .eq('user_id', userId);
        } else {
            await supabaseAdmin
                .from('user_coins')
                .insert({ 
                    user_id: userId, 
                    balance: newBalance, 
                    total_earned: isAdd ? newBalance : 0 
                });
        }

        // 3. Log transaction
        await supabaseAdmin.from('coin_transactions').insert({
            user_id: userId,
            amount: finalAmount,
            type: isAdd ? 'admin_add' : 'admin_deduct',
            description: reason,
        });

        revalidatePath('/users');
        return { success: true, newBalance };
    } catch (error: any) {
        return { success: false, error: error.message };
    }
}

export async function grantUserVipAdmin(userId: string, days: number) {
    if (!userId || !days || days <= 0) return { success: false, error: 'Invalid input' };

    try {
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + days);
        const expiresIso = expiresAt.toISOString();

        // Insert into subscriptions
        await supabaseAdmin.from('subscriptions').insert({
            user_id: userId,
            plan_type: 'admin_grant',
            status: 'active',
            expires_at: expiresIso,
        });

        // Update profile
        await supabaseAdmin.from('profiles').update({
            is_vip: true,
            vip_expires_at: expiresIso,
        }).eq('id', userId);

        revalidatePath('/users');
        return { success: true, expiresIso };
    } catch (error: any) {
        return { success: false, error: error.message };
    }
}

export async function cancelUserVipAdmin(userId: string) {
    if (!userId) return { success: false, error: 'Invalid input' };

    try {
        await supabaseAdmin.from('subscriptions')
            .update({ status: 'cancelled' })
            .eq('user_id', userId)
            .eq('status', 'active');

        await supabaseAdmin.from('profiles').update({
            is_vip: false,
            vip_expires_at: null,
        }).eq('id', userId);

        revalidatePath('/users');
        return { success: true };
    } catch (error: any) {
        return { success: false, error: error.message };
    }
}

export async function toggleUserBanAdmin(userId: string, newBanStatus: boolean) {
    if (!userId) return { success: false, error: 'Invalid input' };

    try {
        await supabaseAdmin.from('profiles')
            .update({ is_banned: newBanStatus })
            .eq('id', userId);

        revalidatePath('/users');
        return { success: true };
    } catch (error: any) {
        return { success: false, error: error.message };
    }
}

export async function fetchUsersAdmin(params: {
    page?: number;
    pageSize?: number;
    filterVip?: boolean;
    filterBanned?: boolean;
    sortByCoins?: boolean;
    search?: string;
}) {
    const {
        page = 1,
        pageSize = 25,
        filterVip = false,
        filterBanned = false,
        sortByCoins = false,
        search = ''
    } = params;

    try {
        let query = supabaseAdmin.from('profiles').select('*', { count: 'exact' });

        if (filterVip) {
            query = query.eq('is_vip', true);
        }
        if (filterBanned) {
            query = query.eq('is_banned', true);
        }
        if (search) {
            query = query.or(`email.ilike.%${search}%,full_name.ilike.%${search}%`);
        }
        if (sortByCoins) {
            query = query.order('coin_balance', { ascending: false });
        } else {
            query = query.order('created_at', { ascending: false });
        }

        const from = (page - 1) * pageSize;
        const to = from + pageSize - 1;
        query = query.range(from, to);

        const { data, count, error } = await query;
        if (error) {
            return { success: false, data: [], count: 0, error: error.message };
        }
        return { success: true, data: data || [], count: count || 0, error: null };
    } catch (e: any) {
        return { success: false, data: [], count: 0, error: e.message };
    }
}

