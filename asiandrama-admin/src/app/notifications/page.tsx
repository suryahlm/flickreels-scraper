'use client';

import { supabaseAdmin } from '@/lib/supabase';
import { useEffect, useState } from 'react';
import { 
    Megaphone, 
    Bell, 
    AlertTriangle, 
    Wrench, 
    Info, 
    CheckCircle2, 
    Trash2, 
    PowerOff, 
    Send, 
    Clock, 
    Sparkles, 
    Smartphone, 
    Radio 
} from 'lucide-react';

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
    const [actionId, setActionId] = useState<string | null>(null);

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
        } catch (err: any) {
            alert('Error: ' + (err.message || err));
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeactivate = async (id: string) => {
        setActionId(id);
        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .update({ is_active: false, updated_at: new Date().toISOString() })
            .eq('id', id);

        if (!error) {
            await fetchNotifications();
        }
        setActionId(null);
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Hapus notifikasi ini dari arsip riwayat?')) return;

        setActionId(id);
        const { error } = await supabaseAdmin
            .from('admin_notifications')
            .delete()
            .eq('id', id);

        if (!error) {
            await fetchNotifications();
        }
        setActionId(null);
    };

    const getTypeMeta = (t: string) => {
        switch (t) {
            case 'warning':
                return {
                    label: 'Warning Peringatan',
                    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                    icon: AlertTriangle,
                    accentColor: 'text-amber-400',
                    boxBg: 'bg-amber-500/10 border-amber-500/20'
                };
            case 'maintenance':
                return {
                    label: 'Maintenance Sistem',
                    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
                    icon: Wrench,
                    accentColor: 'text-rose-400',
                    boxBg: 'bg-rose-500/10 border-rose-500/20'
                };
            default:
                return {
                    label: 'Informasi Umum',
                    badge: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
                    icon: Info,
                    accentColor: 'text-sky-400',
                    boxBg: 'bg-sky-500/10 border-sky-500/20'
                };
        }
    };

    const activeNotification = notifications.find(n => n.is_active);

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-16">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-white/[0.06] gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                        <span className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                            <Megaphone size={20} />
                        </span>
                        <h1 className="text-2xl font-bold tracking-tight text-white">In-App Announcement Studio</h1>
                    </div>
                    <p className="text-xs text-slate-400">
                        Siarkan pengumuman pop-up langsung ke dalam aplikasi mobile (Info update, promo koin, jadwal maintenance server).
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    {activeNotification ? (
                        <div className="px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                            1 Pengumuman Sedang Mengudara
                        </div>
                    ) : (
                        <div className="px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-slate-400 text-xs font-semibold flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-slate-500" />
                            Tidak Ada Siaran Aktif
                        </div>
                    )}
                </div>
            </div>

            {/* Active Notification Hero Spotlight */}
            {activeNotification && (
                <div className="glass-panel p-6 sm:p-7 relative overflow-hidden border border-amber-500/30 bg-gradient-to-r from-amber-500/[0.05] via-transparent to-transparent">
                    <div className="absolute top-0 right-0 w-96 h-40 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
                    
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="space-y-3 max-w-3xl">
                            <div className="flex items-center gap-2.5">
                                <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                    <Radio size={12} className="animate-pulse" /> LIVE BROADCAST
                                </span>
                                {(() => {
                                    const meta = getTypeMeta(activeNotification.type);
                                    const Icon = meta.icon;
                                    return (
                                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border flex items-center gap-1 ${meta.badge}`}>
                                            <Icon size={11} /> {meta.label}
                                        </span>
                                    );
                                })()}
                                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                                    <Clock size={11} />
                                    {new Date(activeNotification.created_at).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' })}
                                </span>
                            </div>

                            <div>
                                <h3 className="text-lg font-bold text-white tracking-tight">{activeNotification.title}</h3>
                                <p className="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed whitespace-pre-line">
                                    {activeNotification.message}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 self-start md:self-center">
                            <button
                                onClick={() => handleDeactivate(activeNotification.id)}
                                disabled={actionId === activeNotification.id}
                                className="px-4 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:text-rose-300 text-xs font-bold flex items-center gap-2 transition-all"
                            >
                                <PowerOff size={14} /> Nonaktifkan Siaran
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Composer and Live Preview Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Form Column */}
                <div className="lg:col-span-7">
                    <div className="glass-panel p-6 sm:p-7 space-y-6">
                        <div className="pb-4 border-b border-white/[0.06]">
                            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                                <Sparkles size={16} className="text-amber-400" /> Buat Pengumuman Baru
                            </h2>
                            <p className="text-xs text-slate-400 mt-1">
                                Tulis judul dan isi pesan. Ketika diterbitkan, pengumuman lama akan otomatis digantikan.
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Type selector */}
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-2">
                                    Tipe Pengumuman
                                </label>
                                <div className="grid grid-cols-3 gap-2.5">
                                    {(['info', 'warning', 'maintenance'] as const).map((t) => {
                                        const isSelected = type === t;
                                        const meta = getTypeMeta(t);
                                        const Icon = meta.icon;
                                        return (
                                            <button
                                                key={t}
                                                type="button"
                                                onClick={() => setType(t)}
                                                className={`p-3 rounded-xl border text-left transition-all flex flex-col gap-1.5 ${
                                                    isSelected
                                                        ? 'bg-amber-500/10 border-amber-500/40 text-amber-300 shadow-md'
                                                        : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:bg-white/[0.04]'
                                                }`}
                                            >
                                                <div className="flex items-center gap-1.5 font-bold text-xs">
                                                    <Icon size={14} className={meta.accentColor} />
                                                    <span className="capitalize">{t}</span>
                                                </div>
                                                <span className="text-[10px] text-slate-500 leading-tight">
                                                    {t === 'info' ? 'Pengumuman umum' : t === 'warning' ? 'Peringatan penting' : 'Jadwal maintenance'}
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Title */}
                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <label className="text-xs font-semibold text-slate-300">Judul Pengumuman</label>
                                    <span className="text-[11px] text-slate-500">{title.length} karakter</span>
                                </div>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="Contoh: Pemeliharaan Server AsianDrama"
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors"
                                    required
                                />
                            </div>

                            {/* Message */}
                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <label className="text-xs font-semibold text-slate-300">Isi Pesan Detail</label>
                                    <span className="text-[11px] text-slate-500">{message.length} karakter</span>
                                </div>
                                <textarea
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    placeholder="Contoh: Halo Sahabat AsianDrama! Server kami akan mengalami pemeliharaan rutin pada pukul 01:00 - 03:00 WIB untuk peningkatan kualitas streaming..."
                                    rows={4}
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors resize-none leading-relaxed"
                                    required
                                />
                            </div>

                            {/* Submit button */}
                            <div className="pt-2">
                                <button
                                    type="submit"
                                    disabled={submitting || !title.trim() || !message.trim()}
                                    className={`w-full py-3 rounded-xl flex items-center justify-center gap-2 text-xs font-bold transition-all ${
                                        submitting || !title.trim() || !message.trim()
                                            ? 'bg-white/[0.04] text-slate-500 border border-white/[0.06] cursor-not-allowed'
                                            : 'gold-btn shadow-lg'
                                    }`}
                                >
                                    <Send size={15} />
                                    {submitting ? 'Menerbitkan Siaran...' : 'Siarkan Pengumuman Sekarang'}
                                </button>
                                <p className="text-[11px] text-slate-500 text-center mt-2">
                                    * Mengirim pengumuman baru akan otomatis menonaktifkan pengumuman yang sedang aktif sebelumnya.
                                </p>
                            </div>
                        </form>
                    </div>
                </div>

                {/* Mobile App Simulator Column */}
                <div className="lg:col-span-5">
                    <div className="glass-panel p-6 space-y-4">
                        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                            <div className="flex items-center gap-2 text-xs font-bold text-white">
                                <Smartphone size={15} className="text-amber-400" /> Simulator Pop-up Mobile App
                            </div>
                            <span className="text-[10px] text-slate-500">Live Preview</span>
                        </div>

                        {/* Phone Mockup Frame */}
                        <div className="mx-auto w-full max-w-sm rounded-3xl border-2 border-white/10 bg-[#07090E] p-4 shadow-2xl relative overflow-hidden">
                            <div className="w-20 h-4 bg-white/10 rounded-full mx-auto mb-4" />
                            
                            <div className="space-y-3 opacity-30 pointer-events-none mb-6">
                                <div className="h-4 bg-white/10 rounded w-1/3" />
                                <div className="h-28 bg-white/5 rounded-2xl" />
                                <div className="h-4 bg-white/10 rounded w-1/2" />
                            </div>

                            {/* In-App Dialog Preview */}
                            <div className="p-4 rounded-2xl bg-[#0F1420] border border-white/15 shadow-2xl relative">
                                <div className="flex items-start gap-3 mb-2.5">
                                    {(() => {
                                        const meta = getTypeMeta(type);
                                        const Icon = meta.icon;
                                        return (
                                            <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${meta.boxBg}`}>
                                                <Icon size={16} className={meta.accentColor} />
                                            </div>
                                        );
                                    })()}
                                    <div className="space-y-0.5">
                                        <div className="text-xs font-bold text-white tracking-tight">
                                            {title.trim() || 'Judul Pengumuman Disini'}
                                        </div>
                                        <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                                            AsianDrama Official
                                        </span>
                                    </div>
                                </div>

                                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line mb-3">
                                    {message.trim() || 'Isi teks pengumuman yang diketikkan admin akan tampil secara langsung di sini bagi seluruh pengguna mobile app.'}
                                </p>

                                <button
                                    type="button"
                                    className="w-full py-2 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-bold"
                                >
                                    Saya Mengerti
                                </button>
                            </div>

                            <p className="text-[10px] text-slate-500 text-center mt-4">
                                Ditampilkan sekali per sesi app dibuka
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* History Table */}
            <div className="glass-panel overflow-hidden">
                <div className="p-5 sm:p-6 border-b border-white/[0.06] flex items-center justify-between">
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Riwayat Notifikasi & Arsip</h2>
                        <p className="text-xs text-slate-400 mt-0.5">Daftar seluruh siaran pengumuman yang pernah diterbitkan.</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-xs text-slate-400 font-semibold">
                        {notifications.length} Riwayat
                    </span>
                </div>

                {loading ? (
                    <div className="p-12 text-center text-slate-500 text-xs">Memuat riwayat pengumuman...</div>
                ) : notifications.length === 0 ? (
                    <div className="p-12 text-center text-slate-500 text-xs">Belum ada pengumuman yang pernah diterbitkan</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-white/[0.02] border-b border-white/[0.06] text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                <tr>
                                    <th className="px-5 py-3.5">Status</th>
                                    <th className="px-5 py-3.5">Tipe</th>
                                    <th className="px-5 py-3.5">Judul</th>
                                    <th className="px-5 py-3.5">Pesan</th>
                                    <th className="px-5 py-3.5">Waktu Rilis</th>
                                    <th className="px-5 py-3.5 text-right">Aksi</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/[0.04] text-xs">
                                {notifications.map((notif) => {
                                    const meta = getTypeMeta(notif.type);
                                    const Icon = meta.icon;
                                    return (
                                        <tr key={notif.id} className="hover:bg-white/[0.02] transition-colors">
                                            <td className="px-5 py-4 whitespace-nowrap">
                                                {notif.is_active ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-bold border border-emerald-500/20">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                                        Aktif
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] text-slate-500 text-[11px] font-medium border border-white/[0.06]">
                                                        Arsip
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-5 py-4 whitespace-nowrap">
                                                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold border ${meta.badge}`}>
                                                    <Icon size={11} /> {notif.type}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 font-semibold text-white max-w-xs truncate">
                                                {notif.title}
                                            </td>
                                            <td className="px-5 py-4 text-slate-400 max-w-sm truncate">
                                                {notif.message}
                                            </td>
                                            <td className="px-5 py-4 text-slate-500 whitespace-nowrap text-[11px]">
                                                {new Date(notif.created_at).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' })}
                                            </td>
                                            <td className="px-5 py-4 text-right whitespace-nowrap">
                                                <div className="flex items-center justify-end gap-2">
                                                    {notif.is_active && (
                                                        <button
                                                            onClick={() => handleDeactivate(notif.id)}
                                                            disabled={actionId === notif.id}
                                                            className="p-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 hover:text-amber-300 transition-colors"
                                                            title="Nonaktifkan"
                                                        >
                                                            <PowerOff size={14} />
                                                        </button>
                                                    )}
                                                    <button
                                                        onClick={() => handleDelete(notif.id)}
                                                        disabled={actionId === notif.id}
                                                        className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 transition-colors"
                                                        title="Hapus Dari Riwayat"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
