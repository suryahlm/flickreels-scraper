'use client';

import { supabaseAdmin } from '@/lib/supabase';
import { useEffect, useState } from 'react';

interface Notification {
    id: string;
    title: string;
    message: string;
    type: 'info' | 'warning' | 'maintenance';
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    // Form state
    const [title, setTitle] = useState('');
    const [message, setMessage] = useState('');
    const [type, setType] = useState<'info' | 'warning' | 'maintenance'>('info');

    const fetchNotifications = async () => {
        const { data, error } = await supabaseAdmin
            .from('admin_notifications')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(20);

        if (!error && data) {
            setNotifications(data);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchNotifications();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim() || !message.trim()) return;

        setSubmitting(true);
        try {
            const { error } = await supabaseAdmin
                .from('admin_notifications')
                .insert({
                    title: title.trim(),
                    message: message.trim(),
                    type,
                    is_active: true,
                });

            if (error) {
                alert('Gagal mengirim notifikasi: ' + error.message);
            } else {
                setTitle('');
                setMessage('');
                setType('info');
                await fetchNotifications();
            }
        } catch (err) {
            alert('Error: ' + err);
        }
        setSubmitting(false);
    };

    const handleDeactivate = async (id: string) => {
        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .update({ is_active: false, updated_at: new Date().toISOString() })
            .eq('id', id);

        if (!error) {
            await fetchNotifications();
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Yakin hapus notifikasi ini?')) return;

        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .delete()
            .eq('id', id);

        if (!error) {
            await fetchNotifications();
        }
    };

    const getTypeBadge = (type: string) => {
        const styles: Record<string, string> = {
            info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
            maintenance: 'bg-red-500/20 text-red-400 border-red-500/30',
        };
        const icons: Record<string, string> = {
            info: '📢',
            warning: '⚠️',
            maintenance: '🔧',
        };
        return (
            <span className={`px-2 py-1 rounded-full text-xs border ${styles[type] || styles.info}`}>
                {icons[type]} {type}
            </span>
        );
    };

    const activeNotification = notifications.find(n => n.is_active);

    return (
        <div className="p-6 max-w-5xl">
            <h1 className="text-2xl font-bold text-white mb-6">📢 Notifikasi Admin</h1>

            {/* Active Notification Preview */}
            {activeNotification && (
                <div className="mb-6 p-4 rounded-lg border border-amber-500/30 bg-amber-500/10">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-amber-400 font-semibold text-sm">🔔 NOTIFIKASI AKTIF</h3>
                        <button
                            onClick={() => handleDeactivate(activeNotification.id)}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                        >
                            Nonaktifkan
                        </button>
                    </div>
                    <p className="text-white font-medium">{activeNotification.title}</p>
                    <p className="text-gray-300 text-sm mt-1">{activeNotification.message}</p>
                    <div className="mt-2 flex items-center gap-2">
                        {getTypeBadge(activeNotification.type)}
                        <span className="text-gray-500 text-xs">
                            {new Date(activeNotification.created_at).toLocaleString('id-ID')}
                        </span>
                    </div>
                </div>
            )}

            {/* Create New Notification Form */}
            <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
                <h2 className="text-lg font-semibold text-white mb-4">Buat Notifikasi Baru</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Judul</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Contoh: Maintenance Server"
                            className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:border-amber-500 focus:outline-none"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Pesan</label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Contoh: Server akan maintenance jam 22:00 - 02:00 WIB"
                            rows={3}
                            className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:border-amber-500 focus:outline-none resize-none"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Tipe</label>
                        <select
                            value={type}
                            onChange={(e) => setType(e.target.value as 'info' | 'warning' | 'maintenance')}
                            className="w-full px-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:border-amber-500 focus:outline-none"
                        >
                            <option value="info">📢 Info — Pengumuman umum</option>
                            <option value="warning">⚠️ Warning — Peringatan penting</option>
                            <option value="maintenance">🔧 Maintenance — Jadwal maintenance</option>
                        </select>
                    </div>

                    <button
                        type="submit"
                        disabled={submitting || !title.trim() || !message.trim()}
                        className="px-6 py-2 bg-gradient-to-r from-amber-500 to-yellow-600 text-white font-semibold rounded-lg hover:from-amber-600 hover:to-yellow-700 disabled:opacity-50 transition-all"
                    >
                        {submitting ? 'Mengirim...' : '🚀 Kirim Notifikasi'}
                    </button>

                    <p className="text-xs text-gray-500">
                        * Mengirim notifikasi baru akan otomatis menonaktifkan notifikasi sebelumnya
                    </p>
                </form>
            </div>

            {/* History Table */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                    <h2 className="text-lg font-semibold text-white">Riwayat Notifikasi</h2>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading...</div>
                ) : notifications.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">Belum ada notifikasi</div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-gray-900/50">
                            <tr>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Status</th>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Tipe</th>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Judul</th>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Pesan</th>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Waktu</th>
                                <th className="text-left px-4 py-3 text-sm text-gray-400">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {notifications.map((notif) => (
                                <tr key={notif.id} className="border-t border-gray-700/50 hover:bg-gray-700/20">
                                    <td className="px-4 py-3">
                                        {notif.is_active ? (
                                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                                                ● Aktif
                                            </span>
                                        ) : (
                                            <span className="px-2 py-1 bg-gray-600/20 text-gray-500 text-xs rounded-full border border-gray-600/30">
                                                ○ Nonaktif
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3">{getTypeBadge(notif.type)}</td>
                                    <td className="px-4 py-3 text-white text-sm font-medium">{notif.title}</td>
                                    <td className="px-4 py-3 text-gray-300 text-sm max-w-xs truncate">{notif.message}</td>
                                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                                        {new Date(notif.created_at).toLocaleString('id-ID')}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex gap-2">
                                            {notif.is_active && (
                                                <button
                                                    onClick={() => handleDeactivate(notif.id)}
                                                    className="px-2 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs rounded transition-colors"
                                                >
                                                    Nonaktifkan
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDelete(notif.id)}
                                                className="px-2 py-1 bg-red-600/50 hover:bg-red-600 text-white text-xs rounded transition-colors"
                                            >
                                                Hapus
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
