'use client';

import { supabase, type Profile } from '@/lib/supabase';
import { Ban, CheckCircle, Coins, Crown, Key, Minus, Plus, Search, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function UsersPage() {
    const [search, setSearch] = useState('');
    const [users, setUsers] = useState<Profile[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState<Profile | null>(null);
    const [coinAmount, setCoinAmount] = useState('');
    const [coinReason, setCoinReason] = useState('');
    const [showVipModal, setShowVipModal] = useState(false);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [vipDays, setVipDays] = useState('30');
    const [newPassword, setNewPassword] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

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
            (u.full_name?.toLowerCase() || '').includes(search.toLowerCase()) ||
            (u.email?.toLowerCase() || '').includes(search.toLowerCase())
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

        // Update profiles table (for admin dashboard display)
        await supabase.from('profiles').update({ coin_balance: newBalance }).eq('id', selectedUser.id);

        // Also update user_coins table (for mobile app sync)
        const { data: existingCoins } = await supabase
            .from('user_coins')
            .select('balance')
            .eq('user_id', selectedUser.id)
            .single();

        if (existingCoins) {
            // Update existing record
            await supabase
                .from('user_coins')
                .update({ balance: newBalance })
                .eq('user_id', selectedUser.id);
        } else {
            // Create new record if doesn't exist
            await supabase
                .from('user_coins')
                .insert({ user_id: selectedUser.id, balance: newBalance, total_earned: newBalance });
        }

        // Log transaction
        await supabase.from('coin_transactions').insert({
            user_id: selectedUser.id,
            amount: finalAmount,
            type: add ? 'admin_add' : 'admin_deduct',
            description: coinReason,
        });

        setUsers((prev) =>
            prev.map((u) => (u.id === selectedUser.id ? { ...u, coin_balance: newBalance } : u))
        );

        alert(`${add ? '+' : '-'}${amount} koin ${add ? 'ditambahkan' : 'dikurangi'}. Alasan: ${coinReason}`);
        setCoinAmount('');
        setCoinReason('');
        setSelectedUser(null);
    };

    const grantVip = async () => {
        if (!selectedUser) return;
        setActionLoading(true);

        const days = parseInt(vipDays);
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + days);

        // Insert into subscriptions table
        await supabase.from('subscriptions').insert({
            user_id: selectedUser.id,
            plan_type: 'admin_grant',
            price_paid: 0,
            status: 'active',
            expires_at: expiresAt.toISOString(),
        });

        // Update profile
        await supabase.from('profiles').update({
            is_vip: true,
            vip_expires_at: expiresAt.toISOString(),
        }).eq('id', selectedUser.id);

        setUsers((prev) =>
            prev.map((u) => (u.id === selectedUser.id ? { ...u, is_vip: true, vip_expires_at: expiresAt.toISOString() } : u))
        );

        alert(`VIP diberikan untuk ${days} hari`);
        setActionLoading(false);
        setShowVipModal(false);
        setSelectedUser(null);
    };

    const cancelVip = async (user: Profile) => {
        if (!confirm(`Batalkan VIP untuk ${user.full_name || 'user ini'}?`)) return;

        // Update subscriptions
        await supabase.from('subscriptions')
            .update({ status: 'cancelled' })
            .eq('user_id', user.id)
            .eq('status', 'active');

        // Update profile
        await supabase.from('profiles').update({
            is_vip: false,
            vip_expires_at: null,
        }).eq('id', user.id);

        setUsers((prev) =>
            prev.map((u) => (u.id === user.id ? { ...u, is_vip: false, vip_expires_at: null } : u))
        );

        alert('VIP dibatalkan');
    };

    const resetPassword = async () => {
        if (!selectedUser || !newPassword) return;
        if (newPassword.length < 6) return alert('Password minimal 6 karakter');

        setActionLoading(true);

        // Call API route to reset password (uses service role key on server)
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: selectedUser.id,
                newPassword: newPassword,
            }),
        });

        const result = await response.json();

        if (!response.ok) {
            alert('Gagal reset password: ' + result.error);
        } else {
            alert('Password berhasil direset');
        }

        setActionLoading(false);
        setShowPasswordModal(false);
        setNewPassword('');
        setSelectedUser(null);
    };

    const deleteUser = async () => {
        if (!selectedUser) return;
        setActionLoading(true);

        const response = await fetch('/api/delete-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: selectedUser.id }),
        });

        const result = await response.json();

        if (!response.ok) {
            alert('Gagal hapus user: ' + result.error);
        } else {
            // Remove user from local state
            setUsers((prev) => prev.filter((u) => u.id !== selectedUser.id));
            alert(`User ${selectedUser.email || selectedUser.full_name || 'ini'} berhasil dihapus`);
        }

        setActionLoading(false);
        setShowDeleteModal(false);
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
                            <th className="text-left px-4 py-3 w-12">#</th>
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
                                <td colSpan={6} className="text-center py-8 text-gray-500">
                                    Belum ada user
                                </td>
                            </tr>
                        ) : (
                            filteredUsers.map((user, index) => (
                                <tr key={user.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                                    <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                                    <td className="px-4 py-3">
                                        <p className="font-medium">{user.email || 'No email'}</p>
                                        <p className="text-xs text-gray-500">{user.id.slice(0, 8)}...</p>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="text-yellow-500 font-bold">{user.coin_balance || 0}</span>
                                    </td>
                                    <td className="px-4 py-3">
                                        {user.is_vip ? (
                                            <div>
                                                <span className="bg-yellow-900 text-yellow-400 px-2 py-1 rounded text-xs">VIP</span>
                                                {user.vip_expires_at && (
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {new Date(user.vip_expires_at).toLocaleDateString('id-ID')}
                                                    </p>
                                                )}
                                            </div>
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
                                            {/* Manage Coins */}
                                            <button
                                                onClick={() => setSelectedUser(user)}
                                                className="p-2 hover:bg-yellow-900 rounded text-yellow-400"
                                                title="Manage Coins"
                                            >
                                                <Coins size={18} />
                                            </button>
                                            {/* VIP Toggle */}
                                            {user.is_vip ? (
                                                <button
                                                    onClick={() => cancelVip(user)}
                                                    className="p-2 hover:bg-gray-700 rounded text-gray-400"
                                                    title="Cancel VIP"
                                                >
                                                    <Crown size={18} />
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => { setSelectedUser(user); setShowVipModal(true); }}
                                                    className="p-2 hover:bg-yellow-900 rounded text-yellow-600"
                                                    title="Grant VIP"
                                                >
                                                    <Crown size={18} />
                                                </button>
                                            )}
                                            {/* Reset Password */}
                                            <button
                                                onClick={() => { setSelectedUser(user); setShowPasswordModal(true); }}
                                                className="p-2 hover:bg-blue-900 rounded text-blue-400"
                                                title="Reset Password"
                                            >
                                                <Key size={18} />
                                            </button>
                                            {/* Ban/Unban */}
                                            <button
                                                onClick={() => toggleBan(user)}
                                                className={`p-2 rounded ${user.is_banned ? 'hover:bg-green-900 text-green-400' : 'hover:bg-red-900 text-red-400'}`}
                                                title={user.is_banned ? 'Unban' : 'Ban'}
                                            >
                                                {user.is_banned ? <CheckCircle size={18} /> : <Ban size={18} />}
                                            </button>
                                            {/* Delete User */}
                                            <button
                                                onClick={() => { setSelectedUser(user); setShowDeleteModal(true); }}
                                                className="p-2 hover:bg-red-900 rounded text-red-500"
                                                title="Hapus User"
                                            >
                                                <Trash2 size={18} />
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
            {selectedUser && !showVipModal && !showPasswordModal && !showDeleteModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-gray-800">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold">Manage Koin</h2>
                            <button onClick={() => setSelectedUser(null)} className="text-gray-500 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>
                        <p className="text-gray-400 mb-2">
                            User: {selectedUser.full_name || 'Anonymous'}
                        </p>
                        <p className="text-yellow-500 font-bold mb-4">
                            Saldo: {selectedUser.coin_balance || 0} Koin
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
                        </div>
                    </div>
                </div>
            )}

            {/* VIP Grant Modal */}
            {showVipModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-gray-800">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <Crown className="text-yellow-500" size={24} /> Grant VIP
                            </h2>
                            <button onClick={() => { setShowVipModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>
                        <p className="text-gray-400 mb-4">
                            User: {selectedUser.full_name || 'Anonymous'}
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-gray-400">Durasi VIP (hari)</label>
                                <select
                                    value={vipDays}
                                    onChange={(e) => setVipDays(e.target.value)}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-yellow-600"
                                >
                                    <option value="7">7 hari</option>
                                    <option value="30">30 hari (1 bulan)</option>
                                    <option value="90">90 hari (3 bulan)</option>
                                    <option value="365">365 hari (1 tahun)</option>
                                </select>
                            </div>

                            <button
                                onClick={grantVip}
                                disabled={actionLoading}
                                className="w-full bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {actionLoading ? 'Loading...' : <><Crown size={18} /> Berikan VIP</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Password Reset Modal */}
            {showPasswordModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-gray-800">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <Key className="text-blue-500" size={24} /> Reset Password
                            </h2>
                            <button onClick={() => { setShowPasswordModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>
                        <p className="text-gray-400 mb-4">
                            User: {selectedUser.full_name || 'Anonymous'}
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-gray-400">Password Baru</label>
                                <input
                                    type="password"
                                    placeholder="Minimal 6 karakter"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 mt-1 focus:outline-none focus:border-blue-600"
                                />
                            </div>

                            <button
                                onClick={resetPassword}
                                disabled={actionLoading || newPassword.length < 6}
                                className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {actionLoading ? 'Loading...' : <><Key size={18} /> Reset Password</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete User Modal */}
            {showDeleteModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-red-800">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold flex items-center gap-2 text-red-500">
                                <Trash2 size={24} /> Hapus User
                            </h2>
                            <button onClick={() => { setShowDeleteModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-4">
                            <p className="text-red-400 text-sm font-medium mb-2">⚠️ Peringatan!</p>
                            <p className="text-gray-300 text-sm">
                                Tindakan ini akan menghapus user secara <strong>permanen</strong> beserta semua data terkait:
                            </p>
                            <ul className="text-gray-400 text-xs mt-2 list-disc list-inside space-y-1">
                                <li>Profil dan akun login</li>
                                <li>Saldo koin dan riwayat transaksi</li>
                                <li>Status VIP dan langganan</li>
                                <li>Episode yang sudah di-unlock</li>
                                <li>Riwayat check-in harian</li>
                            </ul>
                        </div>

                        <div className="bg-gray-800 rounded-lg p-3 mb-4">
                            <p className="text-sm text-gray-400">User yang akan dihapus:</p>
                            <p className="font-medium text-white">{selectedUser.email || 'No email'}</p>
                            <p className="text-xs text-gray-500">{selectedUser.full_name || 'Anonymous'} • ID: {selectedUser.id.slice(0, 8)}...</p>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => { setShowDeleteModal(false); setSelectedUser(null); }}
                                className="flex-1 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg"
                            >
                                Batal
                            </button>
                            <button
                                onClick={deleteUser}
                                disabled={actionLoading}
                                className="flex-1 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {actionLoading ? 'Menghapus...' : <><Trash2 size={18} /> Hapus Permanen</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
