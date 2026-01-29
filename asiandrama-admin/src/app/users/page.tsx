'use client';

import { useEffect, useState } from 'react';
import { Search, Ban, CheckCircle, Coins, Plus, Minus } from 'lucide-react';
import { supabase, type Profile } from '@/lib/supabase';

export default function UsersPage() {
    const [search, setSearch] = useState('');
    const [users, setUsers] = useState<Profile[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState<Profile | null>(null);
    const [coinAmount, setCoinAmount] = useState('');
    const [coinReason, setCoinReason] = useState('');

    useEffect(() => {
        fetchUsers();
    }, []);

    async function fetchUsers() {
        setLoading(true);
        const { data } = await supabase
            .from('profiles')
            .select('*')
            .order('created_at', { ascending: false });
        setUsers(data || []);
        setLoading(false);
    }

    const filteredUsers = users.filter(
        (u) =>
            (u.full_name?.toLowerCase() || '').includes(search.toLowerCase())
    );

    const toggleBan = async (user: Profile) => {
        const newBanStatus = !user.is_banned;
        await supabase.from('profiles').update({ is_banned: newBanStatus }).eq('id', user.id);
        setUsers((prev) =>
            prev.map((u) => (u.id === user.id ? { ...u, is_banned: newBanStatus } : u))
        );
    };

    const updateCoins = async (add: boolean) => {
        if (!selectedUser) return;
        const amount = parseInt(coinAmount);
        if (!amount || amount <= 0) return alert('Masukkan jumlah koin yang valid');
        if (!coinReason.trim()) return alert('Masukkan alasan');

        const finalAmount = add ? amount : -amount;
        const newBalance = Math.max(0, selectedUser.coin_balance + finalAmount);

        // Update balance
        await supabase.from('profiles').update({ coin_balance: newBalance }).eq('id', selectedUser.id);

        // Log transaction
        await supabase.from('coin_transactions').insert({
            user_id: selectedUser.id,
            amount: finalAmount,
            reason: coinReason,
        });

        setUsers((prev) =>
            prev.map((u) => (u.id === selectedUser.id ? { ...u, coin_balance: newBalance } : u))
        );

        alert(`${add ? '+' : '-'}${amount} koin ${add ? 'ditambahkan' : 'dikurangi'}. Alasan: ${coinReason}`);
        setCoinAmount('');
        setCoinReason('');
        setSelectedUser(null);
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div>
            <h1 className="text-2xl font-bold mb-6">User Management</h1>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                    type="text"
                    placeholder="Cari user..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-pink-600"
                />
            </div>

            {/* Table */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-800">
                        <tr>
                            <th className="text-left px-4 py-3">User</th>
                            <th className="text-left px-4 py-3">Koin</th>
                            <th className="text-left px-4 py-3">VIP</th>
                            <th className="text-left px-4 py-3">Status</th>
                            <th className="text-left px-4 py-3">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredUsers.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="text-center py-8 text-gray-500">
                                    Belum ada user
                                </td>
                            </tr>
                        ) : (
                            filteredUsers.map((user) => (
                                <tr key={user.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                                    <td className="px-4 py-3">
                                        <p className="font-medium">{user.full_name || 'Anonymous'}</p>
                                        <p className="text-xs text-gray-500">{user.id.slice(0, 8)}...</p>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="text-yellow-500 font-bold">{user.coin_balance}</span>
                                    </td>
                                    <td className="px-4 py-3">
                                        {user.is_vip ? (
                                            <span className="bg-yellow-900 text-yellow-400 px-2 py-1 rounded text-xs">VIP</span>
                                        ) : (
                                            <span className="text-gray-500">-</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span
                                            className={`px-2 py-1 rounded text-xs ${user.is_banned ? 'bg-red-900 text-red-400' : 'bg-green-900 text-green-400'
                                                }`}
                                        >
                                            {user.is_banned ? 'Banned' : 'Active'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => setSelectedUser(user)}
                                                className="p-2 hover:bg-yellow-900 rounded text-yellow-400"
                                                title="Manage Coins"
                                            >
                                                <Coins size={18} />
                                            </button>
                                            <button
                                                onClick={() => toggleBan(user)}
                                                className={`p-2 rounded ${user.is_banned ? 'hover:bg-green-900 text-green-400' : 'hover:bg-red-900 text-red-400'}`}
                                                title={user.is_banned ? 'Unban' : 'Ban'}
                                            >
                                                {user.is_banned ? <CheckCircle size={18} /> : <Ban size={18} />}
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Coin Management Modal */}
            {selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-gray-800">
                        <h2 className="text-xl font-bold mb-4">Manage Koin</h2>
                        <p className="text-gray-400 mb-2">
                            User: {selectedUser.full_name || 'Anonymous'}
                        </p>
                        <p className="text-yellow-500 font-bold mb-4">
                            Saldo: {selectedUser.coin_balance} Koin
                        </p>

                        <div className="space-y-4">
                            <input
                                type="number"
                                placeholder="Jumlah koin"
                                value={coinAmount}
                                onChange={(e) => setCoinAmount(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-600"
                            />
                            <input
                                type="text"
                                placeholder="Alasan (wajib)"
                                value={coinReason}
                                onChange={(e) => setCoinReason(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-600"
                            />

                            <div className="flex gap-3">
                                <button
                                    onClick={() => updateCoins(true)}
                                    className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                                >
                                    <Plus size={18} /> Tambah
                                </button>
                                <button
                                    onClick={() => updateCoins(false)}
                                    className="flex-1 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                                >
                                    <Minus size={18} /> Kurangi
                                </button>
                            </div>

                            <button
                                onClick={() => setSelectedUser(null)}
                                className="w-full bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg"
                            >
                                Tutup
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
