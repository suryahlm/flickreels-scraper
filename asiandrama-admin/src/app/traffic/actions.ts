'use server';

import { supabaseAdmin } from '@/lib/supabase';

export async function fetchTrafficAnalyticsAdmin() {
    try {
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        // Run all queries in parallel for maximum speed
        const [
            viewRes,
            userCountRes,
            newUsersRes,
            topDramaRes,
            topDramasRes,
            recentUsersRes,
            catDramasRes,
            catsRawRes,
            allUsersRes,
            activityRes
        ] = await Promise.all([
            supabaseAdmin.from('dramas').select('view_count'),
            supabaseAdmin.from('profiles').select('*', { count: 'exact', head: true }),
            supabaseAdmin.from('profiles').select('*', { count: 'exact', head: true }).gte('created_at', weekAgo.toISOString()),
            supabaseAdmin.from('dramas').select('title, view_count').order('view_count', { ascending: false }).limit(1),
            supabaseAdmin.from('dramas').select('id, title, view_count, total_episodes, category_id, r2_folder').order('view_count', { ascending: false }).limit(10),
            supabaseAdmin.from('profiles').select('full_name, email, created_at').order('created_at', { ascending: false }).limit(10),
            supabaseAdmin.from('dramas').select('category_id'),
            supabaseAdmin.from('categories').select('id, name'),
            supabaseAdmin.from('profiles').select('created_at').gte('created_at', thirtyDaysAgo.toISOString()),
            supabaseAdmin.from('user_activity_log').select('activity_date, user_id').gte('activity_date', thirtyDaysAgo.toISOString().split('T')[0]),
        ]);

        const totalViews = viewRes.data?.reduce((sum, d) => sum + (d.view_count || 0), 0) || 0;
        const userCount = userCountRes.count;
        const newUsers = newUsersRes.count;
        const topDrama = topDramaRes.data;
        const topDramasData = topDramasRes.data;
        const usersData = recentUsersRes.data;
        const categoryDramas = catDramasRes.data;
        const categoriesRaw = catsRawRes.data;
        const allUsers = allUsersRes.data;
        const activityData = activityRes.data;

        let categoryData: { name: string; count: number }[] = [];
        if (categoryDramas && categoriesRaw) {
            const catMap = new Map(categoriesRaw.map(c => [c.id, c.name]));
            const countMap = new Map<string, number>();
            categoryDramas.forEach(d => {
                const name = (d.category_id && catMap.get(d.category_id)) || 'Tanpa Kategori';
                countMap.set(name, (countMap.get(name) || 0) + 1);
            });
            categoryData = [...countMap.entries()]
                .map(([name, count]) => ({ name, count }))
                .sort((a, b) => b.count - a.count);
        }

        const userDailyMap = new Map<string, number>();
        for (let i = 29; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const key = d.toISOString().split('T')[0];
            userDailyMap.set(key, 0);
        }
        allUsers?.forEach(u => {
            const key = u.created_at.split('T')[0];
            if (userDailyMap.has(key)) {
                userDailyMap.set(key, (userDailyMap.get(key) || 0) + 1);
            }
        });

        const userTrend = [...userDailyMap.entries()].map(([date, count]) => ({
            date,
            label: new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
            count,
        }));

        const activeUserDailyMap = new Map<string, Set<string>>();
        for (let i = 29; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const key = d.toISOString().split('T')[0];
            activeUserDailyMap.set(key, new Set());
        }
        activityData?.forEach(a => {
            const key = a.activity_date;
            if (activeUserDailyMap.has(key)) {
                activeUserDailyMap.get(key)!.add(a.user_id);
            }
        });
        const activeUserTrend = [...activeUserDailyMap.entries()].map(([date, users]) => ({
            date,
            label: new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
            count: users.size,
        }));

        return {
            success: true,
            stats: {
                totalViews,
                totalUsers: userCount || 0,
                newUsersWeek: newUsers || 0,
                topDramaTitle: topDrama?.[0]?.title || '-',
            },
            topDramas: topDramasData || [],
            recentUsers: usersData || [],
            categoryData,
            userTrend,
            activeUserTrend,
        };
    } catch (err: any) {
        return {
            success: false,
            stats: { totalViews: 0, totalUsers: 0, newUsersWeek: 0, topDramaTitle: '-' },
            topDramas: [],
            recentUsers: [],
            categoryData: [],
            userTrend: [],
            activeUserTrend: [],
            error: err.message,
        };
    }
}
