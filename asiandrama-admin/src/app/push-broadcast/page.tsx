'use client';

import { 
    Bell, 
    Send, 
    Users, 
    Smartphone, 
    Sparkles, 
    CheckCircle2, 
    AlertCircle, 
    Loader2, 
    Film, 
    PlayCircle, 
    Gift, 
    Star, 
    Radio,
    Clock,
    Wifi,
    Battery
} from 'lucide-react';
import { useState } from 'react';

const PRESETS = [
    {
        label: 'Drama Baru',
        icon: Film,
        title: '🎬 Drama Baru Sudah Tersedia!',
        body: 'Drama paling dinanti sudah tayang full HD di AsianDrama. Tonton sekarang gratis!',
    },
    {
        label: 'Lanjutkan Menonton',
        icon: PlayCircle,
        title: '▶️ Lanjutkan Drama Favoritmu',
        body: 'Kamu belum menyelesaikan episode terakhirmu. Buka aplikasi dan lanjutkan nonton!',
    },
    {
        label: 'Rekomendasi Spesial',
        icon: Star,
        title: '⭐ Rekomendasi Drama Pilihan',
        body: 'Kami memilihkan drama romantis terfavorit untuk menemanimu hari ini.',
    },
    {
        label: 'Bonus Koin & Hadiah',
        icon: Gift,
        title: '🎁 Ada Hadiah Koin Spesial!',
        body: 'Klaim bonus koin harianmu sekarang dan tonton episode VIP sepuasnya tanpa iklan!',
    },
    {
        label: 'Pengumuman Penting',
        icon: Bell,
        title: '📢 Pengumuman Penting AsianDrama',
        body: 'Ada pembaruan server dan fitur baru di AsianDrama. Buka aplikasi untuk info lengkap!',
    },
];

export default function PushBroadcastPage() {
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [sending, setSending] = useState(false);
    const [result, setResult] = useState<{
        success?: boolean;
        total_devices?: number;
        sent?: number;
        failed?: number;
        error?: string;
        message?: string;
    } | null>(null);

    const handlePreset = (preset: typeof PRESETS[0]) => {
        setTitle(preset.title);
        setBody(preset.body);
        setResult(null);
    };

    const handleSend = async () => {
        if (!title.trim() || !body.trim()) return;
        setSending(true);
        setResult(null);

        try {
            const res = await fetch('/api/send-push', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim(), body: body.trim() }),
            });
            const data = await res.json();
            setResult(data);
        } catch (err: any) {
            setResult({ error: err.message || 'Gagal mengirim push notification' });
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-16">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-white/[0.06] gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                        <span className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                            <Bell size={20} />
                        </span>
                        <h1 className="text-2xl font-bold tracking-tight text-white">Push Notification Broadcast</h1>
                    </div>
                    <p className="text-xs text-slate-400">
                        Kirim notifikasi pesan langsung ke lockscreen HP seluruh perangkat pengguna aktif aplikasi AsianDrama.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <div className="px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold flex items-center gap-2">
                        <Radio size={13} className="text-amber-400 animate-pulse" />
                        Firebase Cloud Messaging Active
                    </div>
                </div>
            </div>

            {/* Template Gallery */}
            <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
                    <Sparkles size={14} className="text-amber-400" /> Template Cepat:
                </div>
                <div className="flex flex-wrap gap-2.5">
                    {PRESETS.map((preset) => {
                        const Icon = preset.icon;
                        return (
                            <button
                                key={preset.label}
                                onClick={() => handlePreset(preset)}
                                className="px-3.5 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.06] hover:border-amber-500/30 text-xs font-semibold text-slate-300 hover:text-white flex items-center gap-2 transition-all group"
                            >
                                <Icon size={14} className="text-amber-400 group-hover:scale-110 transition-transform" />
                                {preset.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Split Screen Studio: Composer & Smartphone Mockup */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Composer Form */}
                <div className="lg:col-span-7">
                    <div className="glass-panel p-6 sm:p-7 space-y-6">
                        <div className="pb-4 border-b border-white/[0.06]">
                            <h2 className="text-base font-bold text-white tracking-tight">Komposisi Pesan Notifikasi</h2>
                            <p className="text-xs text-slate-400 mt-1">
                                Pastikan judul menarik perhatian dan isi pesan padat agar terbaca penuh di lockscreen ponsel.
                            </p>
                        </div>

                        <div className="space-y-5">
                            {/* Title */}
                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <label className="text-xs font-semibold text-slate-300">Judul Push Notification</label>
                                    <span className="text-[11px] text-slate-500">{title.length} / 100</span>
                                </div>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="Contoh: Drama Baru Sudah Ada!"
                                    maxLength={100}
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors"
                                />
                            </div>

                            {/* Body */}
                            <div>
                                <div className="flex justify-between items-center mb-1.5">
                                    <label className="text-xs font-semibold text-slate-300">Isi Pesan Notifikasi</label>
                                    <span className="text-[11px] text-slate-500">{body.length} / 200</span>
                                </div>
                                <textarea
                                    value={body}
                                    onChange={(e) => setBody(e.target.value)}
                                    placeholder="Contoh: Episode terbaru serial kesayanganmu sudah hadir full subtitle Indonesia. Tonton sekarang juga!"
                                    rows={4}
                                    maxLength={200}
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors resize-none leading-relaxed"
                                />
                            </div>

                            {/* Broadcast Trigger */}
                            <div className="pt-3">
                                <button
                                    onClick={handleSend}
                                    disabled={sending || !title.trim() || !body.trim()}
                                    className={`w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-xs font-bold transition-all ${
                                        sending || !title.trim() || !body.trim()
                                            ? 'bg-white/[0.04] text-slate-500 border border-white/[0.06] cursor-not-allowed'
                                            : 'gold-btn shadow-xl shadow-amber-500/20'
                                    }`}
                                >
                                    {sending ? (
                                        <><Loader2 size={16} className="animate-spin text-black" /> Mengirimkan ke Seluruh Perangkat...</>
                                    ) : (
                                        <><Send size={16} /> Kirim Push Notification ke Semua User</>
                                    )}
                                </button>
                                <p className="text-[11px] text-slate-500 text-center mt-2.5">
                                    Pesan akan langsung diproses oleh server FCM dan dihantarkan ke seluruh perangkat yang terinstal.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Smartphone Lockscreen Mockup */}
                <div className="lg:col-span-5">
                    <div className="glass-panel p-6 sm:p-7 space-y-4">
                        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                            <div className="flex items-center gap-2 text-xs font-bold text-white">
                                <Smartphone size={15} className="text-amber-400" /> Simulator Lockscreen Ponsel
                            </div>
                            <span className="text-[10px] text-slate-500">Realtime Preview</span>
                        </div>

                        {/* Phone Container */}
                        <div className="mx-auto w-full max-w-xs rounded-[36px] border-4 border-slate-800 bg-[#07090E] p-4 shadow-2xl relative overflow-hidden flex flex-col justify-between min-h-[440px]">
                            {/* Wallpaper Ambient Glow */}
                            <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/40 via-purple-950/20 to-black pointer-events-none" />

                            {/* Phone Top Notch / Status Bar */}
                            <div className="relative z-10">
                                <div className="flex items-center justify-between px-3 text-[10px] font-semibold text-slate-400 mb-6">
                                    <span>09:41</span>
                                    <div className="w-16 h-4 bg-black rounded-full border border-white/10" />
                                    <div className="flex items-center gap-1.5">
                                        <Wifi size={10} />
                                        <Battery size={11} />
                                    </div>
                                </div>

                                {/* Lockscreen Clock */}
                                <div className="text-center my-6 space-y-1">
                                    <div className="text-4xl font-extralight text-white tracking-wider">09:41</div>
                                    <div className="text-[11px] text-slate-400 font-medium">Selasa, 13 Oktober</div>
                                </div>

                                {/* Push Notification Pill */}
                                <div className="p-3.5 rounded-2xl bg-black/60 backdrop-blur-xl border border-white/20 shadow-xl transition-all">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <div className="w-5 h-5 rounded-md bg-amber-500 flex items-center justify-center text-[10px] font-black text-black">
                                                AD
                                            </div>
                                            <span className="text-[11px] font-bold text-white tracking-tight">AsianDrama</span>
                                        </div>
                                        <span className="text-[9px] text-slate-400">Baru saja</span>
                                    </div>

                                    <div className="space-y-0.5">
                                        <div className="text-xs font-bold text-white leading-tight">
                                            {title.trim() || 'Judul Notifikasi'}
                                        </div>
                                        <div className="text-[11px] text-slate-300 leading-snug line-clamp-2">
                                            {body.trim() || 'Isi pesan push notification akan ditampilkan di sini pada lockscreen...'}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Bottom Lock Icon / Swipe Bar */}
                            <div className="relative z-10 text-center pb-2">
                                <div className="w-24 h-1 bg-white/30 rounded-full mx-auto" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Delivery Result Card */}
            {result && (
                <div className={`glass-panel p-6 border transition-all ${
                    result.error 
                        ? 'border-rose-500/30 bg-rose-500/[0.04]' 
                        : result.message
                        ? 'border-amber-500/30 bg-amber-500/[0.04]'
                        : 'border-emerald-500/30 bg-emerald-500/[0.04]'
                }`}>
                    {result.error ? (
                        <div className="flex items-center gap-3 text-rose-400 text-xs font-semibold">
                            <AlertCircle size={18} />
                            <span>Gagal Mengirim Broadcast: {result.error}</span>
                        </div>
                    ) : result.message ? (
                        <div className="flex items-center gap-3 text-amber-400 text-xs font-semibold">
                            <AlertCircle size={18} />
                            <span>Perhatian: {result.message}</span>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                                    <CheckCircle2 size={18} />
                                    Broadcast Sukses Dihantarkan ke Jaringan FCM!
                                </div>
                                <span className="text-[11px] text-slate-400 font-mono">
                                    Status: 200 OK
                                </span>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">
                                        Total Token Target
                                    </div>
                                    <div className="text-xl font-black text-white flex items-center gap-2">
                                        <Users size={18} className="text-slate-400" />
                                        {result.total_devices || 0}
                                    </div>
                                </div>

                                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                    <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider mb-1">
                                        Berhasil Terkirim
                                    </div>
                                    <div className="text-xl font-black text-emerald-400">
                                        {result.sent || 0} Perangkat
                                    </div>
                                </div>

                                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
                                    <div className="text-[10px] text-rose-400 font-bold uppercase tracking-wider mb-1">
                                        Gagal / Kedaluwarsa
                                    </div>
                                    <div className="text-xl font-black text-rose-400">
                                        {result.failed || 0} Perangkat
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
