'use client';

import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2, GripVertical } from 'lucide-react';
import { supabase, type Category } from '@/lib/supabase';

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [newCategory, setNewCategory] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchCategories();
    }, []);

    async function fetchCategories() {
        setLoading(true);
        const { data } = await supabase
            .from('categories')
            .select('*')
            .order('display_order');
        setCategories(data || []);
        setLoading(false);
    }

    const addCategory = async () => {
        if (!newCategory.trim()) return;
        const slug = newCategory.toLowerCase().replace(/\s+/g, '-');
        const { data, error } = await supabase
            .from('categories')
            .insert({
                name: newCategory,
                slug,
                display_order: categories.length + 1,
            })
            .select()
            .single();

        if (error) return alert('Error: ' + error.message);
        setCategories([...categories, data]);
        setNewCategory('');
    };

    const deleteCategory = async (id: string) => {
        if (!confirm('Yakin hapus kategori ini?')) return;
        await supabase.from('categories').delete().eq('id', id);
        setCategories(categories.filter((c) => c.id !== id));
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div>
            <h1 className="text-2xl font-bold mb-6">Kategori Management</h1>

            {/* Add New */}
            <div className="flex gap-3 mb-6">
                <input
                    type="text"
                    placeholder="Nama kategori baru..."
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addCategory()}
                    className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                />
                <button
                    onClick={addCategory}
                    className="bg-amber-500 hover:bg-amber-600 px-4 py-2 rounded-lg flex items-center gap-2"
                >
                    <Plus size={20} /> Tambah
                </button>
            </div>

            {/* List */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                {categories.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">Belum ada kategori</div>
                ) : (
                    categories.map((cat) => (
                        <div
                            key={cat.id}
                            className="flex items-center justify-between px-4 py-3 border-b border-gray-800 last:border-0 hover:bg-gray-800/50"
                        >
                            <div className="flex items-center gap-3">
                                <GripVertical className="text-gray-600 cursor-grab" size={20} />
                                <div>
                                    <p className="font-medium">{cat.name}</p>
                                    <p className="text-xs text-gray-500">/{cat.slug}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button className="p-2 hover:bg-gray-700 rounded" title="Edit">
                                    <Edit size={18} />
                                </button>
                                <button
                                    onClick={() => deleteCategory(cat.id)}
                                    className="p-2 hover:bg-red-900 rounded text-red-400"
                                    title="Delete"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
