'use client';

import { useEffect, useState } from 'react';
import { Film, Users, Eye, Coins } from 'lucide-react';
import { supabase, type Drama, type Profile } from '@/lib/supabase';

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
      // Fetch drama count
      const { count: dramaCount } = await supabase
        .from('dramas')
        .select('*', { count: 'exact', head: true });

      // Fetch user count
      const { count: userCount } = await supabase
        .from('profiles')
        .select('*', { count: 'exact', head: true });

      // Fetch total views
      const { data: viewData } = await supabase
        .from('dramas')
        .select('view_count');
      const totalViews = viewData?.reduce((sum, d) => sum + (d.view_count || 0), 0) || 0;

      // Fetch total coins
      const { data: coinData } = await supabase
        .from('profiles')
        .select('coin_balance');
      const totalCoins = coinData?.reduce((sum, p) => sum + (p.coin_balance || 0), 0) || 0;

      setStats({
        totalDramas: dramaCount || 0,
        totalUsers: userCount || 0,
        totalViews,
        totalCoins,
      });

      // Fetch recent users
      const { data: users } = await supabase
        .from('profiles')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5);
      setRecentUsers(users || []);

      // Fetch top dramas
      const { data: dramas } = await supabase
        .from('dramas')
        .select('*')
        .order('view_count', { ascending: false })
        .limit(5);
      setTopDramas(dramas || []);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }

  const statCards = [
    { label: 'Total Drama', value: stats.totalDramas.toLocaleString(), icon: Film, color: 'bg-amber-500' },
    { label: 'Total Users', value: stats.totalUsers.toLocaleString(), icon: Users, color: 'bg-blue-600' },
    { label: 'Total Views', value: stats.totalViews.toLocaleString(), icon: Eye, color: 'bg-green-600' },
    { label: 'Total Koin', value: stats.totalCoins.toLocaleString(), icon: Coins, color: 'bg-yellow-600' },
  ];

  if (loading) {
    return <div className="text-center py-20">Loading...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="bg-gray-900 rounded-xl p-6 border border-gray-800"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon size={24} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                    <th className="text-left pb-3">Koin</th>
                    <th className="text-left pb-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentUsers.map((user) => (
                    <tr key={user.id} className="border-t border-gray-800">
                      <td className="py-3">
                        <p className="font-medium">{user.full_name || 'Anonymous'}</p>
                      </td>
                      <td className="py-3 text-yellow-500">{user.coin_balance}</td>
                      <td className="py-3">
                        {user.is_vip && <span className="bg-yellow-900 text-yellow-400 px-2 py-1 rounded text-xs">VIP</span>}
                        {user.is_banned && <span className="bg-red-900 text-red-400 px-2 py-1 rounded text-xs ml-1">Banned</span>}
                        {!user.is_vip && !user.is_banned && <span className="text-gray-500">-</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Top Dramas */}
        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800">
            <h2 className="font-semibold">Drama Terpopuler</h2>
          </div>
          <div className="p-4">
            {topDramas.length === 0 ? (
              <p className="text-gray-500 text-center py-4">Belum ada drama</p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="text-gray-400 text-sm">
                    <th className="text-left pb-3">#</th>
                    <th className="text-left pb-3">Judul</th>
                    <th className="text-left pb-3">Views</th>
                    <th className="text-left pb-3">Eps</th>
                  </tr>
                </thead>
                <tbody>
                  {topDramas.map((drama, idx) => (
                    <tr key={drama.id} className="border-t border-gray-800">
                      <td className="py-3 text-pink-500 font-bold">{idx + 1}</td>
                      <td className="py-3 font-medium">{drama.title}</td>
                      <td className="py-3 text-gray-400">{drama.view_count?.toLocaleString()}</td>
                      <td className="py-3 text-gray-400">{drama.total_episodes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
