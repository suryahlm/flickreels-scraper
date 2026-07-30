'use client';

import { CheckCircle, Eye, Film, Loader2, RefreshCw, Trash2 } from 'lucide-react';
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
            showToast(`✅ "${drama.title}" berhasil dipublikasi!`, 'success');
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
        <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Film className="text-amber-400" size={28} />
                        Drama Baru (Antrian Review)
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Drama yang baru di-scraping. Periksa lalu Publish atau Hapus.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-full text-sm font-medium border border-amber-500/30">
                        {dramas.length} drama menunggu
                    </span>
                    <button
                        onClick={fetchDrafts}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 rounded-lg transition-colors text-sm"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-32">
                    <Loader2 className="animate-spin text-amber-400" size={32} />
                </div>
            )}

            {/* Empty state */}
            {!loading && dramas.length === 0 && (
                <div className="flex flex-col items-center justify-center py-32 text-center">
                    <CheckCircle className="text-green-400 mb-4" size={48} />
                    <p className="text-white font-semibold text-lg">Semua drama sudah ditinjau!</p>
                    <p className="text-gray-500 text-sm mt-1">Tidak ada drama yang menunggu review saat ini.</p>
                </div>
            )}

            {/* Drama Grid */}
            {!loading && dramas.length > 0 && (
                <div className="grid gap-4">
                    {dramas.map(drama => {
                        const isActing = !!actionLoading[drama.id];
                        let thumbnail = drama.thumbnail_url || drama.cover_url;
                        if (!thumbnail && drama.r2_folder) {
                            // r2_folder is stored raw (unencoded) — encode it here so spaces
                            // and parentheses don't break the Next.js Image component.
                            thumbnail = encodeURI(`https://cdn.asiandrama.cc/${drama.r2_folder}/cover.jpg`);
                        }

                        // NOTE: thumbnail_url/cover_url from the DB are already valid,
                        // correctly-encoded URLs (the publish scripts pre-encode thumbnail_url
                        // with encodeURIComponent; cover_url is the source's own URL as-is) —
                        // do NOT encodeURI() them again here. Doing so double-encodes existing
                        // %20 into %2520 and breaks the image (this was the actual bug).
                        if (thumbnail) {
                            // Bust cache because previous broken 302 redirects were cached
                            thumbnail = thumbnail + '?t=' + new Date().getTime();
                        }

                        return (
                            <div
                                key={drama.id}
                                className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
                                    isActing ? 'opacity-60 border-gray-700' : 'border-gray-800 hover:border-gray-700'
                                }`}
                            >
                                <div className="flex gap-4 p-4">
                                    {/* Thumbnail */}
                                    <div className="flex-shrink-0 w-20 h-28 bg-gray-800 rounded-lg overflow-hidden relative">
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
                                                <Film size={24} className="text-gray-600" />
                                            </div>
                                        )}
                                    </div>

                                    {/* Info */}
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-white font-semibold text-base leading-tight mb-1 truncate">
                                            {drama.title}
                                        </h3>
                                        <div className="flex flex-wrap gap-2 mb-2">
                                            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded border border-blue-500/30">
                                                {drama.total_episodes} Episode
                                            </span>
                                            {drama.r2_folder && (
                                                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded border border-green-500/30">
                                                    ✅ R2: {drama.r2_folder}
                                                </span>
                                            )}
                                            <span className="px-2 py-0.5 bg-gray-700 text-gray-400 text-xs rounded">
                                                {formatDate(drama.created_at)}
                                            </span>
                                        </div>
                                        {drama.synopsis && (
                                            <p className="text-gray-400 text-xs line-clamp-2">
                                                {drama.synopsis}
                                            </p>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex-shrink-0 flex flex-col gap-2 justify-center">
                                        {/* Preview thumbnail in new tab */}
                                        {thumbnail && (
                                            <a
                                                href={thumbnail}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center gap-1.5 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors"
                                            >
                                                <Eye size={14} />
                                                Preview
                                            </a>
                                        )}

                                        {/* Publish */}
                                        <button
                                            onClick={() => handlePublish(drama)}
                                            disabled={isActing}
                                            className="flex items-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
                                        >
                                            {actionLoading[drama.id] === 'publish' ? (
                                                <Loader2 size={14} className="animate-spin" />
                                            ) : (
                                                <CheckCircle size={14} />
                                            )}
                                            Publish
                                        </button>

                                        {/* Delete */}
                                        <button
                                            onClick={() => setConfirmDelete(drama)}
                                            disabled={isActing}
                                            className="flex items-center gap-1.5 px-3 py-2 bg-red-600/80 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
                                        >
                                            {actionLoading[drama.id] === 'delete' ? (
                                                <Loader2 size={14} className="animate-spin" />
                                            ) : (
                                                <Trash2 size={14} />
                                            )}
                                            Hapus
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
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-red-500/30 rounded-2xl p-6 max-w-md w-full shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                                <Trash2 size={20} className="text-red-400" />
                            </div>
                            <h2 className="text-white font-bold text-lg">Konfirmasi Hapus</h2>
                        </div>
                        <p className="text-gray-300 text-sm mb-2">
                            Yakin ingin menghapus drama ini secara permanen?
                        </p>
                        <div className="bg-gray-800 rounded-lg p-3 mb-4">
                            <p className="text-white font-semibold text-sm">"{confirmDelete.title}"</p>
                            <p className="text-gray-400 text-xs mt-1">{confirmDelete.total_episodes} episode</p>
                            {confirmDelete.r2_folder && (
                                <p className="text-red-400 text-xs mt-1">
                                    ⚠️ Semua file di R2 folder <code className="bg-gray-700 px-1 rounded">{confirmDelete.r2_folder}</code> akan ikut terhapus.
                                </p>
                            )}
                        </div>
                        <p className="text-gray-500 text-xs mb-5">
                            Tindakan ini <strong className="text-red-400">tidak dapat dibatalkan</strong>. Drama lain tidak terpengaruh.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setConfirmDelete(null)}
                                className="flex-1 py-2.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
                            >
                                Batal
                            </button>
                            <button
                                onClick={handleDeleteConfirmed}
                                className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-bold transition-colors"
                            >
                                Ya, Hapus Permanen
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast */}
            {toast && (
                <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl shadow-2xl text-sm font-medium transition-all ${
                    toast.type === 'success'
                        ? 'bg-green-600 text-white'
                        : 'bg-red-600 text-white'
                }`}>
                    {toast.msg}
                </div>
            )}
        </div>
    );
}
