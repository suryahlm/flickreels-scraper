'use client';

import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, FolderOpen, GripVertical, Check, X, Tag } from 'lucide-react';
import { type Category } from '@/lib/supabase';
import { 
    fetchCategoriesAdmin, 
    addCategoryAdmin, 
    updateCategoryAdmin, 
    deleteCategoryAdmin 
} from './actions';

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [newCategory, setNewCategory] = useState('');
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editName, setEditName] = useState('');

    useEffect(() => {
        fetchCategories();
    }, []);

    async function fetchCategories() {
        setLoading(true);
        const res = await fetchCategoriesAdmin();
        setCategories((res.data || []) as Category[]);
        setLoading(false);
    }

    const addCategory = async () => {
        if (!newCategory.trim()) return;
        const res = await addCategoryAdmin(newCategory.trim(), categories.length + 1);

        if (!res.success) return alert('Error: ' + res.error);
        if (res.data) setCategories([...categories, res.data as Category]);
        setNewCategory('');
    };

    const handleStartEdit = (cat: Category) => {
        setEditingId(cat.id);
        setEditName(cat.name);
    };

    const handleSaveEdit = async (id: string) => {
        if (!editName.trim()) return;
        const res = await updateCategoryAdmin(id, editName.trim());

        if (!res.success) return alert('Gagal update: ' + res.error);
        const slug = editName.toLowerCase().trim().replace(/\s+/g, '-');
        setCategories(categories.map(c => c.id === id ? { ...c, name: editName.trim(), slug } : c));
        setEditingId(null);
    };

    const deleteCategory = async (id: string) => {
        if (!confirm('Yakin hapus kategori ini? Drama dalam kategori ini tidak akan terhapus.')) return;
        const res = await deleteCategoryAdmin(id);
        if (!res.success) return alert('Gagal hapus: ' + res.error);
        setCategories(categories.filter((c) => c.id !== id));
    };


    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-10 h-10 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-center justify-center p-2">
                        <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="text-xs font-semibold text-gray-400">Memuat kategori...</p>
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
                        <FolderOpen size={20} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-tight">Kategori & Taksonomi Genre</h2>
                        <p className="text-xs text-gray-400">Kelola daftar genre drama yang ditampilkan pada navigasi aplikasi</p>
                    </div>
                </div>

                <span className="px-3 py-1.5 bg-amber-500/10 text-amber-300 rounded-xl text-xs font-bold border border-amber-500/25">
                    {categories.length} Kategori Aktif
                </span>
            </div>

            {/* Quick Add Form Box */}
            <div className="glass-card-static rounded-2xl border border-white/[0.08] p-5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">Tambah Kategori Baru</h3>
                <div className="flex gap-3">
                    <div className="relative flex-1">
                        <Tag className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                        <input
                            type="text"
                            placeholder="Ketik nama kategori baru (contoh: Romantis, CEO, Wuxia)..."
                            value={newCategory}
                            onChange={(e) => setNewCategory(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && addCategory()}
                            className="w-full glass-input rounded-xl pl-10 pr-4 py-3 text-sm focus:border-amber-400"
                        />
                    </div>
                    <button
                        onClick={addCategory}
                        className="gold-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 group flex-shrink-0"
                    >
                        <Plus size={16} className="text-[#07090E]" />
                        <span>Tambah Kategori</span>
                    </button>
                </div>
            </div>

            {/* Categories Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categories.map((cat, idx) => {
                    const isEditing = editingId === cat.id;
                    return (
                        <div
                            key={cat.id}
                            className="glass-card rounded-2xl border border-white/[0.08] p-4.5 flex flex-col justify-between group hover:border-amber-500/30 transition-all"
                        >
                            <div className="flex items-start justify-between gap-3 mb-3">
                                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                                    <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center font-bold text-xs text-amber-400 flex-shrink-0">
                                        #{idx + 1}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        {isEditing ? (
                                            <input
                                                type="text"
                                                value={editName}
                                                onChange={(e) => setEditName(e.target.value)}
                                                className="w-full glass-input rounded-lg px-2.5 py-1 text-xs focus:border-amber-400 font-bold"
                                                autoFocus
                                            />
                                        ) : (
                                            <>
                                                <h4 className="text-sm font-bold text-white truncate group-hover:text-amber-300 transition-colors">
                                                    {cat.name}
                                                </h4>
                                                <p className="text-[11px] font-mono text-gray-500 mt-0.5">
                                                    /{cat.slug}
                                                </p>
                                            </>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center gap-1">
                                    {isEditing ? (
                                        <>
                                            <button
                                                onClick={() => handleSaveEdit(cat.id)}
                                                className="p-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300"
                                                title="Simpan"
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                onClick={() => setEditingId(null)}
                                                className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-gray-400"
                                                title="Batal"
                                            >
                                                <X size={14} />
                                            </button>
                                        </>
                                    ) : (
                                        <>
                                            <button
                                                onClick={() => handleStartEdit(cat)}
                                                className="p-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] text-gray-400 hover:text-white"
                                                title="Edit Nama"
                                            >
                                                <Edit2 size={13} />
                                            </button>
                                            <button
                                                onClick={() => deleteCategory(cat.id)}
                                                className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400"
                                                title="Hapus Kategori"
                                            >
                                                <Trash2 size={13} />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-gray-500">
                                <span>Urutan Display: {cat.display_order}</span>
                                <span className="font-mono text-[10px] text-gray-600 truncate max-w-[120px]">
                                    ID: {cat.id.slice(0, 8)}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
