'use server';

import { supabaseAdmin } from '@/lib/supabase';

export async function fetchTrafficAnalyticsAdmin() {
    try {
        // Total views
        const { data: viewData } = await supabaseAdmin
            .from('dramas')
            .select('view_count');
        const totalViews = viewData?.reduce((sum, d) => sum + (d.view_count || 0), 0) || 0;

        // Total users
        const { count: userCount } = await supabaseAdmin
            .from('profiles')
            .select('*', { count: 'exact', head: true });

        // New users this week
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        const { count: newUsers } = await supabaseAdmin
            .from('profiles')
            .select('*', { count: 'exact', head: true })
            .gte('created_at', weekAgo.toISOString());

        // Top drama
        const { data: topDrama } = await supabaseAdmin
            .from('dramas')
            .select('title, view_count')
            .order('view_count', { ascending: false })
            .limit(1);

        // Top 10 Drama
        const { data: topDramasData } = await supabaseAdmin
            .from('dramas')
            .select('id, title, view_count, total_episodes, category_id, r2_folder')
            .order('view_count', { ascending: false })
            .limit(10);

        // Recent Users
        const { data: usersData } = await supabaseAdmin
            .from('profiles')
            .select('full_name, email, created_at')
            .order('created_at', { ascending: false })
            .limit(10);

        // Category Distribution
        const { data: categoryDramas } = await supabaseAdmin
            .from('dramas')
            .select('category_id');
        const { data: categoriesRaw } = await supabaseAdmin
            .from('categories')
            .select('id, name');

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

        // 30 days user registration trend
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        const { data: allUsers } = await supabaseAdmin
            .from('profiles')
            .select('created_at')
            .gte('created_at', thirtyDaysAgo.toISOString());

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

        // Active User Trend from user_activity_log
        const { data: activityData } = await supabaseAdmin
            .from('user_activity_log')
            .select('activity_date, user_id')
            .gte('activity_date', thirtyDaysAgo.toISOString().split('T')[0]);

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
