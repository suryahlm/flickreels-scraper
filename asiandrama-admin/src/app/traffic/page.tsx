'use client';

import { supabase } from '@/lib/supabase';
import { Crown, Eye, Film, TrendingUp, Users } from 'lucide-react';
import { useEffect, useState } from 'react';

interface TrafficStats {
    totalViews: number;
    totalUsers: number;
    newUsersWeek: number;
    topDramaTitle: string;
}

interface TopDrama {
    title: string;
    view_count: number;
    total_episodes: number;
    category_id: string | null;
}

interface RecentUser {
    full_name: string | null;
    email: string | null;
    created_at: string;
}

interface CoinActivity {
    amount: number;
    reason: string | null;
    created_at: string;
    user_id: string;
    user_name?: string;
}

interface CategoryCount {
    name: string;
    count: number;
}

interface DailyData {
    date: string;
    label: string;
    count: number;
}

export default function TrafficPage() {
    const [stats, setStats] = useState<TrafficStats>({
        totalViews: 0,
        totalUsers: 0,
        newUsersWeek: 0,
        topDramaTitle: '-',
    });
    const [topDramas, setTopDramas] = useState<TopDrama[]>([]);
    const [recentUsers, setRecentUsers] = useState<RecentUser[]>([]);
    const [coinActivity, setCoinActivity] = useState<CoinActivity[]>([]);
    const [categoryData, setCategoryData] = useState<CategoryCount[]>([]);
    const [userTrend, setUserTrend] = useState<DailyData[]>([]);
    const [coinTrend, setCoinTrend] = useState<DailyData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTrafficData();
    }, []);

    async function fetchTrafficData() {
        try {
            // ---- Stat Cards ----
            // Total views
            const { data: viewData } = await supabase
                .from('dramas')
                .select('view_count');
            const totalViews = viewData?.reduce((sum, d) => sum + (d.view_count || 0), 0) || 0;

            // Total users
            const { count: userCount } = await supabase
                .from('profiles')
                .select('*', { count: 'exact', head: true });

            // New users this week
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            const { count: newUsers } = await supabase
                .from('profiles')
                .select('*', { count: 'exact', head: true })
                .gte('created_at', weekAgo.toISOString());

            // Top drama
            const { data: topDrama } = await supabase
                .from('dramas')
                .select('title, view_count')
                .order('view_count', { ascending: false })
                .limit(1);

            setStats({
                totalViews,
                totalUsers: userCount || 0,
                newUsersWeek: newUsers || 0,
                topDramaTitle: topDrama?.[0]?.title || '-',
            });

            // ---- Top 10 Drama ----
            const { data: topDramasData } = await supabase
                .from('dramas')
                .select('title, view_count, total_episodes, category_id')
                .order('view_count', { ascending: false })
                .limit(10);
            setTopDramas(topDramasData || []);

            // ---- Recent Users ----
            const { data: usersData } = await supabase
                .from('profiles')
                .select('full_name, email, created_at')
                .order('created_at', { ascending: false })
                .limit(10);
            setRecentUsers(usersData || []);

            // ---- Coin Activity ----
            const { data: coinData } = await supabase
                .from('coin_transactions')
                .select('amount, reason, created_at, user_id')
                .order('created_at', { ascending: false })
                .limit(10);
            setCoinActivity(coinData || []);

            // ---- Category Distribution ----
            const { data: categoryDramas } = await supabase
                .from('dramas')
                .select('category_id');
            const { data: categoriesRaw } = await supabase
                .from('categories')
                .select('id, name');

            if (categoryDramas && categoriesRaw) {
                const catMap = new Map(categoriesRaw.map(c => [c.id, c.name]));
                const countMap = new Map<string, number>();
                categoryDramas.forEach(d => {
                    const name = catMap.get(d.category_id) || 'Tanpa Kategori';
                    countMap.set(name, (countMap.get(name) || 0) + 1);
                });
                const sorted = [...countMap.entries()]
                    .map(([name, count]) => ({ name, count }))
                    .sort((a, b) => b.count - a.count);
                setCategoryData(sorted);
            }

            // ---- User Registration Trend (30 days) ----
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            const { data: allUsers } = await supabase
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
            setUserTrend(
                [...userDailyMap.entries()].map(([date, count]) => ({
                    date,
                    label: new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
                    count,
                }))
            );

            // ---- Coin Transaction Trend (30 days) ----
            const { data: allCoins } = await supabase
                .from('coin_transactions')
                .select('created_at, amount')
                .gte('created_at', thirtyDaysAgo.toISOString());

            const coinDailyMap = new Map<string, number>();
            for (let i = 29; i >= 0; i--) {
                const d = new Date();
                d.setDate(d.getDate() - i);
                const key = d.toISOString().split('T')[0];
                coinDailyMap.set(key, 0);
            }
            allCoins?.forEach(c => {
                const key = c.created_at.split('T')[0];
                if (coinDailyMap.has(key)) {
                    coinDailyMap.set(key, (coinDailyMap.get(key) || 0) + 1);
                }
            });
            setCoinTrend(
                [...coinDailyMap.entries()].map(([date, count]) => ({
                    date,
                    label: new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
                    count,
                }))
            );

        } catch (error) {
            console.error('Error fetching traffic data:', error);
        } finally {
            setLoading(false);
        }
    }

    const maxViews = topDramas.length > 0 ? Math.max(...topDramas.map(d => d.view_count || 1)) : 1;
    const maxCategoryCount = categoryData.length > 0 ? Math.max(...categoryData.map(c => c.count)) : 1;
    const maxUserTrend = Math.max(...userTrend.map(d => d.count), 1);
    const maxCoinTrend = Math.max(...coinTrend.map(d => d.count), 1);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                    <p className="text-gray-400">Memuat data trafik...</p>
                </div>
            </div>
        );
    }

    return (
        <div>
            <h1 className="text-2xl font-bold mb-6">Trafik & Analitik</h1>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[
                    { label: 'Total Views', value: stats.totalViews.toLocaleString(), icon: Eye, color: 'bg-green-600' },
                    { label: 'Total Users', value: stats.totalUsers.toLocaleString(), icon: Users, color: 'bg-blue-600' },
                    { label: 'User Baru (7 hari)', value: `+${stats.newUsersWeek}`, icon: TrendingUp, color: 'bg-purple-600' },
                    { label: 'Drama Terpopuler', value: stats.topDramaTitle, icon: Crown, color: 'bg-amber-500', small: stats.topDramaTitle.length > 20 },
                ].map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <div key={stat.label} className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <p className="text-gray-400 text-sm">{stat.label}</p>
                                    <p className={`font-bold mt-1 truncate ${stat.small ? 'text-lg' : 'text-2xl'}`}>
                                        {stat.value}
                                    </p>
                                </div>
                                <div className={`${stat.color} p-3 rounded-lg ml-3 flex-shrink-0`}>
                                    <Icon size={24} />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* User Registration & Coin Activity Trend Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* User Registration Trend */}
                <div className="bg-gray-900 rounded-xl border border-gray-800">
                    <div className="p-4 border-b border-gray-800">
                        <h2 className="font-semibold flex items-center gap-2">
                            <Users size={18} className="text-blue-400" />
                            Pendaftaran User (30 hari)
                        </h2>
                    </div>
                    <div className="p-4">
                        <div className="flex items-end gap-[2px] h-40">
                            {userTrend.map((d, i) => (
                                <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                                    <div
                                        className="w-full bg-blue-500 rounded-t-sm min-h-[2px] transition-all hover:bg-blue-400"
                                        style={{ height: `${Math.max((d.count / maxUserTrend) * 100, 2)}%` }}
                                    ></div>
                                    {/* Tooltip */}
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                                        {d.label}: {d.count} user
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-2 text-xs text-gray-500">
                            <span>{userTrend[0]?.label}</span>
                            <span>{userTrend[Math.floor(userTrend.length / 2)]?.label}</span>
                            <span>{userTrend[userTrend.length - 1]?.label}</span>
                        </div>
                    </div>
                </div>

                {/* Coin Transaction Trend */}
                <div className="bg-gray-900 rounded-xl border border-gray-800">
                    <div className="p-4 border-b border-gray-800">
                        <h2 className="font-semibold flex items-center gap-2">
                            <TrendingUp size={18} className="text-yellow-400" />
                            Aktivitas Koin (30 hari)
                        </h2>
                    </div>
                    <div className="p-4">
                        <div className="flex items-end gap-[2px] h-40">
                            {coinTrend.map((d, i) => (
                                <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                                    <div
                                        className="w-full bg-yellow-500 rounded-t-sm min-h-[2px] transition-all hover:bg-yellow-400"
                                        style={{ height: `${Math.max((d.count / maxCoinTrend) * 100, 2)}%` }}
                                    ></div>
                                    <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-700 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                                        {d.label}: {d.count} transaksi
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-2 text-xs text-gray-500">
                            <span>{coinTrend[0]?.label}</span>
                            <span>{coinTrend[Math.floor(coinTrend.length / 2)]?.label}</span>
                            <span>{coinTrend[coinTrend.length - 1]?.label}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Top 10 Drama */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 mb-8">
                <div className="p-4 border-b border-gray-800">
                    <h2 className="font-semibold flex items-center gap-2">
                        <Film size={18} className="text-pink-400" />
                        Top 10 Drama Terpopuler
                    </h2>
                </div>
                <div className="p-4">
                    {topDramas.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">Belum ada data views</p>
                    ) : (
                        <div className="space-y-3">
                            {topDramas.map((drama, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                    <span className={`text-lg font-bold w-8 text-center ${idx < 3 ? 'text-amber-400' : 'text-gray-500'}`}>
                                        {idx + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="font-medium truncate">{drama.title}</span>
                                            <span className="text-sm text-gray-400 ml-2 flex-shrink-0">
                                                {(drama.view_count || 0).toLocaleString()} views · {drama.total_episodes} eps
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-800 rounded-full h-2">
                                            <div
                                                className={`h-2 rounded-full transition-all ${idx === 0 ? 'bg-gradient-to-r from-amber-500 to-yellow-400' :
                                                    idx === 1 ? 'bg-gradient-to-r from-gray-300 to-gray-400' :
                                                        idx === 2 ? 'bg-gradient-to-r from-amber-700 to-amber-600' :
                                                            'bg-gray-600'
                                                    }`}
                                                style={{ width: `${Math.max((drama.view_count || 0) / maxViews * 100, 3)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* User Terbaru & Coin Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Recent Users */}
                <div className="bg-gray-900 rounded-xl border border-gray-800">
                    <div className="p-4 border-b border-gray-800">
                        <h2 className="font-semibold">User Terbaru</h2>
                    </div>
                    <div className="p-4">
                        {recentUsers.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">Belum ada user</p>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="text-gray-400 text-sm">
                                        <th className="text-left pb-3">Nama</th>
                                        <th className="text-left pb-3">Tanggal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {recentUsers.map((user, idx) => (
                                        <tr key={idx} className="border-t border-gray-800">
                                            <td className="py-2.5">
                                                <p className="font-medium text-sm">{user.full_name || 'Anonymous'}</p>
                                                <p className="text-xs text-gray-500 truncate max-w-[200px]">{user.email}</p>
                                            </td>
                                            <td className="py-2.5 text-sm text-gray-400">
                                                {new Date(user.created_at).toLocaleDateString('id-ID', {
                                                    day: '2-digit', month: 'short', year: 'numeric'
                                                })}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>

                {/* Coin Activity */}
                <div className="bg-gray-900 rounded-xl border border-gray-800">
                    <div className="p-4 border-b border-gray-800">
                        <h2 className="font-semibold">Aktivitas Koin Terbaru</h2>
                    </div>
                    <div className="p-4">
                        {coinActivity.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">Belum ada aktivitas</p>
                        ) : (
                            <table className="w-full">
                                <thead>
                                    <tr className="text-gray-400 text-sm">
                                        <th className="text-left pb-3">Jumlah</th>
                                        <th className="text-left pb-3">Alasan</th>
                                        <th className="text-left pb-3">Tanggal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {coinActivity.map((coin, idx) => (
                                        <tr key={idx} className="border-t border-gray-800">
                                            <td className={`py-2.5 font-bold text-sm ${coin.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                {coin.amount > 0 ? '+' : ''}{coin.amount}
                                            </td>
                                            <td className="py-2.5 text-sm text-gray-300 truncate max-w-[180px]">
                                                {coin.reason || '-'}
                                            </td>
                                            <td className="py-2.5 text-sm text-gray-400">
                                                {new Date(coin.created_at).toLocaleDateString('id-ID', {
                                                    day: '2-digit', month: 'short'
                                                })}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            </div>

            {/* Drama per Kategori */}
            <div className="bg-gray-900 rounded-xl border border-gray-800">
                <div className="p-4 border-b border-gray-800">
                    <h2 className="font-semibold">Drama per Kategori</h2>
                </div>
                <div className="p-4">
                    {categoryData.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">Belum ada data</p>
                    ) : (
                        <div className="space-y-3">
                            {categoryData.map((cat) => (
                                <div key={cat.name} className="flex items-center gap-3">
                                    <span className="text-sm text-gray-300 w-32 truncate">{cat.name}</span>
                                    <div className="flex-1 bg-gray-800 rounded-full h-6 overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full flex items-center px-2 transition-all"
                                            style={{ width: `${Math.max((cat.count / maxCategoryCount) * 100, 8)}%` }}
                                        >
                                            <span className="text-xs font-bold text-gray-900">{cat.count}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
