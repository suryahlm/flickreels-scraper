'use client';

import { supabase, type Category, type Drama } from '@/lib/supabase';
import { Edit, Eye, EyeOff, Filter, Plus, Search, Trash2, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

// ── Source detection from r2_folder ──
const SOURCES = ['FlickReels', 'DramaBox', 'Melolo', 'Netshort'] as const;
type Source = (typeof SOURCES)[number];

const SOURCE_COLORS: Record<Source, string> = {
    FlickReels: 'bg-purple-900/60 text-purple-300 border-purple-700',
    DramaBox: 'bg-blue-900/60 text-blue-300 border-blue-700',
    Melolo: 'bg-emerald-900/60 text-emerald-300 border-emerald-700',
    Netshort: 'bg-amber-900/60 text-amber-300 border-amber-700',
};

function getSource(r2_folder: string | null | undefined): Source {
    if (r2_folder?.startsWith('netshort/')) return 'Netshort';
    if (r2_folder?.startsWith('dramabox/')) return 'DramaBox';
    if (r2_folder?.startsWith('melolo/')) return 'Melolo';
    return 'FlickReels';
}

export default function DramasPage() {
    const [search, setSearch] = useState('');
    const [dramas, setDramas] = useState<Drama[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newDrama, setNewDrama] = useState({ title: '', synopsis: '', category_id: '' });

    // Filter states
    const [filterSource, setFilterSource] = useState<string>('all');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [filterCategory, setFilterCategory] = useState<string>('all');

    useEffect(() => {
        fetchData();
    }, []);

    async function fetchData() {
        setLoading(true);
        const [dramasRes, catsRes] = await Promise.all([
            supabase.from('dramas').select('*').order('created_at', { ascending: false }),
            supabase.from('categories').select('*').order('display_order'),
        ]);
        setDramas(dramasRes.data || []);
        setCategories(catsRes.data || []);
        setLoading(false);
    }

    // Source counts for badges
    const sourceCounts = useMemo(() => {
        const counts: Record<string, number> = { all: dramas.length };
        SOURCES.forEach((s) => (counts[s] = 0));
        dramas.forEach((d) => counts[getSource(d.r2_folder)]++);
        return counts;
    }, [dramas]);

    // Status counts
    const statusCounts = useMemo(() => ({
        all: dramas.length,
        published: dramas.filter((d) => d.is_published).length,
        draft: dramas.filter((d) => !d.is_published).length,
    }), [dramas]);

    // Multi-filter
    const filteredDramas = useMemo(() => dramas.filter((d) => {
        const matchSearch = d.title.toLowerCase().includes(search.toLowerCase());
        const matchSource = filterSource === 'all' || getSource(d.r2_folder) === filterSource;
        const matchStatus = filterStatus === 'all'
            || (filterStatus === 'published' && d.is_published)
            || (filterStatus === 'draft' && !d.is_published);
        const matchCategory = filterCategory === 'all' || d.category_id === filterCategory;
        return matchSearch && matchSource && matchStatus && matchCategory;
    }), [dramas, search, filterSource, filterStatus, filterCategory]);

    const hasActiveFilter = filterSource !== 'all' || filterStatus !== 'all' || filterCategory !== 'all';

    const clearFilters = () => {
        setFilterSource('all');
        setFilterStatus('all');
        setFilterCategory('all');
    };

    const togglePublish = async (id: string, currentStatus: boolean) => {
        const res = await fetch('/api/dramas', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, is_published: !currentStatus }),
        });
        const result = await res.json();
        if (!res.ok) {
            alert('Gagal mengubah status: ' + (result.error || 'Unknown error'));
            return;
        }
        setDramas((prev) =>
            prev.map((d) => (d.id === id ? { ...d, is_published: !currentStatus } : d))
        );
    };

    const deleteDrama = async (id: string) => {
        if (!confirm('Yakin hapus drama ini?')) return;
        const res = await fetch(`/api/dramas?id=${id}`, { method: 'DELETE' });
        const result = await res.json();
        if (!res.ok) {
            alert('Gagal menghapus drama: ' + (result.error || 'Unknown error'));
            return;
        }
        setDramas((prev) => prev.filter((d) => d.id !== id));
    };

    const addDrama = async () => {
        if (!newDrama.title.trim()) return alert('Judul wajib diisi');
        const res = await fetch('/api/dramas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newDrama),
        });
        const result = await res.json();
        if (!res.ok) return alert('Error: ' + (result.error || 'Unknown error'));
        setDramas([result.drama, ...dramas]);
        setNewDrama({ title: '', synopsis: '', category_id: '' });
        setShowAddModal(false);
    };

    const getCategoryName = (catId: string | null) => {
        if (!catId) return '-';
        return categories.find((c) => c.id === catId)?.name || '-';
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Drama Management</h1>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-amber-500 hover:bg-amber-600 px-4 py-2 rounded-lg flex items-center gap-2"
                >
                    <Plus size={20} />
                    Tambah Drama
                </button>
            </div>

            {/* Search */}
            <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                    type="text"
                    placeholder="Cari drama..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-amber-500"
                />
            </div>

            {/* Filters */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4 space-y-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Filter size={16} />
                        <span>Filter</span>
                    </div>
                    {hasActiveFilter && (
                        <button
                            onClick={clearFilters}
                            className="text-xs text-gray-500 hover:text-white flex items-center gap-1"
                        >
                            <X size={14} />
                            Reset Filter
                        </button>
                    )}
                </div>

                {/* Source Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 w-16 shrink-0">Sumber:</span>
                    <FilterButton
                        active={filterSource === 'all'}
                        onClick={() => setFilterSource('all')}
                        count={sourceCounts.all}
                    >
                        Semua
                    </FilterButton>
                    {SOURCES.map((src) => (
                        <FilterButton
                            key={src}
                            active={filterSource === src}
                            onClick={() => setFilterSource(src)}
                            count={sourceCounts[src]}
                            color={SOURCE_COLORS[src]}
                        >
                            {src}
                        </FilterButton>
                    ))}
                </div>

                {/* Status Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 w-16 shrink-0">Status:</span>
                    <FilterButton
                        active={filterStatus === 'all'}
                        onClick={() => setFilterStatus('all')}
                        count={statusCounts.all}
                    >
                        Semua
                    </FilterButton>
                    <FilterButton
                        active={filterStatus === 'published'}
                        onClick={() => setFilterStatus('published')}
                        count={statusCounts.published}
                        color="bg-green-900/60 text-green-300 border-green-700"
                    >
                        Published
                    </FilterButton>
                    <FilterButton
                        active={filterStatus === 'draft'}
                        onClick={() => setFilterStatus('draft')}
                        count={statusCounts.draft}
                        color="bg-gray-700/60 text-gray-300 border-gray-600"
                    >
                        Draft
                    </FilterButton>
                </div>

                {/* Category Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 w-16 shrink-0">Kategori:</span>
                    <FilterButton
                        active={filterCategory === 'all'}
                        onClick={() => setFilterCategory('all')}
                    >
                        Semua
                    </FilterButton>
                    {categories.map((cat) => (
                        <FilterButton
                            key={cat.id}
                            active={filterCategory === cat.id}
                            onClick={() => setFilterCategory(cat.id)}
                        >
                            {cat.name}
                        </FilterButton>
                    ))}
                </div>
            </div>

            {/* Result count */}
            <div className="text-sm text-gray-500 mb-3">
                Menampilkan <span className="text-white font-medium">{filteredDramas.length}</span> dari{' '}
                <span className="text-white font-medium">{dramas.length}</span> drama
            </div>

            {/* Table */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-800">
                        <tr>
                            <th className="text-left px-4 py-3 w-12">No.</th>
                            <th className="text-left px-4 py-3">Judul</th>
                            <th className="text-left px-4 py-3">Sumber</th>
                            <th className="text-left px-4 py-3">Kategori</th>
                            <th className="text-left px-4 py-3">Episode</th>
                            <th className="text-left px-4 py-3">Views</th>
                            <th className="text-left px-4 py-3">Status</th>
                            <th className="text-left px-4 py-3">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredDramas.length === 0 ? (
                            <tr>
                                <td colSpan={8} className="text-center py-8 text-gray-500">
                                    {hasActiveFilter ? 'Tidak ada drama yang cocok dengan filter' : 'Belum ada drama'}
                                </td>
                            </tr>
                        ) : (
                            filteredDramas.map((drama, index) => {
                                const source = getSource(drama.r2_folder);
                                return (
                                    <tr key={drama.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                                        <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                                        <td className="px-4 py-3 font-medium">{drama.title}</td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-0.5 rounded text-xs border ${SOURCE_COLORS[source]}`}>
                                                {source}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-gray-400">{getCategoryName(drama.category_id)}</td>
                                        <td className="px-4 py-3 text-gray-400">{drama.total_episodes}</td>
                                        <td className="px-4 py-3 text-gray-400">{drama.view_count?.toLocaleString()}</td>
                                        <td className="px-4 py-3">
                                            <span
                                                className={`px-2 py-1 rounded text-xs ${drama.is_published ? 'bg-green-900 text-green-400' : 'bg-gray-700 text-gray-400'
                                                    }`}
                                            >
                                                {drama.is_published ? 'Published' : 'Draft'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => togglePublish(drama.id, drama.is_published)}
                                                    className="p-2 hover:bg-gray-700 rounded"
                                                    title={drama.is_published ? 'Unpublish' : 'Publish'}
                                                >
                                                    {drama.is_published ? <EyeOff size={18} /> : <Eye size={18} />}
                                                </button>
                                                <button className="p-2 hover:bg-gray-700 rounded" title="Edit">
                                                    <Edit size={18} />
                                                </button>
                                                <button
                                                    onClick={() => deleteDrama(drama.id)}
                                                    className="p-2 hover:bg-red-900 rounded text-red-400"
                                                    title="Delete"
                                                >
                                                    <Trash2 size={18} />
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

            {/* Add Drama Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md border border-gray-800">
                        <h2 className="text-xl font-bold mb-4">Tambah Drama Baru</h2>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Judul *</label>
                                <input
                                    type="text"
                                    value={newDrama.title}
                                    onChange={(e) => setNewDrama({ ...newDrama, title: e.target.value })}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-600"
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Kategori</label>
                                <select
                                    value={newDrama.category_id}
                                    onChange={(e) => setNewDrama({ ...newDrama, category_id: e.target.value })}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-600"
                                >
                                    <option value="">Pilih kategori</option>
                                    {categories.map((cat) => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Sinopsis</label>
                                <textarea
                                    value={newDrama.synopsis}
                                    onChange={(e) => setNewDrama({ ...newDrama, synopsis: e.target.value })}
                                    rows={3}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-pink-600"
                                />
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={addDrama}
                                    className="flex-1 bg-pink-600 hover:bg-pink-700 px-4 py-2 rounded-lg"
                                >
                                    Simpan
                                </button>
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg"
                                >
                                    Batal
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Filter Button Component ──
function FilterButton({
    children,
    active,
    onClick,
    count,
    color,
}: {
    children: React.ReactNode;
    active: boolean;
    onClick: () => void;
    count?: number;
    color?: string;
}) {
    return (
        <button
            onClick={onClick}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all border ${active
                ? color || 'bg-amber-600/80 text-white border-amber-500'
                : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-600 hover:text-gray-300'
                }`}
        >
            {children}
            {count !== undefined && (
                <span className={`ml-1.5 ${active ? 'opacity-80' : 'opacity-50'}`}>
                    {count}
                </span>
            )}
        </button>
    );
}
