'use client';

import { supabase, type Drama } from '@/lib/supabase';
import { GripVertical, Plus, Search, Star, Trash2, Save } from 'lucide-react';
import { useEffect, useState } from 'react';

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

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        try {
            // Fetch current featured list
            const featuredRes = await fetch('/api/featured');
            const featuredData = await featuredRes.json();

            // Fetch all dramas for search/add
            const { data: dramas } = await supabase
                .from('dramas')
                .select('*')
                .eq('is_published', true)
                .order('title');

            setFeatured(featuredData.featured || []);
            setAllDramas(dramas || []);
        } catch (e) {
            console.error('Failed to load:', e);
        } finally {
            setLoading(false);
        }
    }

    // Dramas available to add (not already featured)
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
            alert('Featured drama berhasil disimpan!');
        } catch (e: any) {
            alert('Error: ' + e.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Star className="text-amber-500" size={24} />
                        Featured Drama
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Pilih dan atur urutan 18 drama yang tampil di tab Home
                    </p>
                </div>
                <button
                    onClick={saveFeatured}
                    disabled={!hasChanges || saving}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium transition-all ${hasChanges
                        ? 'bg-amber-500 hover:bg-amber-600 text-black'
                        : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        }`}
                >
                    <Save size={18} />
                    {saving ? 'Menyimpan...' : 'Simpan'}
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Featured List */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
                    <h2 className="text-lg font-semibold mb-3 flex items-center justify-between">
                        <span>🏠 Drama di Home ({featured.length}/18)</span>
                        {hasChanges && (
                            <span className="text-xs text-amber-400 bg-amber-900/30 px-2 py-1 rounded">
                                Belum disimpan
                            </span>
                        )}
                    </h2>

                    {featured.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <Star size={48} className="mx-auto mb-3 opacity-30" />
                            <p>Belum ada drama featured</p>
                            <p className="text-sm">Cari dan tambahkan dari panel kanan →</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {featured.map((item, index) => (
                                <div
                                    key={item.drama_id}
                                    className="flex items-center gap-3 bg-gray-800 rounded-lg px-3 py-2.5 group hover:bg-gray-750"
                                >
                                    <GripVertical size={16} className="text-gray-600" />
                                    <span className="text-amber-500 font-bold text-sm w-6">
                                        {index + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">
                                            {item.drama?.title || item.drama_id}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            {item.drama?.total_episodes || '?'} episodes
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => moveUp(index)}
                                            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
                                            title="Naik"
                                        >
                                            ↑
                                        </button>
                                        <button
                                            onClick={() => moveDown(index)}
                                            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
                                            title="Turun"
                                        >
                                            ↓
                                        </button>
                                        <button
                                            onClick={() => removeDrama(index)}
                                            className="p-1 hover:bg-red-900 rounded text-red-400"
                                            title="Hapus"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Drama Search/Add */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
                    <h2 className="text-lg font-semibold mb-3">➕ Tambah Drama</h2>

                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                        <input
                            type="text"
                            placeholder="Cari drama..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-amber-500 text-sm"
                        />
                    </div>

                    <div className="max-h-[500px] overflow-y-auto space-y-1">
                        {availableDramas.slice(0, 50).map(drama => {
                            const dramaId = (drama as any).flickreels_id || drama.id;
                            return (
                                <button
                                    key={dramaId}
                                    onClick={() => addDrama(drama)}
                                    disabled={featured.length >= 18}
                                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-left group"
                                >
                                    <Plus
                                        size={16}
                                        className={`${featured.length >= 18 ? 'text-gray-600' : 'text-amber-500 group-hover:scale-110'} transition-transform`}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm truncate">{drama.title}</p>
                                        <p className="text-xs text-gray-500">
                                            {drama.total_episodes} eps
                                        </p>
                                    </div>
                                </button>
                            );
                        })}
                        {availableDramas.length === 0 && search && (
                            <p className="text-center py-8 text-gray-500 text-sm">
                                Tidak ditemukan drama &quot;{search}&quot;
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
