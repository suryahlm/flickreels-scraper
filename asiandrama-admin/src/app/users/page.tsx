'use client';

import { supabase, type Profile } from '@/lib/supabase';
import { Ban, CheckCircle, Coins, Crown, Key, Minus, Plus, Search, Trash2, X, Users, ShieldAlert, ShieldCheck, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import { cancelUserVipAdmin, grantUserVipAdmin, toggleUserBanAdmin, updateUserCoinsAdmin } from './actions';

export default function UsersPage() {
    const [search, setSearch] = useState('');
    const [users, setUsers] = useState<Profile[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Pagination & Filters
    const [page, setPage] = useState(1);
    const [pageSize] = useState(30);
    const [filterVip, setFilterVip] = useState(false);
    const [filterBanned, setFilterBanned] = useState(false);
    const [sortByCoins, setSortByCoins] = useState(false);
    const [hasMore, setHasMore] = useState(false);
    const [selectedUser, setSelectedUser] = useState<Profile | null>(null);
    const [coinAmount, setCoinAmount] = useState('');
    const [coinReason, setCoinReason] = useState('');
    const [showVipModal, setShowVipModal] = useState(false);
    const [showPasswordModal, setShowPasswordModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [vipDays, setVipDays] = useState('30');
    const [customVipDays, setCustomVipDays] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            fetchUsers();
        }, 300);
        return () => clearTimeout(timer);
    }, [page, filterVip, filterBanned, sortByCoins, search]);

    async function fetchUsers() {
        setLoading(true);
        let query = supabase.from('profiles').select('*', { count: 'exact' });

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
            console.error(error);
        } else {
            setUsers(data || []);
            setHasMore(count ? from + (data?.length || 0) < count : false);
        }
        setLoading(false);
    }

    const handleFilterChange = (setter: any, value: any) => {
        setter(value);
        setPage(1);
    };

    const handleSearchChange = (val: string) => {
        setSearch(val);
        setPage(1);
    };

    const toggleBan = async (user: Profile) => {
        const newBanStatus = !user.is_banned;
        const result = await toggleUserBanAdmin(user.id, newBanStatus);
        
        if (result.success) {
            setUsers((prev) =>
                prev.map((u) => (u.id === user.id ? { ...u, is_banned: newBanStatus } : u))
            );
        } else {
            alert('Gagal update: ' + result.error);
        }
    };

    const updateCoins = async (add: boolean) => {
        if (!selectedUser) return;
        const amount = parseInt(coinAmount);
        if (!amount || amount <= 0) return alert('Masukkan jumlah koin yang valid');
        if (!coinReason.trim()) return alert('Masukkan alasan');

        const result = await updateUserCoinsAdmin(selectedUser.id, amount, coinReason, add);

        if (result.success) {
            setUsers((prev) =>
                prev.map((u) => (u.id === selectedUser.id ? { ...u, coin_balance: result.newBalance! } : u))
            );
            alert(`${add ? '+' : '-'}${amount} koin ${add ? 'ditambahkan' : 'dikurangi'}.`);
        } else {
            alert('Gagal update koin: ' + result.error);
        }

        setCoinAmount('');
        setCoinReason('');
        setSelectedUser(null);
    };

    const grantVip = async () => {
        if (!selectedUser) return;
        setActionLoading(true);

        const days = vipDays === 'custom' ? parseInt(customVipDays) : parseInt(vipDays);
        if (isNaN(days) || days <= 0) {
            alert("Masukkan jumlah hari yang valid");
            setActionLoading(false);
            return;
        }
        const result = await grantUserVipAdmin(selectedUser.id, days);

        if (result.success) {
            setUsers((prev) =>
                prev.map((u) => (u.id === selectedUser.id ? { ...u, is_vip: true, vip_expires_at: result.expiresIso! } : u))
            );
            alert(`VIP diberikan untuk ${days} hari`);
        } else {
            alert('Gagal memberikan VIP: ' + result.error);
        }

        setActionLoading(false);
        setShowVipModal(false);
        setSelectedUser(null);
    };

    const cancelVip = async (user: Profile) => {
        if (!confirm(`Batalkan VIP untuk ${user.full_name || 'user ini'}?`)) return;

        const result = await cancelUserVipAdmin(user.id);

        if (result.success) {
            setUsers((prev) =>
                prev.map((u) => (u.id === user.id ? { ...u, is_vip: false, vip_expires_at: null } : u))
            );
            alert('VIP dibatalkan');
        } else {
            alert('Gagal membatalkan VIP: ' + result.error);
        }
    };

    const resetPassword = async () => {
        if (!selectedUser || !newPassword) return;
        if (newPassword.length < 6) return alert('Password minimal 6 karakter');

        setActionLoading(true);
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
            setUsers((prev) => prev.filter((u) => u.id !== selectedUser.id));
            alert(`User ${selectedUser.email || selectedUser.full_name || 'ini'} berhasil dihapus`);
        }

        setActionLoading(false);
        setShowDeleteModal(false);
        setSelectedUser(null);
    };

    return (
        <div className="space-y-6">
            {/* Header Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/[0.08]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <Users size={20} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Direktori Pengguna Platform</h2>
                        <p className="text-xs text-gray-400">Kelola akun terdaftar, status VIP, saldo koin, dan moderasi akses</p>
                    </div>
                </div>
            </div>

            {/* Search & Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                        type="text"
                        placeholder="Cari berdasarkan email atau nama pengguna..."
                        value={search}
                        onChange={(e) => handleSearchChange(e.target.value)}
                        className="w-full glass-input rounded-2xl pl-12 pr-4 py-3 text-xs focus:border-amber-400"
                    />
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    <button 
                        onClick={() => handleFilterChange(setFilterVip, !filterVip)} 
                        className={`px-3.5 py-2.5 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                            filterVip
                                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-[0_0_12px_rgba(229,169,60,0.2)]'
                                : 'bg-white/[0.03] border-white/[0.06] text-gray-400 hover:text-white'
                        }`}
                    >
                        VIP
                    </button>
                    <button 
                        onClick={() => handleFilterChange(setSortByCoins, !sortByCoins)} 
                        className={`px-3.5 py-2.5 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                            sortByCoins
                                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 shadow-[0_0_12px_rgba(229,169,60,0.2)]'
                                : 'bg-white/[0.03] border-white/[0.06] text-gray-400 hover:text-white'
                        }`}
                    >
                        Koin Terbanyak
                    </button>
                    <button 
                        onClick={() => handleFilterChange(setFilterBanned, !filterBanned)} 
                        className={`px-3.5 py-2.5 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                            filterBanned
                                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 shadow-[0_0_12px_rgba(239,68,68,0.2)]'
                                : 'bg-white/[0.03] border-white/[0.06] text-gray-400 hover:text-white'
                        }`}
                    >
                        Banned
                    </button>
                </div>
            </div>

            {/* Users Data Table */}
            <div className="glass-card-static rounded-2xl border border-white/[0.08] overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white/[0.02] border-b border-white/[0.07] text-[11px] font-bold uppercase tracking-wider text-gray-400">
                                <th className="px-5 py-4 w-12">#</th>
                                <th className="px-5 py-4">Pengguna</th>
                                <th className="px-5 py-4">Saldo Koin</th>
                                <th className="px-5 py-4">Status VIP</th>
                                <th className="px-5 py-4">Akun Status</th>
                                <th className="px-5 py-4 text-right">Tindakan Moderasi</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04]">
                            {loading && users.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-16 text-xs text-gray-500">
                                        Memuat data pengguna...
                                    </td>
                                </tr>
                            ) : users.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-16 text-xs text-gray-500">
                                        Belum ada user yang cocok dengan kriteria pencarian
                                    </td>
                                </tr>
                            ) : (
                                users.map((user, index) => {
                                    const initial = (user.full_name || user.email || 'U').charAt(0).toUpperCase();
                                    return (
                                        <tr key={user.id} className="hover:bg-white/[0.03] transition-colors group">
                                            <td className="px-5 py-4 text-xs font-mono text-gray-500">
                                                {(page - 1) * pageSize + index + 1}
                                            </td>
                                            <td className="px-5 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500/20 to-yellow-500/10 border border-amber-500/30 flex items-center justify-center font-bold text-xs text-amber-400 flex-shrink-0">
                                                        {initial}
                                                    </div>
                                                    <div className="min-w-0">
                                                        <p className="text-xs font-bold text-white truncate group-hover:text-amber-300 transition-colors">
                                                            {user.full_name || 'Anonymous User'}
                                                        </p>
                                                        <p className="text-[11px] text-gray-400 truncate max-w-[220px]">
                                                            {user.email || 'Tanpa Email'}
                                                        </p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-5 py-4">
                                                <span className="text-xs font-bold text-amber-400">
                                                    {(user.coin_balance || 0).toLocaleString()} <span className="text-[10px] font-normal text-gray-500">koin</span>
                                                </span>
                                            </td>
                                            <td className="px-5 py-4">
                                                {user.is_vip ? (
                                                    <div>
                                                        <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-bold flex items-center gap-1 w-max shadow-[0_0_8px_rgba(229,169,60,0.15)]">
                                                            <Crown size={10} /> VIP
                                                        </span>
                                                        {user.vip_expires_at && (
                                                            <p className="text-[10px] text-gray-500 mt-1">
                                                                Exp: {new Date(user.vip_expires_at).toLocaleDateString('id-ID')}
                                                            </p>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-gray-600">-</span>
                                                )}
                                            </td>
                                            <td className="px-5 py-4">
                                                <span
                                                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                                                        user.is_banned
                                                            ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                                                            : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                                    }`}
                                                >
                                                    {user.is_banned ? 'Banned' : 'Active'}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 text-right">
                                                <div className="flex items-center justify-end gap-1.5">
                                                    {/* Manage Coins */}
                                                    <button
                                                        onClick={() => setSelectedUser(user)}
                                                        className="p-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 transition-all"
                                                        title="Kelola Saldo Koin"
                                                    >
                                                        <Coins size={14} />
                                                    </button>

                                                    {/* VIP Toggle */}
                                                    {user.is_vip ? (
                                                        <button
                                                            onClick={() => cancelVip(user)}
                                                            className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-gray-400 hover:text-white border border-white/[0.06] transition-all"
                                                            title="Batalkan Akses VIP"
                                                        >
                                                            <Crown size={14} />
                                                        </button>
                                                    ) : (
                                                        <button
                                                            onClick={() => { setSelectedUser(user); setShowVipModal(true); }}
                                                            className="p-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 transition-all"
                                                            title="Berikan Akses VIP"
                                                        >
                                                            <Crown size={14} />
                                                        </button>
                                                    )}

                                                    {/* Reset Password */}
                                                    <button
                                                        onClick={() => { setSelectedUser(user); setShowPasswordModal(true); }}
                                                        className="p-2 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 transition-all"
                                                        title="Reset Kata Sandi"
                                                    >
                                                        <Key size={14} />
                                                    </button>

                                                    {/* Ban / Unban */}
                                                    <button
                                                        onClick={() => toggleBan(user)}
                                                        className={`p-2 rounded-xl border transition-all ${
                                                            user.is_banned
                                                                ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/20'
                                                                : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border-rose-500/20'
                                                        }`}
                                                        title={user.is_banned ? 'Buka Blokir (Unban)' : 'Blokir Akun (Ban)'}
                                                    >
                                                        {user.is_banned ? <CheckCircle size={14} /> : <Ban size={14} />}
                                                    </button>

                                                    {/* Delete User */}
                                                    <button
                                                        onClick={() => { setSelectedUser(user); setShowDeleteModal(true); }}
                                                        className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-all"
                                                        title="Hapus Akun Permanen"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-between items-center px-1">
                <button 
                    disabled={page === 1 || loading} 
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                    <ChevronLeft size={14} /> Sebelumnya
                </button>
                <div className="text-xs text-gray-400 font-medium">
                    Halaman <strong className="text-white">{page}</strong>
                </div>
                <button 
                    disabled={!hasMore || loading} 
                    onClick={() => setPage(p => p + 1)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                    Berikutnya <ChevronRight size={14} />
                </button>
            </div>

            {/* Coin Management Luxury Modal */}
            {selectedUser && !showVipModal && !showPasswordModal && !showDeleteModal && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-white/[0.1] rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center pb-4 mb-4 border-b border-white/[0.07]">
                            <div className="flex items-center gap-2">
                                <Coins className="text-amber-400" size={20} />
                                <h3 className="text-base font-bold text-white tracking-tight">Kelola Saldo Koin</h3>
                            </div>
                            <button onClick={() => setSelectedUser(null)} className="text-gray-500 hover:text-white">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-4">
                            <p className="text-xs text-gray-400">Pengguna: <strong className="text-white">{selectedUser.full_name || 'Anonymous'}</strong></p>
                            <p className="text-xs font-bold text-amber-400 mt-1">Saldo Saat Ini: {(selectedUser.coin_balance || 0).toLocaleString()} Koin</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Jumlah Koin</label>
                                <input
                                    type="number"
                                    placeholder="Contoh: 100"
                                    value={coinAmount}
                                    onChange={(e) => setCoinAmount(e.target.value)}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-xs focus:border-amber-400"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Alasan (Wajib)</label>
                                <input
                                    type="text"
                                    placeholder="Alasan penyesuaian koin..."
                                    value={coinReason}
                                    onChange={(e) => setCoinReason(e.target.value)}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-xs focus:border-amber-400"
                                />
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => updateCoins(true)}
                                    className="flex-1 py-2.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-bold flex items-center justify-center gap-2"
                                >
                                    <Plus size={16} /> Tambah Koin
                                </button>
                                <button
                                    onClick={() => updateCoins(false)}
                                    className="flex-1 py-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-bold flex items-center justify-center gap-2"
                                >
                                    <Minus size={16} /> Kurangi Koin
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* VIP Grant Modal */}
            {showVipModal && selectedUser && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-white/[0.1] rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center pb-4 mb-4 border-b border-white/[0.07]">
                            <div className="flex items-center gap-2">
                                <Crown className="text-amber-400" size={20} />
                                <h3 className="text-base font-bold text-white tracking-tight">Berikan Akses VIP</h3>
                            </div>
                            <button onClick={() => { setShowVipModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-4">
                            <p className="text-xs text-gray-400">Pengguna: <strong className="text-white">{selectedUser.full_name || selectedUser.email}</strong></p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Durasi VIP (Hari)</label>
                                <select
                                    value={vipDays}
                                    onChange={(e) => setVipDays(e.target.value)}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-xs focus:border-amber-400"
                                >
                                    <option value="7" className="bg-[#090D15]">7 Hari</option>
                                    <option value="30" className="bg-[#090D15]">30 Hari (1 Bulan)</option>
                                    <option value="90" className="bg-[#090D15]">90 Hari (3 Bulan)</option>
                                    <option value="365" className="bg-[#090D15]">365 Hari (1 Tahun)</option>
                                    <option value="custom" className="bg-[#090D15]">Custom (Isi Manual)</option>
                                </select>
                                
                                {vipDays === 'custom' && (
                                    <input
                                        type="number"
                                        min="1"
                                        placeholder="Ketik jumlah hari..."
                                        value={customVipDays}
                                        onChange={(e) => setCustomVipDays(e.target.value)}
                                        className="w-full glass-input rounded-xl px-4 py-2.5 text-xs focus:border-amber-400 mt-2"
                                    />
                                )}
                            </div>

                            <button
                                onClick={grantVip}
                                disabled={actionLoading}
                                className="w-full gold-btn py-3 rounded-xl text-xs font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {actionLoading ? 'Memproses...' : <><Crown size={15} /> Berikan VIP Sekarang</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Password Reset Modal */}
            {showPasswordModal && selectedUser && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-white/[0.1] rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center pb-4 mb-4 border-b border-white/[0.07]">
                            <div className="flex items-center gap-2">
                                <Key className="text-blue-400" size={20} />
                                <h3 className="text-base font-bold text-white tracking-tight">Reset Kata Sandi User</h3>
                            </div>
                            <button onClick={() => { setShowPasswordModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-4">
                            <p className="text-xs text-gray-400">Pengguna: <strong className="text-white">{selectedUser.full_name || selectedUser.email}</strong></p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Password Baru</label>
                                <input
                                    type="password"
                                    placeholder="Minimal 6 karakter"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-xs focus:border-blue-400"
                                />
                            </div>

                            <button
                                onClick={resetPassword}
                                disabled={actionLoading || newPassword.length < 6}
                                className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold flex items-center justify-center gap-2 disabled:opacity-50 transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                            >
                                {actionLoading ? 'Memproses...' : <><Key size={15} /> Setel Password Baru</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete User Modal */}
            {showDeleteModal && selectedUser && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-rose-500/30 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center pb-4 mb-4 border-b border-white/[0.07]">
                            <div className="flex items-center gap-2 text-rose-400 font-bold">
                                <Trash2 size={20} />
                                <h3 className="text-base text-white tracking-tight">Hapus Akun Pengguna</h3>
                            </div>
                            <button onClick={() => { setShowDeleteModal(false); setSelectedUser(null); }} className="text-gray-500 hover:text-white">
                                <X size={18} />
                            </button>
                        </div>

                        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs mb-4 leading-relaxed">
                            ⚠️ Tindakan ini akan menghapus akun user secara permanen beserta riwayat tontonan dan saldonya.
                        </div>

                        <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-6">
                            <p className="text-xs text-gray-400">Akun: <strong className="text-white">{selectedUser.email || 'Tanpa Email'}</strong></p>
                            <p className="text-[11px] text-gray-500 mt-0.5 font-mono">ID: {selectedUser.id}</p>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => { setShowDeleteModal(false); setSelectedUser(null); }}
                                className="flex-1 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white text-xs font-semibold"
                            >
                                Batal
                            </button>
                            <button
                                onClick={deleteUser}
                                disabled={actionLoading}
                                className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-[0_0_15px_rgba(239,68,68,0.3)] disabled:opacity-50"
                            >
                                {actionLoading ? 'Menghapus...' : 'Ya, Hapus Akun'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
