'use client';

import { supabase, type Drama } from '@/lib/supabase';
import { GripVertical, Plus, Search, Star, Trash2, Save, ArrowUp, ArrowDown, Sparkles, CheckCircle2 } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';

interface FeaturedItem {
    drama_id: string;
    display_order: number;
    drama: { title: string; total_episodes: number; r2_folder: string } | null;
}

export default function FeaturedPage() {
    const [featured, setFeatured] = useState<FeaturedItem[]>([]);
    const [allDramas, setAllDramas] = useState<Drama[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    const dragItem = useRef<number | null>(null);
    const dragOverItem = useRef<number | null>(null);

    const handleSort = () => {
        if (dragItem.current !== null && dragOverItem.current !== null && dragItem.current !== dragOverItem.current) {
            let _featured = [...featured];
            const draggedItemContent = _featured.splice(dragItem.current, 1)[0];
            _featured.splice(dragOverItem.current, 0, draggedItemContent);
            setFeatured(_featured);
            setHasChanges(true);
        }
        dragItem.current = null;
        dragOverItem.current = null;
    };

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        try {
            const featuredRes = await fetch('/api/featured');
            const featuredData = await featuredRes.json();

            setFeatured(featuredData.featured || []);
            setAllDramas(featuredData.allDramas || []);
        } catch (e) {
            console.error('Failed to load:', e);
        } finally {
            setLoading(false);
        }
    }


    const featuredIds = new Set(featured.map(f => f.drama_id));
    const availableDramas = allDramas.filter(d => {
        const dramaId = (d as any).flickreels_id || d.id;
        return !featuredIds.has(dramaId) &&
            d.title.toLowerCase().includes(search.toLowerCase());
    });

    const addDrama = (drama: Drama) => {
        if (featured.length >= 18) {
            alert('Maksimal 18 drama featured!');
            return;
        }
        const dramaId = (drama as any).flickreels_id || drama.id;
        setFeatured(prev => [...prev, {
            drama_id: dramaId,
            display_order: prev.length + 1,
            drama: {
                title: drama.title,
                total_episodes: drama.total_episodes,
                r2_folder: (drama as any).r2_folder || '',
            },
        }]);
        setHasChanges(true);
    };

    const removeDrama = (index: number) => {
        setFeatured(prev => prev.filter((_, i) => i !== index));
        setHasChanges(true);
    };

    const moveUp = (index: number) => {
        if (index === 0) return;
        setFeatured(prev => {
            const copy = [...prev];
            [copy[index - 1], copy[index]] = [copy[index], copy[index - 1]];
            return copy;
        });
        setHasChanges(true);
    };

    const moveDown = (index: number) => {
        if (index === featured.length - 1) return;
        setFeatured(prev => {
            const copy = [...prev];
            [copy[index], copy[index + 1]] = [copy[index + 1], copy[index]];
            return copy;
        });
        setHasChanges(true);
    };

    const saveFeatured = async () => {
        setSaving(true);
        try {
            const items = featured.map(f => f.drama_id);
            const res = await fetch('/api/featured', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items }),
            });

            if (!res.ok) {
                const err = await res.json();
                alert('Gagal menyimpan: ' + (err.error || 'Unknown error'));
                return;
            }

            setHasChanges(false);
            alert('Featured drama berhasil disimpan dan live di aplikasi!');
        } catch (e: any) {
            alert('Error: ' + e.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center p-2">
                        <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="text-xs font-semibold text-gray-400">Memuat kurasi featured...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/[0.08]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                        <Star size={20} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Featured Drama Curator</h2>
                        <p className="text-xs text-gray-400">Susun urutan 18 tayangan utama di baris beranda aplikasi</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {hasChanges && (
                        <span className="px-3 py-1.5 bg-amber-500/15 border border-amber-500/30 text-amber-300 rounded-xl text-xs font-bold flex items-center gap-1.5 animate-pulse">
                            <span className="w-2 h-2 rounded-full bg-amber-400" />
                            Perubahan Belum Disimpan
                        </span>
                    )}
                    <button
                        onClick={saveFeatured}
                        disabled={!hasChanges || saving}
                        className={`gold-btn px-5 py-2 rounded-xl text-xs flex items-center gap-2 ${
                            !hasChanges && 'opacity-40 cursor-not-allowed filter grayscale'
                        }`}
                    >
                        <Save size={15} />
                        <span>{saving ? 'Menyimpan...' : 'Simpan Urutan'}</span>
                    </button>
                </div>
            </div>

            {/* Dual Pane Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Pane: Current Featured (1-18) */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-5 flex flex-col">
                    <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.07]">
                        <div>
                            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                                <span>Drama Terpilih di Beranda</span>
                                <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold">
                                    {featured.length}/18
                                </span>
                            </h3>
                            <p className="text-[11px] text-gray-400">Drag atau klik panah untuk mengatur urutan tayang</p>
                        </div>
                    </div>

                    <div className="flex-1">
                        {featured.length === 0 ? (
                            <div className="text-center py-20 text-gray-500">
                                <Star size={40} className="mx-auto mb-3 opacity-30 text-amber-400" />
                                <p className="text-xs font-semibold text-white">Belum ada drama featured</p>
                                <p className="text-[11px] text-gray-400 mt-1">Cari dan tambahkan drama dari panel katalog di samping →</p>
                            </div>
                        ) : (
                            <div className="space-y-2.5">
                                {featured.map((item, index) => (
                                    <div
                                        key={item.drama_id}
                                        draggable
                                        onDragStart={() => dragItem.current = index}
                                        onDragEnter={() => dragOverItem.current = index}
                                        onDragEnd={handleSort}
                                        onDragOver={(e) => e.preventDefault()}
                                        className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.05] hover:border-amber-500/30 cursor-move transition-all group"
                                    >
                                        <div className="cursor-grab active:cursor-grabbing text-gray-500 hover:text-amber-400">
                                            <GripVertical size={16} />
                                        </div>

                                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                                            index < 3
                                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-[0_0_8px_rgba(229,169,60,0.2)]'
                                                : 'bg-white/[0.04] text-gray-400 border border-white/[0.06]'
                                        }`}>
                                            {index + 1}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-bold text-white truncate group-hover:text-amber-300 transition-colors">
                                                {item.drama?.title || item.drama_id}
                                            </p>
                                            <p className="text-[10px] text-gray-500 mt-0.5">
                                                {item.drama?.total_episodes || '?'} episode
                                            </p>
                                        </div>

                                        <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => moveUp(index)}
                                                className="p-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] text-gray-400 hover:text-white"
                                                title="Pindah ke Atas"
                                            >
                                                <ArrowUp size={13} />
                                            </button>
                                            <button
                                                onClick={() => moveDown(index)}
                                                className="p-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] text-gray-400 hover:text-white"
                                                title="Pindah ke Bawah"
                                            >
                                                <ArrowDown size={13} />
                                            </button>
                                            <button
                                                onClick={() => removeDrama(index)}
                                                className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400"
                                                title="Keluarkan dari Featured"
                                            >
                                                <Trash2 size={13} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Pane: Search & Add Available Dramas */}
                <div className="glass-card-static rounded-2xl border border-white/[0.08] p-5 flex flex-col">
                    <div className="pb-4 mb-4 border-b border-white/[0.07]">
                        <h3 className="text-sm font-bold text-white tracking-tight">Katalog Siap Ditambahkan</h3>
                        <p className="text-[11px] text-gray-400">Pilih dari drama yang sudah berstatus Published</p>
                    </div>

                    <div className="relative mb-4">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                        <input
                            type="text"
                            placeholder="Cari drama untuk ditambahkan..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full glass-input rounded-xl pl-10 pr-4 py-2.5 text-xs focus:border-amber-400"
                        />
                    </div>

                    <div className="flex-1 max-h-[550px] overflow-y-auto space-y-1.5 pr-1">
                        {availableDramas.slice(0, 50).map(drama => {
                            const dramaId = (drama as any).flickreels_id || drama.id;
                            const isFull = featured.length >= 18;
                            return (
                                <button
                                    key={dramaId}
                                    onClick={() => addDrama(drama)}
                                    disabled={isFull}
                                    className="w-full flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] hover:border-amber-500/30 transition-all text-left group disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform">
                                        <Plus size={14} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs font-bold text-white truncate group-hover:text-amber-300 transition-colors">
                                            {drama.title}
                                        </p>
                                        <p className="text-[10px] text-gray-500 mt-0.5">
                                            {drama.total_episodes} episode
                                        </p>
                                    </div>
                                </button>
                            );
                        })}
                        {availableDramas.length === 0 && search && (
                            <div className="text-center py-12 text-xs text-gray-500">
                                Tidak ditemukan judul yang cocok dengan &quot;{search}&quot;
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
