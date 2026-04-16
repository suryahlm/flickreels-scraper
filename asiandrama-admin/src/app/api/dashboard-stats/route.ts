import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

/**
 * GET /api/dashboard-stats
 * Server-side API route that uses supabaseAdmin (service role key) to bypass RLS
 * and return accurate dashboard statistics including real-time coin balances.
 */
/**
 * Helper to get the correct sum over 1,000+ rows bypassing the 1,000 row limit.
 */
async function fetchSum(table: string, column: string): Promise<number> {
    let total = 0;
    let page = 0;
    const pageSize = 1000;
    let hasMore = true;

    while (hasMore) {
        const { data } = await supabaseAdmin
            .from(table)
            .select(column)
            .range(page * pageSize, (page + 1) * pageSize - 1);

        if (!data || data.length === 0) {
            hasMore = false;
        } else {
            total += data.reduce((sum, item: any) => sum + (item[column] || 0), 0);
            if (data.length < pageSize) hasMore = false;
        }
        page++;
    }
    return total;
}

export async function GET() {
    try {
        // Fetch all stats in parallel for speed
        const [
            dramaResult,
            userResult,
            viewResult,
            coinResult,
            recentUsersResult,
            topDramasResult,
        ] = await Promise.all([
            // Drama count
            supabaseAdmin
                .from('dramas')
                .select('*', { count: 'exact', head: true }),

            // User count
            supabaseAdmin
                .from('profiles')
                .select('*', { count: 'exact', head: true }),

            // Total views (Pagination loop for >1000 limit)
            fetchSum('dramas', 'view_count'),

            // Total coins (Pagination loop for >1000 limit)
            fetchSum('user_coins', 'balance'),

            // Recent 5 users
            supabaseAdmin
                .from('profiles')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(5),

            // Top 5 dramas by views
            supabaseAdmin
                .from('dramas')
                .select('*')
                .order('view_count', { ascending: false })
                .limit(5),
        ]);

        // Calculate totals (totalViews and totalCoins are already numbers)

        // Enrich recent users with real coin balances
        let recentUsers = recentUsersResult.data || [];
        if (recentUsers.length > 0) {
            const userIds = recentUsers.map(u => u.id);
            const { data: coinBalances } = await supabaseAdmin
                .from('user_coins')
                .select('user_id, balance')
                .in('user_id', userIds);

            const coinMap = new Map(coinBalances?.map(c => [c.user_id, c.balance]) || []);
            recentUsers = recentUsers.map(u => ({
                ...u,
                coin_balance: coinMap.get(u.id) ?? u.coin_balance ?? 0,
            }));
        }

        return NextResponse.json({
            stats: {
                totalDramas: dramaResult.count || 0,
                totalUsers: userResult.count || 0,
                totalViews: viewResult,
                totalCoins: coinResult,
            },
            recentUsers,
            topDramas: topDramasResult.data || [],
        });
    } catch (error) {
        console.error('[Dashboard API] Error:', error);
        return NextResponse.json(
            { error: 'Failed to fetch dashboard stats' },
            { status: 500 }
        );
    }
}
