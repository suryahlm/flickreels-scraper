'use client';

import { Bell, Send, Users } from 'lucide-react';
import { useState } from 'react';

const PRESETS = [
    {
        label: '🎬 Drama Baru Tersedia!',
        title: 'Drama Baru Sudah Ada!',
        body: 'Drama terbaru sudah tersedia di AsianDrama. Tonton sekarang!',
    },
    {
        label: '▶️ Lanjutkan Menonton',
        title: 'Lanjutkan Drama Favoritmu',
        body: 'Kamu belum selesai menonton. Lanjutkan sekarang sebelum ketinggalan!',
    },
    {
        label: '📢 Pengumuman Admin',
        title: '',
        body: '',
    },
    {
        label: '⭐ Rekomendasi Drama',
        title: 'Drama Pilihan Untukmu',
        body: 'Kami punya rekomendasi drama spesial untukmu hari ini!',
    },
    {
        label: '🎁 Promo & Hadiah',
        title: 'Ada Hadiah Untukmu!',
        body: 'Buka AsianDrama sekarang dan dapatkan hadiah spesialmu!',
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
            setResult({ error: err.message });
        } finally {
            setSending(false);
        }
    };

    return (
        <div className="p-6 max-w-2xl">
            <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                <Bell className="text-amber-400" size={28} />
                Broadcast Push Notification
            </h1>
            <p className="text-gray-400 mb-8 text-sm">
                Kirim notifikasi langsung ke HP seluruh pengguna yang sudah mengaktifkan notifikasi.
            </p>

            {/* Preset Buttons */}
            <div className="mb-6">
                <p className="text-sm text-gray-400 mb-3">Template cepat:</p>
                <div className="flex flex-wrap gap-2">
                    {PRESETS.map((preset) => (
                        <button
                            key={preset.label}
                            onClick={() => handlePreset(preset)}
                            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
                        >
                            {preset.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Form */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
                <div>
                    <label className="block text-sm text-gray-400 mb-2">Judul Notifikasi</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Contoh: Drama Baru Sudah Ada!"
                        maxLength={100}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:outline-none"
                    />
                    <p className="text-xs text-gray-600 mt-1 text-right">{title.length}/100</p>
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-2">Isi Pesan</label>
                    <textarea
                        value={body}
                        onChange={(e) => setBody(e.target.value)}
                        placeholder="Contoh: Drama terbaru sudah tersedia. Tonton sekarang!"
                        rows={3}
                        maxLength={200}
                        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:outline-none resize-none"
                    />
                    <p className="text-xs text-gray-600 mt-1 text-right">{body.length}/200</p>
                </div>

                {/* Preview */}
                {(title || body) && (
                    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <p className="text-xs text-gray-500 mb-2">📱 Preview Notifikasi:</p>
                        <div className="bg-gray-700 rounded-lg p-3 flex items-start gap-3">
                            <div className="w-8 h-8 bg-amber-600 rounded-lg flex-shrink-0 flex items-center justify-center text-xs">🎬</div>
                            <div>
                                <p className="text-white text-sm font-semibold">{title || 'Judul Notifikasi'}</p>
                                <p className="text-gray-300 text-xs mt-0.5">{body || 'Isi pesan notifikasi...'}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Send Button */}
                <button
                    onClick={handleSend}
                    disabled={sending || !title.trim() || !body.trim()}
                    className="w-full py-3 bg-gradient-to-r from-amber-500 to-yellow-600 hover:from-amber-600 hover:to-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-all"
                >
                    <Send size={18} />
                    {sending ? 'Mengirim ke semua perangkat...' : 'Kirim Notifikasi ke Semua User'}
                </button>
            </div>

            {/* Result */}
            {result && (
                <div className={`mt-4 p-4 rounded-lg border ${result.error ? 'bg-red-500/10 border-red-500/30' : 'bg-green-500/10 border-green-500/30'}`}>
                    {result.error ? (
                        <p className="text-red-400 text-sm">❌ Error: {result.error}</p>
                    ) : result.message ? (
                        <p className="text-yellow-400 text-sm">⚠️ {result.message}</p>
                    ) : (
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2 text-green-400">
                                <Users size={18} />
                                <div>
                                    <p className="text-xs text-gray-400">Total Perangkat</p>
                                    <p className="font-bold">{result.total_devices}</p>
                                </div>
                            </div>
                            <div className="text-green-400">
                                <p className="text-xs text-gray-400">Terkirim</p>
                                <p className="font-bold">{result.sent}</p>
                            </div>
                            {result.failed! > 0 && (
                                <div className="text-red-400">
                                    <p className="text-xs text-gray-400">Gagal</p>
                                    <p className="font-bold">{result.failed}</p>
                                </div>
                            )}
                            <p className="text-green-400 text-sm ml-auto">✅ Notifikasi berhasil dikirim!</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
