'use client';

import { useState } from 'react';
import { Plus, Trash2, Eye, EyeOff, GripVertical } from 'lucide-react';

const bannersData = [
    { id: '1', image: '/banner1.jpg', drama: 'Jagal Tak Terkalahkan', active: true, order: 1 },
    { id: '2', image: '/banner2.jpg', drama: 'Cinta Rahasia CEO', active: true, order: 2 },
    { id: '3', image: '/banner3.jpg', drama: null, active: false, order: 3 },
];

export default function BannersPage() {
    const [banners, setBanners] = useState(bannersData);

    const toggleActive = (id: string) => {
        setBanners((prev) =>
            prev.map((b) => (b.id === id ? { ...b, active: !b.active } : b))
        );
    };

    const deleteBanner = (id: string) => {
        if (confirm('Yakin hapus banner ini?')) {
            setBanners(banners.filter((b) => b.id !== id));
        }
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold">Banner Management</h1>
                <button className="bg-amber-500 hover:bg-amber-600 px-4 py-2 rounded-lg flex items-center gap-2">
                    <Plus size={20} /> Upload Banner
                </button>
            </div>

            {/* Banner Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {banners.map((banner) => (
                    <div
                        key={banner.id}
                        className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden"
                    >
                        {/* Banner Preview */}
                        <div className="aspect-video bg-gray-800 flex items-center justify-center">
                            <span className="text-gray-600">Banner Preview</span>
                        </div>

                        {/* Info */}
                        <div className="p-4">
                            <p className="text-sm text-gray-400 mb-2">
                                Link: {banner.drama || 'Tidak ada link'}
                            </p>
                            <div className="flex items-center justify-between">
                                <span
                                    className={`px-2 py-1 rounded text-xs ${banner.active ? 'bg-green-900 text-green-400' : 'bg-gray-700 text-gray-400'
                                        }`}
                                >
                                    {banner.active ? 'Active' : 'Inactive'}
                                </span>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => toggleActive(banner.id)}
                                        className="p-2 hover:bg-gray-700 rounded"
                                    >
                                        {banner.active ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                    <button
                                        onClick={() => deleteBanner(banner.id)}
                                        className="p-2 hover:bg-red-900 rounded text-red-400"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
