'use client';

import { useEffect, useState } from 'react';
import { Film, Users, Eye, Sparkles, TrendingUp, ArrowUpRight, Plus, Bell, RefreshCw, Crown, Shield } from 'lucide-react';
import { type Drama, type Profile } from '@/lib/supabase';
import Link from 'next/link';

interface Stats {
  totalDramas: number;
  totalUsers: number;
  totalViews: number;
  totalCoins: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    totalDramas: 0,
    totalUsers: 0,
    totalViews: 0,
    totalCoins: 0,
  });
  const [recentUsers, setRecentUsers] = useState<Profile[]>([]);
  const [topDramas, setTopDramas] = useState<Drama[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  async function fetchDashboardData() {
    try {
      setLoading(true);
      const res = await fetch('/api/dashboard-stats');
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      
      const data = await res.json();
      setStats(data.stats);
      setRecentUsers(data.recentUsers || []);
      setTopDramas(data.topDramas || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }

  const statCards = [
    {
      label: 'Katalog Drama',
      value: stats.totalDramas.toLocaleString(),
      subtext: 'Tayangan aktif di katalog',
      icon: Film,
      badge: 'Online',
      color: 'from-amber-500/20 to-yellow-500/5',
      borderColor: 'border-amber-500/30',
      iconColor: 'text-amber-400',
      glow: 'shadow-[0_0_20px_rgba(229,169,60,0.15)]',
    },
    {
      label: 'Total Pengguna',
      value: stats.totalUsers.toLocaleString(),
      subtext: 'Akun terdaftar di sistem',
      icon: Users,
      badge: '+Aktif',
      color: 'from-blue-500/20 to-cyan-500/5',
      borderColor: 'border-blue-500/30',
      iconColor: 'text-blue-400',
      glow: 'shadow-[0_0_20px_rgba(59,130,246,0.15)]',
    },
    {
      label: 'Total Penayangan',
      value: stats.totalViews.toLocaleString(),
      subtext: 'Akumulasi streaming episode',
      icon: Eye,
      badge: 'Real-time',
      color: 'from-emerald-500/20 to-teal-500/5',
      borderColor: 'border-emerald-500/30',
      iconColor: 'text-emerald-400',
      glow: 'shadow-[0_0_20px_rgba(16,185,129,0.15)]',
    },
    {
      label: 'Model Akses',
      value: '100% Free',
      subtext: 'Seluruh episode bebas biaya',
      icon: Sparkles,
      badge: 'Unlocked',
      color: 'from-purple-500/20 to-pink-500/5',
      borderColor: 'border-purple-500/30',
      iconColor: 'text-purple-400',
      glow: 'shadow-[0_0_20px_rgba(168,85,247,0.15)]',
    },
  ];

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 glass-panel rounded-2xl border border-white/[0.05]" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 glass-panel rounded-2xl border border-white/[0.05]" />
          <div className="h-96 glass-panel rounded-2xl border border-white/[0.05]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Quick Action Top Ribbon */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl glass-panel border border-white/[0.07]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <TrendingUp size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">Pusat Kendali Cepat</h3>
            <p className="text-xs text-gray-400">Akses langsung ke alur kerja utama admin</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <Link
            href="/draft-dramas"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold transition-all shadow-[0_0_12px_rgba(229,169,60,0.1)]"
          >
            <span>Review Drama Baru</span>
            <ArrowUpRight size={14} />
          </Link>
          <Link
            href="/dramas"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-gray-300 hover:text-white text-xs font-semibold transition-all"
          >
            <Plus size={14} />
            <span>Katalog Drama</span>
          </Link>
          <Link
            href="/push-broadcast"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-gray-300 hover:text-white text-xs font-semibold transition-all"
          >
            <Bell size={14} />
            <span>Push Notif</span>
          </Link>
          <button
            onClick={fetchDashboardData}
            title="Refresh Data"
            className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-gray-400 hover:text-white transition-all"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className={`relative glass-card rounded-2xl p-6 border ${stat.borderColor} overflow-hidden group`}
            >
              <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${stat.color} rounded-full blur-2xl pointer-events-none group-hover:scale-125 transition-transform`} />
              
              <div className="relative z-10 flex items-start justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">{stat.label}</p>
                  <p className="text-3xl font-extrabold text-white mt-1.5 tracking-tight">{stat.value}</p>
                  <p className="text-[11px] text-gray-500 mt-1">{stat.subtext}</p>
                </div>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} border ${stat.borderColor} flex items-center justify-center ${stat.iconColor} ${stat.glow} flex-shrink-0`}>
                  <Icon size={22} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Column Layout: Recent Users & Top Dramas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Users */}
        <div className="glass-card-static rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col">
          <div className="p-5 border-b border-white/[0.07] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Users size={16} />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white tracking-tight">Pengguna Terbaru</h2>
                <p className="text-[11px] text-gray-400">Pendaftaran akun terakhir yang masuk ke database</p>
              </div>
            </div>
            <Link
              href="/users"
              className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 transition-colors"
            >
              <span>Lihat Semua</span>
              <ArrowUpRight size={13} />
            </Link>
          </div>

          <div className="p-5 flex-1">
            {recentUsers.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-xs text-gray-500">Belum ada data pengguna</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentUsers.slice(0, 6).map((user) => {
                  const initial = (user.full_name || user.email || 'U').charAt(0).toUpperCase();
                  return (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] hover:border-white/[0.08] transition-all"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500/20 to-yellow-500/10 border border-amber-500/30 flex items-center justify-center font-bold text-xs text-amber-400 flex-shrink-0">
                          {initial}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-white truncate">
                            {user.full_name || 'Pengguna Tanpa Nama'}
                          </p>
                          <p className="text-[11px] text-gray-500 truncate max-w-[220px]">
                            {user.email || 'ID: ' + user.id.slice(0, 8)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        {user.is_vip ? (
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-bold flex items-center gap-1 shadow-[0_0_8px_rgba(229,169,60,0.15)]">
                            <Crown size={10} /> VIP
                          </span>
                        ) : user.is_banned ? (
                          <span className="px-2.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 text-[10px] font-bold">
                            Banned
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-medium">
                            Aktif
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Top Dramas */}
        <div className="glass-card-static rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col">
          <div className="p-5 border-b border-white/[0.07] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Film size={16} />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white tracking-tight">Drama Terpopuler</h2>
                <p className="text-[11px] text-gray-400">Berdasarkan total penayangan audiens</p>
              </div>
            </div>
            <Link
              href="/dramas"
              className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 transition-colors"
            >
              <span>Katalog Lengkap</span>
              <ArrowUpRight size={13} />
            </Link>
          </div>

          <div className="p-5 flex-1">
            {topDramas.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-xs text-gray-500">Belum ada data drama</p>
              </div>
            ) : (
              <div className="space-y-3">
                {topDramas.slice(0, 6).map((drama, idx) => (
                  <div
                    key={drama.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] hover:border-white/[0.08] transition-all"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 border ${
                        idx === 0
                          ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-[0_0_10px_rgba(229,169,60,0.25)]'
                          : idx === 1
                          ? 'bg-slate-300/20 border-slate-300/40 text-slate-200'
                          : idx === 2
                          ? 'bg-amber-700/20 border-amber-700/40 text-amber-400'
                          : 'bg-white/[0.03] border-white/[0.06] text-gray-500'
                      }`}>
                        #{idx + 1}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white truncate">
                          {drama.title}
                        </p>
                        <p className="text-[11px] text-gray-500 truncate">
                          {drama.total_episodes} Episode Lengkap
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0 text-right">
                      <div className="px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
                        {(drama.view_count || 0).toLocaleString()} <span className="text-[10px] font-normal text-emerald-500/80">views</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
