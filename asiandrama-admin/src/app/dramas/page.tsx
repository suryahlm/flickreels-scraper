'use client';

import { supabase, type Category, type Drama } from '@/lib/supabase';
import { Edit, Eye, EyeOff, Plus, Search, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function DramasPage() {
    const [search, setSearch] = useState('');
    const [dramas, setDramas] = useState<Drama[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newDrama, setNewDrama] = useState({ title: '', synopsis: '', category_id: '' });

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

    const filteredDramas = dramas.filter((d) =>
        d.title.toLowerCase().includes(search.toLowerCase())
    );

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
            <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                <input
                    type="text"
                    placeholder="Cari drama..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-amber-500"
                />
            </div>

            {/* Table */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <table className="w-full">
                    <thead className="bg-gray-800">
                        <tr>
                            <th className="text-left px-4 py-3 w-12">No.</th>
                            <th className="text-left px-4 py-3">Judul</th>
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
                                <td colSpan={7} className="text-center py-8 text-gray-500">
                                    Belum ada drama
                                </td>
                            </tr>
                        ) : (
                            filteredDramas.map((drama, index) => (
                                <tr key={drama.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                                    <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                                    <td className="px-4 py-3 font-medium">{drama.title}</td>
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
                            ))
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
