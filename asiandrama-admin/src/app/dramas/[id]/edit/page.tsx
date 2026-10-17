'use client';

import { useState, useEffect, useRef, useTransition } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { 
    ArrowLeft, 
    Save, 
    Loader2, 
    Upload, 
    Image as ImageIcon, 
    Link2, 
    CheckCircle2, 
    AlertCircle, 
    Tag, 
    Film, 
    Eye, 
    Sparkles, 
    ExternalLink, 
    Copy, 
    Check, 
    Folder, 
    Layers,
    Clock,
    RefreshCw,
    X
} from 'lucide-react';
import { fetchDramaForEdit, updateDramaAdminAction } from '../../actions';
import { type Category, type Drama } from '@/lib/supabase';

// Helper for source detection from r2_folder
function getSourceBadge(r2_folder: string | null | undefined): { label: string; color: string } {
    if (r2_folder?.startsWith('reelshort/')) return { label: 'ReelShort', color: 'bg-purple-500/15 text-purple-300 border-purple-500/30' };
    if (r2_folder?.startsWith('netshort/')) return { label: 'Netshort', color: 'bg-amber-500/15 text-amber-300 border-amber-500/30' };
    if (r2_folder?.startsWith('dramanova/')) return { label: 'DramaNova', color: 'bg-rose-500/15 text-rose-300 border-rose-500/30' };
    if (r2_folder?.startsWith('dramabox/')) return { label: 'DramaBox', color: 'bg-blue-500/15 text-blue-300 border-blue-500/30' };
    if (r2_folder?.startsWith('melolo/')) return { label: 'Melolo', color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' };
    if (r2_folder?.startsWith('flickreels/')) return { label: 'FlickReels', color: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' };
    return { label: 'ReelShort', color: 'bg-purple-500/15 text-purple-300 border-purple-500/30' };
}

export default function EditDramaPage() {
    const params = useParams();
    const router = useRouter();
    const dramaId = params?.id as string;

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploadingCover, setUploadingCover] = useState(false);
    const [categories, setCategories] = useState<Category[]>([]);
    const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [copiedUrl, setCopiedUrl] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [imageError, setImageError] = useState(false);

    // Form fields
    const [title, setTitle] = useState('');
    const [synopsis, setSynopsis] = useState('');
    const [categoryId, setCategoryId] = useState<string>('');
    const [coverUrl, setCoverUrl] = useState('');
    const [customUrlInput, setCustomUrlInput] = useState('');
    const [totalEpisodes, setTotalEpisodes] = useState<number>(0);
    const [viewCount, setViewCount] = useState<number>(0);
    const [realViewCount, setRealViewCount] = useState<number>(0);
    const [releaseStatus, setReleaseStatus] = useState<'ongoing' | 'completed'>('completed');
    const [isPublished, setIsPublished] = useState<boolean>(true);
    const [r2Folder, setR2Folder] = useState<string>('');
    const [createdAt, setCreatedAt] = useState<string>('');
    const [updatedAt, setUpdatedAt] = useState<string>('');

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load drama data
    useEffect(() => {
        if (!dramaId) return;
        loadData();
    }, [dramaId]);

    // Keyboard shortcut for saving (Ctrl/Cmd + S)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 's') {
                e.preventDefault();
                handleSave();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [title, synopsis, categoryId, coverUrl, totalEpisodes, viewCount, releaseStatus, isPublished, saving]);

    // Toast auto-dismiss
    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 4000);
            return () => clearTimeout(timer);
        }
    }, [toast]);

    async function loadData() {
        setLoading(true);
        setImageError(false);
        try {
            const res = await fetchDramaForEdit(dramaId);
            if (!res.success || !res.drama) {
                setToast({ type: 'error', message: res.error || 'Drama tidak ditemukan' });
                setLoading(false);
                return;
            }

            const d = res.drama;
            setTitle(d.title || '');
            setSynopsis(d.synopsis || '');
            setCategoryId(d.category_id || '');
            
            // Prefer cover_url, then thumbnail_url, then construct from r2_folder
            let initialCover = d.cover_url || d.thumbnail_url || '';
            if (initialCover.startsWith('/api/stream/')) {
                initialCover = 'https://api.asiandrama.cc' + initialCover.replace('/api/stream', '/stream');
            } else if (!initialCover && d.r2_folder) {
                initialCover = `https://api.asiandrama.cc/stream/${encodeURI(d.r2_folder)}/cover.jpg`;
            }
            setCoverUrl(initialCover);
            setCustomUrlInput(initialCover);

            setTotalEpisodes(d.total_episodes || 0);
            setViewCount(d.view_count || 0);
            setRealViewCount(d.real_view_count || 0);
            setReleaseStatus(d.release_status === 'ongoing' ? 'ongoing' : 'completed');
            setIsPublished(!!d.is_published);
            setR2Folder(d.r2_folder || '');
            setCreatedAt(d.created_at || '');
            setUpdatedAt(d.updated_at || '');

            setCategories(res.categories || []);
        } catch (err: any) {
            setToast({ type: 'error', message: err.message || 'Gagal memuat drama' });
        } finally {
            setLoading(false);
        }
    }

    // Handle Upload Cover to R2
    async function handleFileUpload(file: File) {
        if (!file) return;

        // Validasi ekstensi & tipe
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            setToast({ type: 'error', message: 'Hanya file format JPG, PNG, atau WebP yang diperbolehkan' });
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            setToast({ type: 'error', message: 'Ukuran file maksimum 10MB' });
            return;
        }

        setUploadingCover(true);
        setImageError(false);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('dramaId', dramaId);
            if (r2Folder) {
                formData.append('r2Folder', r2Folder);
            }

            const res = await fetch('/api/upload-cover', {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || 'Gagal mengunggah cover ke Cloudflare R2');
            }

            // Update live cover URL with cache buster
            const newUrl = data.url;
            setCoverUrl(newUrl);
            setCustomUrlInput(newUrl);
            setToast({ type: 'success', message: 'Cover berhasil diunggah ke Cloudflare R2 & diperbarui!' });
        } catch (err: any) {
            console.error('Upload error:', err);
            setToast({ type: 'error', message: err.message || 'Gagal mengunggah cover' });
        } finally {
            setUploadingCover(false);
        }
    }

    // Handle Paste URL
    const applyCustomUrl = () => {
        if (!customUrlInput.trim()) {
            setToast({ type: 'error', message: 'Harap masukkan URL cover yang valid' });
            return;
        }
        setImageError(false);
        setCoverUrl(customUrlInput.trim());
        setToast({ type: 'success', message: 'URL Cover berhasil diterapkan. Klik Simpan untuk menyimpan ke database.' });
    };

    // Copy CDN URL to clipboard
    const copyCdnUrl = () => {
        if (!coverUrl) return;
        navigator.clipboard.writeText(coverUrl);
        setCopiedUrl(true);
        setTimeout(() => setCopiedUrl(false), 2000);
    };

    // Save Changes
    async function handleSave() {
        if (!title.trim()) {
            setToast({ type: 'error', message: 'Judul drama wajib diisi' });
            return;
        }

        setSaving(true);
        try {
            const updates = {
                title: title.trim(),
                synopsis: synopsis.trim() || null,
                category_id: categoryId || null,
                cover_url: coverUrl.trim() || null,
                thumbnail_url: coverUrl.trim() || null,
                total_episodes: Number(totalEpisodes) || 0,
                view_count: Number(viewCount) || 0,
                release_status: releaseStatus,
                is_published: isPublished,
            };

            const res = await updateDramaAdminAction(dramaId, updates);

            if (!res.success) {
                throw new Error(res.error || 'Gagal menyimpan perubahan');
            }

            setToast({ type: 'success', message: 'Data drama berhasil disimpan!' });
        } catch (err: any) {
            console.error('Save error:', err);
            setToast({ type: 'error', message: err.message || 'Terjadi kesalahan saat menyimpan' });
        } finally {
            setSaving(false);
        }
    }

    // Word & Char counter for synopsis
    const synopsisCharCount = synopsis.length;
    const synopsisWordCount = synopsis.trim() ? synopsis.trim().split(/\s+/).length : 0;

    const sourceBadge = getSourceBadge(r2Folder);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
                <div className="w-12 h-12 rounded-2xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center shadow-[0_0_30px_rgba(229,169,60,0.2)]">
                    <Loader2 size={24} className="text-amber-400 animate-spin" />
                </div>
                <p className="text-xs font-semibold tracking-wider uppercase text-gray-400">
                    Memuat Editor Drama...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20">
            {/* Floating Toast Notification */}
            {toast && (
                <div 
                    className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-200 ${
                        toast.type === 'success' 
                            ? 'bg-emerald-950/90 text-emerald-200 border-emerald-500/30 shadow-[0_10px_40px_rgba(16,185,129,0.2)]' 
                            : 'bg-rose-950/90 text-rose-200 border-rose-500/30 shadow-[0_10px_40px_rgba(244,63,94,0.2)]'
                    }`}
                >
                    {toast.type === 'success' ? <CheckCircle2 size={18} className="text-emerald-400 shrink-0" /> : <AlertCircle size={18} className="text-rose-400 shrink-0" />}
                    <span className="text-xs font-semibold">{toast.message}</span>
                    <button onClick={() => setToast(null)} className="ml-2 text-white/50 hover:text-white">
                        <X size={14} />
                    </button>
                </div>
            )}

            {/* Breadcrumb & Top Bar Navigation */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/[0.08]">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                        <Link href="/dramas" className="hover:text-amber-400 transition-colors flex items-center gap-1">
                            <ArrowLeft size={12} />
                            Katalog Drama
                        </Link>
                        <span>/</span>
                        <span className="text-amber-400">Editor Drama</span>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight">
                            {title || 'Edit Drama'}
                        </h1>
                        <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-bold border ${sourceBadge.color}`}>
                            {sourceBadge.label}
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-bold border ${
                            isPublished 
                                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' 
                                : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                        }`}>
                            {isPublished ? '● Published' : '○ Draft'}
                        </span>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2.5 flex-wrap">
                    <Link
                        href="/dramas"
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-gray-300 hover:text-white transition-all"
                    >
                        <ArrowLeft size={14} />
                        Kembali
                    </Link>

                    <a
                        href={dramaId ? `https://asiandrama.cc/watch.html?id=${encodeURIComponent(dramaId)}` : 'https://asiandrama.cc'}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-gray-300 hover:text-white transition-all"
                        title="Buka Drama di Web Player"
                    >
                        <ExternalLink size={14} />
                        Lihat di Web
                    </a>

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 hover:from-amber-400 hover:to-yellow-300 text-black text-xs font-bold shadow-[0_0_20px_rgba(229,169,60,0.3)] transition-all transform active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                    >
                        {saving ? (
                            <>
                                <Loader2 size={15} className="animate-spin" />
                                Menyimpan...
                            </>
                        ) : (
                            <>
                                <Save size={15} />
                                Simpan Perubahan
                                <span className="hidden sm:inline text-[10px] font-normal opacity-70 ml-1">(⌘S)</span>
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Main 2-Column Luxury Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* ── LEFT COLUMN: Cover Poster Card & File Upload (5 Cols) ── */}
                <div className="lg:col-span-5 space-y-6">
                    {/* Cover Preview Card */}
                    <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 space-y-5">
                        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                            <div className="flex items-center gap-2">
                                <ImageIcon size={16} className="text-amber-400" />
                                <h3 className="text-sm font-bold text-white tracking-tight">Poster Cover Drama</h3>
                            </div>
                            <span className="text-[10px] text-gray-400 uppercase font-mono">
                                2:3 Vertical
                            </span>
                        </div>

                        {/* Poster Frame */}
                        <div className="relative aspect-[2/3] w-full max-w-[320px] mx-auto rounded-2xl overflow-hidden border border-white/[0.12] bg-[#0A0E17] shadow-[0_20px_50px_rgba(0,0,0,0.7)] group">
                            {/* Ambient Glow */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10 pointer-events-none" />

                            {coverUrl && !imageError ? (
                                <img
                                    src={coverUrl}
                                    alt={title || 'Cover Drama'}
                                    onError={() => setImageError(true)}
                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-gray-500 gap-3">
                                    <Film size={44} className="text-gray-600" />
                                    <div>
                                        <p className="text-xs font-semibold text-gray-400">Belum Ada Cover</p>
                                        <p className="text-[11px] text-gray-600 mt-1">Unggah gambar vertikal poster drama</p>
                                    </div>
                                </div>
                            )}

                            {/* Uploading Overlay */}
                            {uploadingCover && (
                                <div className="absolute inset-0 bg-black/85 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-3">
                                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
                                        <Loader2 size={24} className="text-amber-400 animate-spin" />
                                    </div>
                                    <p className="text-xs font-bold text-amber-300 tracking-wide">
                                        Mengunggah ke Cloudflare R2...
                                    </p>
                                </div>
                            )}

                            {/* Floating Format Pill */}
                            <div className="absolute top-3 right-3 z-10 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-[10px] font-bold text-amber-300">
                                WebP / JPG
                            </div>
                        </div>

                        {/* File Upload Zone (Drag & Drop) */}
                        <div
                            onDragOver={(e) => {
                                e.preventDefault();
                                setIsDragging(true);
                            }}
                            onDragLeave={() => setIsDragging(false)}
                            onDrop={(e) => {
                                e.preventDefault();
                                setIsDragging(false);
                                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                                    handleFileUpload(e.dataTransfer.files[0]);
                                }
                            }}
                            onClick={() => fileInputRef.current?.click()}
                            className={`p-5 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center space-y-2.5 ${
                                isDragging 
                                    ? 'border-amber-400 bg-amber-500/10 shadow-[0_0_20px_rgba(229,169,60,0.2)]' 
                                    : 'border-white/[0.12] hover:border-amber-500/50 hover:bg-white/[0.02]'
                            }`}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/jpg"
                                onChange={(e) => {
                                    if (e.target.files && e.target.files[0]) {
                                        handleFileUpload(e.target.files[0]);
                                    }
                                }}
                                className="hidden"
                            />
                            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mx-auto">
                                <Upload size={18} />
                            </div>
                            <div>
                                <p className="text-xs font-bold text-white">
                                    Klik atau Seret Gambar ke Sini
                                </p>
                                <p className="text-[11px] text-gray-400 mt-0.5">
                                    Mendukung JPG, PNG, atau WebP (Maks. 10MB)
                                </p>
                            </div>
                        </div>

                        {/* Manual URL Input Fallback */}
                        <div className="space-y-2 pt-2 border-t border-white/[0.06]">
                            <label className="text-[11px] font-semibold text-gray-400 flex items-center gap-1.5">
                                <Link2 size={13} className="text-amber-400" />
                                Atau Gunakan URL Gambar Langsung:
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={customUrlInput}
                                    onChange={(e) => setCustomUrlInput(e.target.value)}
                                    placeholder="https://api.asiandrama.cc/stream/.../cover.jpg"
                                    className="flex-1 px-3.5 py-2.5 rounded-xl bg-black/40 border border-white/[0.08] focus:border-amber-500/50 focus:outline-none text-xs text-white placeholder-gray-600 font-mono"
                                />
                                <button
                                    type="button"
                                    onClick={applyCustomUrl}
                                    className="px-3.5 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-xs font-semibold text-gray-200 hover:text-white transition-all whitespace-nowrap"
                                >
                                    Terapkan
                                </button>
                            </div>
                        </div>

                        {/* Storage CDN Information */}
                        {coverUrl && (
                            <div className="p-3.5 rounded-xl bg-black/30 border border-white/[0.06] space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1">
                                        <Folder size={11} className="text-amber-400" />
                                        Lokasi Storage & CDN:
                                    </span>
                                    <button
                                        onClick={copyCdnUrl}
                                        className="text-[10px] text-amber-400 hover:text-amber-300 flex items-center gap-1 font-semibold"
                                    >
                                        {copiedUrl ? <Check size={11} /> : <Copy size={11} />}
                                        {copiedUrl ? 'Tersalin' : 'Salin URL'}
                                    </button>
                                </div>
                                <p className="text-[10px] font-mono text-gray-400 break-all bg-black/40 p-2 rounded-lg border border-white/[0.04]">
                                    {coverUrl}
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* ── RIGHT COLUMN: Main Metadata Form (7 Cols) ── */}
                <div className="lg:col-span-7 space-y-6">
                    {/* Card 1: Judul & Genre */}
                    <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 space-y-6">
                        {/* Judul Drama */}
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-300 flex items-center justify-between">
                                <span className="flex items-center gap-1.5">
                                    <Film size={14} className="text-amber-400" />
                                    Judul Drama
                                </span>
                                <span className="text-[11px] text-gray-500 font-normal">
                                    {title.length} karakter
                                </span>
                            </label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Masukkan judul drama..."
                                className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/[0.09] focus:border-amber-500/60 focus:ring-1 focus:ring-amber-500/30 focus:outline-none text-sm font-semibold text-white placeholder-gray-600 transition-all"
                            />
                        </div>

                        {/* Kategori Genre (Isi Genre) */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
                                    <Tag size={14} className="text-amber-400" />
                                    Kategori Genre
                                </label>
                                {categoryId && (
                                    <button
                                        type="button"
                                        onClick={() => setCategoryId('')}
                                        className="text-[11px] text-gray-400 hover:text-amber-400 transition-colors"
                                    >
                                        Hapus Pilihan (Kosongkan)
                                    </button>
                                )}
                            </div>

                            {/* Dropdown Selector */}
                            <select
                                value={categoryId}
                                onChange={(e) => setCategoryId(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl bg-[#090D15] border border-white/[0.09] focus:border-amber-500/60 focus:outline-none text-xs text-white"
                            >
                                <option value="">-- Pilih Genre Drama --</option>
                                {categories.map((cat) => (
                                    <option key={cat.id} value={cat.id}>
                                        {cat.name}
                                    </option>
                                ))}
                            </select>

                            {/* Quick Select Pill Badges */}
                            <div className="space-y-1.5 pt-1">
                                <p className="text-[11px] text-gray-400 font-medium">
                                    Pilih cepat genre dengan 1-klik:
                                </p>
                                <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1 rounded-xl bg-black/20 border border-white/[0.04]">
                                    {categories.map((cat) => {
                                        const isSelected = categoryId === cat.id;
                                        return (
                                            <button
                                                key={cat.id}
                                                type="button"
                                                onClick={() => setCategoryId(isSelected ? '' : cat.id)}
                                                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                                                    isSelected
                                                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-[0_0_15px_rgba(229,169,60,0.25)] ring-1 ring-amber-500/30'
                                                        : 'bg-white/[0.03] text-gray-400 border-white/[0.06] hover:bg-white/[0.08] hover:text-white'
                                                }`}
                                            >
                                                {isSelected && <Check size={12} className="text-amber-400" />}
                                                {cat.name}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Sinopsis Drama */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
                                    <Layers size={14} className="text-amber-400" />
                                    Sinopsis & Alur Cerita
                                </label>
                                <div className="text-[11px] text-gray-500 font-mono space-x-2">
                                    <span>{synopsisWordCount} kata</span>
                                    <span>•</span>
                                    <span>{synopsisCharCount} karakter</span>
                                </div>
                            </div>
                            <textarea
                                value={synopsis}
                                onChange={(e) => setSynopsis(e.target.value)}
                                rows={7}
                                placeholder="Tuliskan sinopsis lengkap alur cerita drama ini..."
                                className="w-full px-4 py-3 rounded-xl bg-black/40 border border-white/[0.09] focus:border-amber-500/60 focus:ring-1 focus:ring-amber-500/30 focus:outline-none text-xs leading-relaxed text-gray-200 placeholder-gray-600 resize-y transition-all font-sans"
                            />
                        </div>
                    </div>

                    {/* Card 2: Status & Metrik Penayangan */}
                    <div className="glass-panel rounded-2xl border border-white/[0.08] p-6 space-y-6">
                        <div className="flex items-center gap-2 pb-3 border-b border-white/[0.06]">
                            <Sparkles size={16} className="text-amber-400" />
                            <h3 className="text-sm font-bold text-white tracking-tight">Status & Metrik Penayangan</h3>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                            {/* Status Publikasi */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-300">
                                    Status Publikasi
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setIsPublished(true)}
                                        className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all flex items-center justify-center gap-1.5 ${
                                            isPublished
                                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                                                : 'bg-white/[0.02] text-gray-500 border-white/[0.06] hover:bg-white/[0.05]'
                                        }`}
                                    >
                                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                                        Published
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setIsPublished(false)}
                                        className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all flex items-center justify-center gap-1.5 ${
                                            !isPublished
                                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_15px_rgba(229,169,60,0.2)]'
                                                : 'bg-white/[0.02] text-gray-500 border-white/[0.06] hover:bg-white/[0.05]'
                                        }`}
                                    >
                                        <span className="w-2 h-2 rounded-full bg-amber-400" />
                                        Draft
                                    </button>
                                </div>
                            </div>

                            {/* Status Rilis */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-300">
                                    Status Rilis
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setReleaseStatus('ongoing')}
                                        className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all flex items-center justify-center gap-1.5 ${
                                            releaseStatus === 'ongoing'
                                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                                                : 'bg-white/[0.02] text-gray-500 border-white/[0.06] hover:bg-white/[0.05]'
                                        }`}
                                    >
                                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                        Ongoing
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setReleaseStatus('completed')}
                                        className={`py-2.5 px-3 rounded-xl text-xs font-bold border transition-all flex items-center justify-center gap-1.5 ${
                                            releaseStatus === 'completed'
                                                ? 'bg-blue-500/20 text-blue-300 border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                                                : 'bg-white/[0.02] text-gray-500 border-white/[0.06] hover:bg-white/[0.05]'
                                        }`}
                                    >
                                        Tamat
                                    </button>
                                </div>
                            </div>

                            {/* Total Episodes */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-300">
                                    Total Episode
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    value={totalEpisodes}
                                    onChange={(e) => setTotalEpisodes(Number(e.target.value))}
                                    className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-white/[0.09] focus:border-amber-500/60 focus:outline-none text-xs text-white font-mono"
                                />
                            </div>

                            {/* Views di Aplikasi (Public Heat) */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-300 flex items-center gap-1">
                                    <Sparkles size={12} className="text-amber-400" />
                                    Views Aplikasi (Public Heat)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    value={viewCount}
                                    onChange={(e) => setViewCount(Number(e.target.value))}
                                    className="w-full px-4 py-2.5 rounded-xl bg-black/40 border border-white/[0.09] focus:border-amber-500/60 focus:outline-none text-xs text-white font-mono"
                                />
                            </div>
                        </div>

                        {/* Read-Only Stats Info */}
                        <div className="pt-4 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-4 text-xs text-gray-400">
                            <div className="flex items-center gap-2">
                                <Eye size={13} className="text-emerald-400" />
                                <span>Real Organik Tontonan:</span>
                                <strong className="text-emerald-300 font-mono">
                                    {realViewCount.toLocaleString()} tontonan
                                </strong>
                            </div>

                            {createdAt && (
                                <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-mono">
                                    <Clock size={11} />
                                    <span>Dibuat: {new Date(createdAt).toLocaleDateString('id-ID')}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Bottom Save Bar for Convenience */}
                    <div className="p-4 rounded-2xl glass-panel border border-white/[0.08] flex items-center justify-between gap-4">
                        <p className="text-xs text-gray-400">
                            Perubahan akan langsung ter-sinkronisasi ke web dan aplikasi.
                        </p>
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-400 hover:from-amber-400 hover:to-yellow-300 text-black text-xs font-bold shadow-[0_0_20px_rgba(229,169,60,0.3)] transition-all transform active:scale-95 disabled:opacity-50"
                        >
                            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                            Simpan Sekarang
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
