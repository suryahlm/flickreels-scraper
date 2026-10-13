'use client';

import { type Category, type Drama } from '@/lib/supabase';
import { fetchDramasCatalogAdmin } from './actions';
import { Edit, Eye, EyeOff, Filter, Plus, Search, Trash2, X, Film, FolderCheck, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';


// ── Source detection from r2_folder ──
const SOURCES = ['FlickReels', 'DramaBox', 'Melolo', 'Netshort', 'DramaNova'] as const;
type Source = (typeof SOURCES)[number];

const SOURCE_COLORS: Record<Source, string> = {
    FlickReels: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
    DramaBox: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    Melolo: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    Netshort: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    DramaNova: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

function getSource(r2_folder: string | null | undefined): Source {
    if (r2_folder?.startsWith('dramanova/')) return 'DramaNova';
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
    const [filterStatus, setFilterStatus] = useState<string>('published');
    const [filterReleaseStatus, setFilterReleaseStatus] = useState<string>('all');
    const [filterCategory, setFilterCategory] = useState<string>('all');

    useEffect(() => {
        fetchData();
    }, []);

    async function fetchData() {
        setLoading(true);
        const res = await fetchDramasCatalogAdmin();
        setDramas(res.dramas || []);
        setCategories(res.categories || []);
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

    // Release status counts
    const releaseStatusCounts = useMemo(() => ({
        all: dramas.length,
        ongoing: dramas.filter((d) => d.release_status === 'ongoing').length,
        completed: dramas.filter((d) => d.release_status !== 'ongoing').length,
    }), [dramas]);

    // Multi-filter
    const filteredDramas = useMemo(() => dramas.filter((d) => {
        const matchSearch = d.title.toLowerCase().includes(search.toLowerCase());
        const matchSource = filterSource === 'all' || getSource(d.r2_folder) === filterSource;
        const matchStatus = filterStatus === 'all'
            || (filterStatus === 'published' && d.is_published)
            || (filterStatus === 'draft' && !d.is_published);
        const matchRelease = filterReleaseStatus === 'all'
            || (filterReleaseStatus === 'ongoing' && d.release_status === 'ongoing')
            || (filterReleaseStatus === 'completed' && d.release_status !== 'ongoing');
        const matchCategory = filterCategory === 'all' || d.category_id === filterCategory;
        return matchSearch && matchSource && matchStatus && matchRelease && matchCategory;
    }), [dramas, search, filterSource, filterStatus, filterReleaseStatus, filterCategory]);

    const hasActiveFilter = filterSource !== 'all' || filterStatus !== 'published' || filterReleaseStatus !== 'all' || filterCategory !== 'all';

    const clearFilters = () => {
        setFilterSource('all');
        setFilterStatus('published');
        setFilterReleaseStatus('all');
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
        if (!confirm('Yakin hapus drama ini? Tindakan tidak dapat dibatalkan.')) return;
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

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center p-2">
                        <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="text-xs font-semibold text-gray-400">Memuat katalog drama...</p>
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
                        <Film size={20} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Katalog Master Drama</h2>
                        <p className="text-xs text-gray-400">Total {statusCounts.published} judul aktif dipublikasikan ({dramas.length} di database)</p>
                    </div>
                </div>

                <button
                    onClick={() => setShowAddModal(true)}
                    className="gold-btn px-4 py-2 rounded-xl text-xs flex items-center gap-2 group"
                >
                    <Plus size={16} className="text-[#07090E]" />
                    <span>Tambah Drama Baru</span>
                </button>
            </div>

            {/* Search Input Bar */}
            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                    type="text"
                    placeholder="Cari berdasarkan judul drama..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full glass-input rounded-2xl pl-12 pr-10 py-3.5 text-sm focus:border-amber-400"
                />
                {search && (
                    <button
                        onClick={() => setSearch('')}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                    >
                        <X size={16} />
                    </button>
                )}
            </div>

            {/* Multi-Filters Box */}
            <div className="glass-card-static rounded-2xl border border-white/[0.08] p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2 text-xs font-bold text-gray-300 uppercase tracking-wider">
                        <Filter size={14} className="text-amber-400" />
                        <span>Filter Katalog</span>
                    </div>
                    {hasActiveFilter && (
                        <button
                            onClick={clearFilters}
                            className="text-xs text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 transition-colors"
                        >
                            <X size={13} />
                            Reset Filter
                        </button>
                    )}
                </div>

                {/* Source Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-gray-400 w-20 shrink-0">Sumber:</span>
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
                    <span className="text-xs font-semibold text-gray-400 w-20 shrink-0">Status:</span>
                    <FilterButton
                        active={filterStatus === 'published'}
                        onClick={() => setFilterStatus('published')}
                        count={statusCounts.published}
                        color="bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                    >
                        Published
                    </FilterButton>
                    <FilterButton
                        active={filterStatus === 'draft'}
                        onClick={() => setFilterStatus('draft')}
                        count={statusCounts.draft}
                        color="bg-amber-500/15 text-amber-300 border-amber-500/30"
                    >
                        Draft
                    </FilterButton>
                    <FilterButton
                        active={filterStatus === 'all'}
                        onClick={() => setFilterStatus('all')}
                        count={statusCounts.all}
                    >
                        Semua
                    </FilterButton>
                </div>

                {/* Release Status Filter (Ongoing vs Tamat) */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-gray-400 w-20 shrink-0">Status Rilis:</span>
                    <FilterButton
                        active={filterReleaseStatus === 'all'}
                        onClick={() => setFilterReleaseStatus('all')}
                        count={releaseStatusCounts.all}
                    >
                        Semua
                    </FilterButton>
                    <FilterButton
                        active={filterReleaseStatus === 'ongoing'}
                        onClick={() => setFilterReleaseStatus('ongoing')}
                        count={releaseStatusCounts.ongoing}
                        color="bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                    >
                        ● Ongoing
                    </FilterButton>
                    <FilterButton
                        active={filterReleaseStatus === 'completed'}
                        onClick={() => setFilterReleaseStatus('completed')}
                        count={releaseStatusCounts.completed}
                        color="bg-gray-500/15 text-gray-300 border-gray-500/30"
                    >
                        Tamat
                    </FilterButton>
                </div>

                {/* Category Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-gray-400 w-20 shrink-0">Kategori:</span>
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

            {/* Result Counter */}
            <div className="flex items-center justify-between text-xs text-gray-400 px-1 font-medium">
                <span>
                    Menampilkan <strong className="text-white">{filteredDramas.length}</strong> judul
                    {filterStatus === 'published' && <span className="text-emerald-400/90 ml-1.5 font-semibold">● Dipublikasikan ({statusCounts.published})</span>}
                    {filterStatus === 'draft' && <span className="text-amber-400/90 ml-1.5 font-semibold">● Masih Draft ({statusCounts.draft})</span>}
                    {filterStatus === 'all' && <span className="text-gray-400 ml-1.5 font-semibold">● Semua Status ({statusCounts.all})</span>}
                </span>
            </div>

            {/* Table Container */}
            <div className="glass-card-static rounded-2xl border border-white/[0.08] overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white/[0.02] border-b border-white/[0.07] text-[11px] font-bold uppercase tracking-wider text-gray-400">
                                <th className="px-5 py-4 w-12 text-center">#</th>
                                <th className="px-5 py-4 min-w-[240px]">Judul Drama</th>
                                <th className="px-5 py-4 whitespace-nowrap">Asal Sumber</th>
                                <th className="px-5 py-4 whitespace-nowrap">Kategori Genre</th>
                                <th className="px-5 py-4 text-center whitespace-nowrap">Episode</th>
                                <th className="px-5 py-4 text-center whitespace-nowrap">Penayangan</th>
                                <th className="px-5 py-4 text-center whitespace-nowrap">Status</th>
                                <th className="px-5 py-4 text-right whitespace-nowrap">Aksi</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04]">
                            {filteredDramas.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="text-center py-16 text-xs text-gray-500">
                                        {hasActiveFilter ? 'Tidak ada drama yang cocok dengan kriteria filter' : 'Belum ada drama terdaftar'}
                                    </td>
                                </tr>
                            ) : (
                                filteredDramas.map((drama, index) => {
                                    const source = getSource(drama.r2_folder);
                                    return (
                                        <tr key={drama.id} className="hover:bg-white/[0.03] transition-colors group">
                                            <td className="px-5 py-4 text-xs font-mono text-gray-500 text-center">{index + 1}</td>
                                            <td className="px-5 py-4">
                                                <p className="text-xs font-bold text-white group-hover:text-amber-300 transition-colors">
                                                    {drama.title}
                                                </p>
                                                <p className="text-[10px] text-gray-500 font-mono mt-0.5">
                                                    {drama.r2_folder || drama.id.slice(0, 10)}
                                                </p>
                                            </td>
                                            <td className="px-5 py-4 whitespace-nowrap">
                                                <span className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${SOURCE_COLORS[source]}`}>
                                                    {source}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 text-xs text-gray-400 whitespace-nowrap">
                                                <span className="px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[11px] font-medium">
                                                    {getCategoryName(drama.category_id)}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 text-center whitespace-nowrap">
                                                <div className="flex flex-col items-center gap-1">
                                                    <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-bold whitespace-nowrap">
                                                        {drama.total_episodes} eps
                                                    </span>
                                                    {drama.release_status === 'ongoing' ? (
                                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
                                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                                            Ongoing
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.08] text-gray-400 text-[10px] font-medium">
                                                            Tamat
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-5 py-4 text-center whitespace-nowrap">
                                                <div className="flex flex-col items-center gap-1">
                                                    <div className="flex items-center gap-1 text-xs font-bold text-amber-300" title="Views di Aplikasi (Public Heat Score)">
                                                        <Sparkles size={12} className="text-amber-400 shrink-0" />
                                                        <span>{(drama.view_count || 0).toLocaleString()}</span>
                                                        <span className="text-[10px] font-normal text-gray-400">app</span>
                                                    </div>
                                                    <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400/90" title="Views Real Organik (Tontonan Pengguna Real)">
                                                        <Eye size={11} className="text-emerald-400 shrink-0" />
                                                        <span>{(drama.real_view_count || 0).toLocaleString()}</span>
                                                        <span className="text-[10px] font-normal text-gray-400">real</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-5 py-4 text-center whitespace-nowrap">
                                                <span
                                                    className={`inline-flex items-center justify-center px-3 py-1 rounded-lg text-xs font-bold border whitespace-nowrap ${
                                                        drama.is_published
                                                            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                                            : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                                                    }`}
                                                >
                                                    {drama.is_published ? 'Published' : 'Draft'}
                                                </span>
                                            </td>
                                            <td className="px-5 py-4 text-right whitespace-nowrap">
                                                <div className="flex items-center justify-end gap-1.5">
                                                    <button
                                                        onClick={() => togglePublish(drama.id, drama.is_published)}
                                                        className={`p-2 rounded-xl border transition-all ${
                                                            drama.is_published
                                                                ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/20 text-emerald-400'
                                                                : 'bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/20 text-amber-400'
                                                        }`}
                                                        title={drama.is_published ? 'Ubah ke Draft' : 'Publikasikan Sekarang'}
                                                    >
                                                        {drama.is_published ? <EyeOff size={15} /> : <Eye size={15} />}
                                                    </button>
                                                    <button
                                                        onClick={() => deleteDrama(drama.id)}
                                                        className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 transition-all"
                                                        title="Hapus Drama"
                                                    >
                                                        <Trash2 size={15} />
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
            </div>

            {/* Add Drama Luxury Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-[#07090E]/80 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="glass-panel border border-white/[0.1] rounded-2xl p-6 w-full max-w-lg shadow-[0_20px_60px_rgba(0,0,0,0.6)]">
                        <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/[0.07]">
                            <div className="flex items-center gap-2.5">
                                <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                                    <Film size={18} />
                                </div>
                                <h3 className="text-base font-bold text-white tracking-tight">Tambah Drama Baru</h3>
                            </div>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/[0.05]"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Judul Drama *</label>
                                <input
                                    type="text"
                                    value={newDrama.title}
                                    onChange={(e) => setNewDrama({ ...newDrama, title: e.target.value })}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-sm focus:border-amber-400"
                                    placeholder="Contoh: Sang Juara Bela Diri"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Kategori Genre</label>
                                <select
                                    value={newDrama.category_id}
                                    onChange={(e) => setNewDrama({ ...newDrama, category_id: e.target.value })}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-sm focus:border-amber-400"
                                >
                                    <option value="" className="bg-[#090D15]">Pilih kategori...</option>
                                    {categories.map((cat) => (
                                        <option key={cat.id} value={cat.id} className="bg-[#090D15]">{cat.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Sinopsis</label>
                                <textarea
                                    value={newDrama.synopsis}
                                    onChange={(e) => setNewDrama({ ...newDrama, synopsis: e.target.value })}
                                    rows={3}
                                    className="w-full glass-input rounded-xl px-4 py-2.5 text-sm focus:border-amber-400"
                                    placeholder="Ringkasan cerita drama..."
                                />
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-white text-xs font-semibold transition-all"
                                >
                                    Batal
                                </button>
                                <button
                                    onClick={addDrama}
                                    className="flex-1 gold-btn py-2.5 rounded-xl text-xs font-bold"
                                >
                                    Simpan Drama
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
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${active
                ? color || 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_12px_rgba(229,169,60,0.15)]'
                : 'bg-white/[0.03] text-gray-400 border-white/[0.06] hover:border-white/[0.12] hover:text-white'
                }`}
        >
            {children}
            {count !== undefined && (
                <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] ${active ? 'bg-amber-400/20 text-amber-200' : 'bg-white/[0.06] text-gray-400'}`}>
                    {count}
                </span>
            )}
        </button>
    );
}
