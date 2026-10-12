'use client';

import { CheckCircle, Eye, Film, Loader2, RefreshCw, Trash2, FolderCheck, Clock, Sparkles } from 'lucide-react';
import Image from 'next/image';
import { useCallback, useEffect, useState } from 'react';
import { supabaseAdmin } from '@/lib/supabase';

interface DraftDrama {
    id: string;
    title: string;
    synopsis: string | null;
    thumbnail_url: string | null;
    cover_url: string | null;
    total_episodes: number;
    r2_folder: string | null;
    created_at: string;
    flickreels_id: string | null;
}

export default function DraftDramasPage() {
    const [dramas, setDramas] = useState<DraftDrama[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<Record<string, 'publish' | 'delete' | null>>({});
    const [confirmDelete, setConfirmDelete] = useState<DraftDrama | null>(null);
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

    const showToast = (msg: string, type: 'success' | 'error') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 4000);
    };

    const fetchDrafts = useCallback(async () => {
        setLoading(true);
        const { data, error } = await supabaseAdmin
            .from('dramas')
            .select('id, title, synopsis, thumbnail_url, cover_url, total_episodes, r2_folder, created_at, flickreels_id')
            .eq('is_published', false)
            .order('created_at', { ascending: false });

        if (error) {
            showToast('Gagal memuat data: ' + error.message, 'error');
        } else {
            setDramas(data || []);
        }
        setLoading(false);
    }, []);

    useEffect(() => { fetchDrafts(); }, [fetchDrafts]);

    const handlePublish = async (drama: DraftDrama) => {
        setActionLoading(prev => ({ ...prev, [drama.id]: 'publish' }));
        try {
            const res = await fetch('/api/dramas', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: drama.id, is_published: true }),
            });
            const result = await res.json();
            if (!res.ok) throw new Error(result.error);
            showToast(`✅ "${drama.title}" berhasil dipublikasikan!`, 'success');
            setDramas(prev => prev.filter(d => d.id !== drama.id));
        } catch (err: any) {
            showToast('Gagal publish: ' + err.message, 'error');
        } finally {
            setActionLoading(prev => ({ ...prev, [drama.id]: null }));
        }
    };

    const handleDeleteConfirmed = async () => {
        if (!confirmDelete) return;
        const drama = confirmDelete;
        setConfirmDelete(null);
        setActionLoading(prev => ({ ...prev, [drama.id]: 'delete' }));
        try {
            const res = await fetch(`/api/dramas?id=${drama.id}`, { method: 'DELETE' });
            const result = await res.json();
            if (!res.ok) throw new Error(result.error);
            showToast(`🗑️ "${drama.title}" berhasil dihapus dari DB & R2.`, 'success');
            setDramas(prev => prev.filter(d => d.id !== drama.id));
        } catch (err: any) {
            showToast('Gagal hapus: ' + err.message, 'error');
        } finally {
            setActionLoading(prev => ({ ...prev, [drama.id]: null }));
        }
    };

    const formatDate = (iso: string) => {
        return new Date(iso).toLocaleString('id-ID', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    };

    return (
        <div className="space-y-6">
            {/* Header Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/[0.08]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                        <Film size={20} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Antrian Kurasi Drama</h2>
                        <p className="text-xs text-gray-400">Review hasil scraping sebelum ditayangkan ke pengguna aplikasi</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <span className="px-3 py-1.5 bg-amber-500/10 text-amber-300 rounded-xl text-xs font-bold border border-amber-500/25 shadow-[0_0_12px_rgba(229,169,60,0.12)]">
                        {dramas.length} drama menunggu
                    </span>
                    <button
                        onClick={fetchDrafts}
                        disabled={loading}
                        className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-gray-300 hover:text-white transition-all disabled:opacity-50"
                    >
                        <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Loading Skeleton */}
            {loading && (
                <div className="flex items-center justify-center py-32">
                    <div className="flex flex-col items-center gap-3">
                        <div className="w-10 h-10 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center p-2">
                            <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                        </div>
                        <p className="text-xs font-semibold text-gray-400">Memuat antrian kurasi...</p>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!loading && dramas.length === 0 && (
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-16 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto mb-4 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
                        <CheckCircle size={32} />
                    </div>
                    <h3 className="text-lg font-bold text-white tracking-tight">Semua Drama Sudah Ditinjau!</h3>
                    <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                        Tidak ada drama antrian baru saat ini. Semua konten yang di-scrape telah berhasil dipublikasikan.
                    </p>
                </div>
            )}

            {/* Drama Grid */}
            {!loading && dramas.length > 0 && (
                <div className="grid gap-4">
                    {dramas.map(drama => {
                        const isActing = !!actionLoading[drama.id];
                        let thumbnail = drama.thumbnail_url || drama.cover_url;
                        if (!thumbnail && drama.r2_folder) {
                            thumbnail = encodeURI(`https://cdn.asiandrama.cc/${drama.r2_folder}/cover.jpg`);
                        }
                        if (thumbnail) {
                            thumbnail = thumbnail + '?t=' + new Date().getTime();
                        }

                        return (
                            <div
                                key={drama.id}
                                className={`glass-card rounded-2xl border transition-all overflow-hidden ${
                                    isActing ? 'opacity-60 border-white/20' : 'border-white/[0.08] hover:border-amber-500/30'
                                }`}
                            >
                                <div className="flex flex-col sm:flex-row gap-5 p-5">
                                    {/* Thumbnail 2:3 */}
                                    <div className="flex-shrink-0 w-24 h-36 bg-[#090D15] rounded-xl overflow-hidden relative border border-white/[0.08] shadow-lg">
                                        {thumbnail ? (
                                            <Image
                                                src={thumbnail}
                                                alt={drama.title}
                                                fill
                                                className="object-cover"
                                                unoptimized
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center">
                                                <Film size={28} className="text-gray-600" />
                                            </div>
                                        )}
                                    </div>

                                    {/* Info */}
                                    <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                                <span className="px-2.5 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 text-[10px] font-bold">
                                                    {drama.total_episodes} Episode
                                                </span>
                                                {drama.r2_folder && (
                                                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold flex items-center gap-1">
                                                        <FolderCheck size={11} /> {drama.r2_folder}
                                                    </span>
                                                )}
                                                <span className="px-2.5 py-0.5 rounded-full bg-white/[0.04] text-gray-400 text-[10px] font-medium flex items-center gap-1">
                                                    <Clock size={11} /> {formatDate(drama.created_at)}
                                                </span>
                                            </div>

                                            <h3 className="text-base font-bold text-white leading-tight mb-2 truncate">
                                                {drama.title}
                                            </h3>

                                            {drama.synopsis ? (
                                                <p className="text-gray-400 text-xs line-clamp-3 leading-relaxed">
                                                    {drama.synopsis}
                                                </p>
                                            ) : (
                                                <p className="text-gray-600 text-xs italic">
                                                    Tidak ada sinopsis teks yang tersedia.
                                                </p>
                                            )}
                                        </div>

                                        <p className="text-[10px] text-gray-500 mt-3 font-mono">
                                            ID: {drama.id}
                                        </p>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="flex-shrink-0 flex sm:flex-col gap-2 justify-center pt-2 sm:pt-0 border-t sm:border-t-0 border-white/[0.06]">
                                        {thumbnail && (
                                            <a
                                                href={thumbnail}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-gray-300 text-xs font-semibold transition-all"
                                            >
                                                <Eye size={13} />
                                                <span>Cover</span>
                                            </a>
                                        )}

                                        <button
                                            onClick={() => handlePublish(drama)}
                                            disabled={isActing}
                                            className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-bold transition-all shadow-[0_0_12px_rgba(16,185,129,0.15)] disabled:opacity-50"
                                        >
                                            {actionLoading[drama.id] === 'publish' ? (
                                                <Loader2 size={13} className="animate-spin text-emerald-300" />
                                            ) : (
                                                <CheckCircle size={13} />
                                            )}
                                            <span>Publish</span>
                                        </button>

                                        <button
                                            onClick={() => setConfirmDelete(drama)}
                                            disabled={isActing}
                                            className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-300 text-xs font-bold transition-all disabled:opacity-50"
                                        >
                                            {actionLoading[drama.id] === 'delete' ? (
                                                <Loader2 size={13} className="animate-spin text-rose-300" />
                                            ) : (
                                                <Trash2 size={13} />
                                            )}
                                            <span>Hapus</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {confirmDelete && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-rose-500/30 rounded-2xl p-6 max-w-md w-full shadow-[0_20px_60px_rgba(0,0,0,0.6)]">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-rose-500/15 border border-rose-500/30 rounded-xl flex items-center justify-center text-rose-400">
                                <Trash2 size={20} />
                            </div>
                            <div>
                                <h3 className="text-white font-bold text-base tracking-tight">Hapus Drama Permanen</h3>
                                <p className="text-gray-400 text-xs">Peringatan penghapusan berkas & database</p>
                            </div>
                        </div>

                        <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-4">
                            <p className="text-white font-bold text-sm">"{confirmDelete.title}"</p>
                            <p className="text-gray-400 text-xs mt-1">{confirmDelete.total_episodes} episode</p>
                            {confirmDelete.r2_folder && (
                                <p className="text-amber-400 text-xs mt-2 bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg">
                                    ⚠️ File Cloudflare R2 di folder <code className="font-mono text-white">{confirmDelete.r2_folder}</code> akan ikut dibersihkan.
                                </p>
                            )}
                        </div>

                        <p className="text-gray-400 text-xs mb-6 leading-relaxed">
                            Tindakan ini tidak dapat dibatalkan. Pastikan Anda benar-benar ingin membuang konten ini.
                        </p>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setConfirmDelete(null)}
                                className="flex-1 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-white text-xs font-semibold transition-all"
                            >
                                Batal
                            </button>
                            <button
                                onClick={handleDeleteConfirmed}
                                className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-[0_0_15px_rgba(239,68,68,0.3)]"
                            >
                                Ya, Hapus Sekarang
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toast && (
                <div className={`fixed bottom-6 right-6 z-50 px-5 py-3.5 rounded-2xl shadow-2xl text-xs font-bold transition-all border ${
                    toast.type === 'success'
                        ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
                        : 'bg-rose-950/90 border-rose-500/40 text-rose-200'
                }`}>
                    {toast.msg}
                </div>
            )}
        </div>
    );
}
