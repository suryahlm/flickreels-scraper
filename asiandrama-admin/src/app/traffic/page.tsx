'use client';

import { supabase } from '@/lib/supabase';
import { Activity, Crown, Eye, Film, TrendingUp, Users, Sparkles, FolderOpen } from 'lucide-react';
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
    const [categoryData, setCategoryData] = useState<CategoryCount[]>([]);
    const [userTrend, setUserTrend] = useState<DailyData[]>([]);
    const [activeUserTrend, setActiveUserTrend] = useState<DailyData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTrafficData();
    }, []);

    async function fetchTrafficData() {
        try {
            setLoading(true);
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

            // Top 10 Drama
            const { data: topDramasData } = await supabase
                .from('dramas')
                .select('title, view_count, total_episodes, category_id')
                .order('view_count', { ascending: false })
                .limit(10);
            setTopDramas(topDramasData || []);

            // Recent Users
            const { data: usersData } = await supabase
                .from('profiles')
                .select('full_name, email, created_at')
                .order('created_at', { ascending: false })
                .limit(10);
            setRecentUsers(usersData || []);

            // Category Distribution
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
                    const name = (d.category_id && catMap.get(d.category_id)) || 'Tanpa Kategori';
                    countMap.set(name, (countMap.get(name) || 0) + 1);
                });
                const sorted = [...countMap.entries()]
                    .map(([name, count]) => ({ name, count }))
                    .sort((a, b) => b.count - a.count);
                setCategoryData(sorted);
            }

            // User Registration Trend (30 days)
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

            // Active User Trend (30 days)
            const { data: activityData } = await supabase
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
            setActiveUserTrend(
                [...activeUserDailyMap.entries()].map(([date, users]) => ({
                    date,
                    label: new Date(date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
                    count: users.size,
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
    const maxActiveUserTrend = Math.max(...activeUserTrend.map(d => d.count), 1);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center p-2">
                        <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="text-xs font-semibold text-gray-400">Menganalisa lalu lintas data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                {[
                    { label: 'Total Penayangan', value: stats.totalViews.toLocaleString(), sub: 'Akumulasi streaming', icon: Eye, color: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'from-emerald-500/20 to-teal-500/5' },
                    { label: 'Total Pengguna', value: stats.totalUsers.toLocaleString(), sub: 'Akun terdaftar', icon: Users, color: 'text-blue-400', border: 'border-blue-500/30', bg: 'from-blue-500/20 to-indigo-500/5' },
                    { label: 'User Baru (7 Hari)', value: `+${stats.newUsersWeek}`, sub: 'Pertumbuhan mingguan', icon: TrendingUp, color: 'text-amber-400', border: 'border-amber-500/30', bg: 'from-amber-500/20 to-yellow-500/5' },
                    { label: 'Top Drama Saat Ini', value: stats.topDramaTitle, sub: 'Paling sering ditonton', icon: Crown, color: 'text-purple-400', border: 'border-purple-500/30', bg: 'from-purple-500/20 to-pink-500/5', small: true },
                ].map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <div key={stat.label} className={`glass-card rounded-2xl p-6 border ${stat.border} relative overflow-hidden group`}>
                            <div className={`absolute top-0 right-0 w-28 h-28 bg-gradient-to-br ${stat.bg} rounded-full blur-2xl pointer-events-none group-hover:scale-125 transition-transform`} />
                            <div className="relative z-10 flex items-start justify-between">
                                <div className="min-w-0 flex-1 pr-2">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">{stat.label}</p>
                                    <p className={`font-extrabold text-white mt-1.5 tracking-tight truncate ${stat.small ? 'text-lg' : 'text-3xl'}`}>
                                        {stat.value}
                                    </p>
                                    <p className="text-[11px] text-gray-500 mt-1">{stat.sub}</p>
                                </div>
                                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${stat.bg} border ${stat.border} flex items-center justify-center ${stat.color} flex-shrink-0 shadow-lg`}>
                                    <Icon size={20} />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* User Registration & Active Users Trend Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* User Registration Trend */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-6">
                    <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.07]">
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                                <Users size={16} />
                            </div>
                            <div>
                                <h2 className="text-sm font-bold text-white tracking-tight">Pendaftaran User (30 Hari)</h2>
                                <p className="text-[11px] text-gray-400">Tren registrasi akun baru per hari</p>
                            </div>
                        </div>
                        <span className="px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-bold">
                            30D Range
                        </span>
                    </div>

                    <div className="pt-2">
                        <div className="flex items-end gap-[3px] h-44">
                            {userTrend.map((d) => (
                                <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                                    <div
                                        className="w-full bg-gradient-to-t from-blue-600 to-cyan-400 rounded-t-sm min-h-[3px] transition-all group-hover:from-blue-500 group-hover:to-cyan-300 shadow-[0_0_8px_rgba(59,130,246,0.2)]"
                                        style={{ height: `${Math.max((d.count / maxUserTrend) * 100, 3)}%` }}
                                    />
                                    <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center bg-[#090D15] border border-blue-500/40 text-white text-[10px] px-2.5 py-1.5 rounded-lg whitespace-nowrap z-20 shadow-xl pointer-events-none">
                                        <span className="text-gray-400">{d.label}</span>
                                        <span className="font-bold text-blue-400">+{d.count} akun baru</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-3 text-[11px] text-gray-500 font-medium">
                            <span>{userTrend[0]?.label}</span>
                            <span>{userTrend[Math.floor(userTrend.length / 2)]?.label}</span>
                            <span>{userTrend[userTrend.length - 1]?.label}</span>
                        </div>
                    </div>
                </div>

                {/* Active Users Trend */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-6">
                    <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.07]">
                        <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                                <Activity size={16} />
                            </div>
                            <div>
                                <h2 className="text-sm font-bold text-white tracking-tight">Aktivitas Pemirsa (30 Hari)</h2>
                                <p className="text-[11px] text-gray-400">Jumlah pengguna unik aktif per hari</p>
                            </div>
                        </div>
                        <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                            Live Stream
                        </span>
                    </div>

                    <div className="pt-2">
                        <div className="flex items-end gap-[3px] h-44">
                            {activeUserTrend.map((d) => (
                                <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                                    <div
                                        className="w-full bg-gradient-to-t from-emerald-600 to-teal-400 rounded-t-sm min-h-[3px] transition-all group-hover:from-emerald-500 group-hover:to-teal-300 shadow-[0_0_8px_rgba(16,185,129,0.2)]"
                                        style={{ height: `${Math.max((d.count / maxActiveUserTrend) * 100, 3)}%` }}
                                    />
                                    <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center bg-[#090D15] border border-emerald-500/40 text-white text-[10px] px-2.5 py-1.5 rounded-lg whitespace-nowrap z-20 shadow-xl pointer-events-none">
                                        <span className="text-gray-400">{d.label}</span>
                                        <span className="font-bold text-emerald-400">{d.count} user aktif</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-3 text-[11px] text-gray-500 font-medium">
                            <span>{activeUserTrend[0]?.label}</span>
                            <span>{activeUserTrend[Math.floor(activeUserTrend.length / 2)]?.label}</span>
                            <span>{activeUserTrend[activeUserTrend.length - 1]?.label}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Top 10 Drama Podium Rankings */}
            <div className="glass-card-static rounded-2xl border border-white/[0.08] p-6">
                <div className="flex items-center justify-between pb-4 mb-5 border-b border-white/[0.07]">
                    <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                            <Film size={16} />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white tracking-tight">Top 10 Drama Terfavorit Audiens</h2>
                            <p className="text-[11px] text-gray-400">Peringkat penayangan tertinggi sepanjang masa</p>
                        </div>
                    </div>
                </div>

                {topDramas.length === 0 ? (
                    <div className="text-center py-12 text-xs text-gray-500">Belum ada statistik penayangan</div>
                ) : (
                    <div className="space-y-4">
                        {topDramas.map((drama, idx) => {
                            const isGold = idx === 0;
                            const isSilver = idx === 1;
                            const isBronze = idx === 2;
                            return (
                                <div key={idx} className="flex items-center gap-4 group">
                                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs flex-shrink-0 border ${
                                        isGold
                                            ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-[0_0_12px_rgba(229,169,60,0.3)]'
                                            : isSilver
                                            ? 'bg-slate-300/20 border-slate-300/40 text-slate-200'
                                            : isBronze
                                            ? 'bg-amber-700/20 border-amber-700/40 text-amber-400'
                                            : 'bg-white/[0.03] border-white/[0.06] text-gray-500'
                                    }`}>
                                        {idx + 1}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1.5">
                                            <span className="text-xs font-bold text-white truncate group-hover:text-amber-300 transition-colors">
                                                {drama.title}
                                            </span>
                                            <span className="text-[11px] font-semibold text-gray-400 ml-3 flex-shrink-0">
                                                {(drama.view_count || 0).toLocaleString()} <span className="text-gray-500">views</span> · {drama.total_episodes} eps
                                            </span>
                                        </div>
                                        <div className="w-full bg-white/[0.04] rounded-full h-2 overflow-hidden border border-white/[0.05]">
                                            <div
                                                className={`h-full rounded-full transition-all ${
                                                    isGold
                                                        ? 'bg-gradient-to-r from-amber-500 to-yellow-300 shadow-[0_0_8px_rgba(229,169,60,0.4)]'
                                                        : isSilver
                                                        ? 'bg-gradient-to-r from-slate-400 to-slate-200'
                                                        : isBronze
                                                        ? 'bg-gradient-to-r from-amber-700 to-amber-500'
                                                        : 'bg-gradient-to-r from-blue-500 to-cyan-400'
                                                }`}
                                                style={{ width: `${Math.max(((drama.view_count || 0) / maxViews) * 100, 3)}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Category Breakdown & Recent Users Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Distribution */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-6">
                    <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-white/[0.07]">
                        <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                            <FolderOpen size={16} />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white tracking-tight">Distribusi Genre & Kategori</h2>
                            <p className="text-[11px] text-gray-400">Proporsi judul drama yang terdaftar per genre</p>
                        </div>
                    </div>

                    {categoryData.length === 0 ? (
                        <div className="text-center py-10 text-xs text-gray-500">Belum ada data kategori</div>
                    ) : (
                        <div className="space-y-3 pt-1">
                            {categoryData.slice(0, 8).map((cat) => (
                                <div key={cat.name} className="flex items-center gap-3">
                                    <span className="text-xs font-semibold text-gray-300 w-32 truncate">{cat.name}</span>
                                    <div className="flex-1 bg-white/[0.04] rounded-full h-5 overflow-hidden border border-white/[0.05] p-0.5">
                                        <div
                                            className="h-full bg-gradient-to-r from-purple-500 to-amber-400 rounded-full flex items-center justify-end px-2 transition-all shadow-[0_0_10px_rgba(168,85,247,0.2)]"
                                            style={{ width: `${Math.max((cat.count / maxCategoryCount) * 100, 10)}%` }}
                                        >
                                            <span className="text-[10px] font-bold text-[#07090E]">{cat.count}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Recent Users */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-6">
                    <div className="flex items-center gap-2.5 pb-4 mb-4 border-b border-white/[0.07]">
                        <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                            <Users size={16} />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold text-white tracking-tight">Registrasi Terakhir</h2>
                            <p className="text-[11px] text-gray-400">Daftar pengguna yang baru bergabung</p>
                        </div>
                    </div>

                    {recentUsers.length === 0 ? (
                        <div className="text-center py-10 text-xs text-gray-500">Belum ada pengguna</div>
                    ) : (
                        <div className="space-y-2.5">
                            {recentUsers.slice(0, 6).map((u, i) => (
                                <div key={i} className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                                    <div className="min-w-0 pr-2">
                                        <p className="text-xs font-semibold text-white truncate">{u.full_name || 'Anonymous'}</p>
                                        <p className="text-[10px] text-gray-500 truncate">{u.email || '-'}</p>
                                    </div>
                                    <span className="text-[11px] font-medium text-gray-400 flex-shrink-0">
                                        {new Date(u.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
