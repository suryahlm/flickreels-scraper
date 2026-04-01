'use client';

import { useState, useEffect } from 'react';
import { Plus, Trash2, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import Image from 'next/image';

interface AppBanners {
    banner_1: string[];
    banner_2: string[];
    banner_3: string[];
    telegram_link?: string;
}

type BannerSlot = 'banner_1' | 'banner_2' | 'banner_3';

export default function BannersPage() {
    const [banners, setBanners] = useState<AppBanners>({
        banner_1: [],
        banner_2: [],
        banner_3: [],
        telegram_link: 'https://t.me/asiandrama_id',
    });
    const [originalBanners, setOriginalBanners] = useState<AppBanners | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploadingSlot, setUploadingSlot] = useState<string | null>(null);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    useEffect(() => {
        fetchBanners();
    }, []);

    const fetchBanners = async () => {
        try {
            setLoading(true);
            const res = await fetch('/api/banners');
            const raw = await res.json() as AppBanners;
            // Normalisasi: pastikan telegram_link selalu ada agar hasChanges tidak false-positive
            const data: AppBanners = {
                banner_1: raw.banner_1 || [],
                banner_2: raw.banner_2 || [],
                banner_3: raw.banner_3 || [],
                telegram_link: raw.telegram_link || 'https://t.me/asiandrama_id',
            };
            setBanners(data);
            setOriginalBanners(JSON.parse(JSON.stringify(data)));
        } catch (e) {
            console.error('Failed to load banners');
        } finally {
            setLoading(false);
        }
    };

    const hasChanges = JSON.stringify(banners) !== JSON.stringify(originalBanners);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, slot: BannerSlot) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const currentImages = banners[slot] as string[];
        if (currentImages.length >= 5) {
            setStatus({ type: 'error', message: `Kotak ini sudah penuh maksimal 5 gambar!` });
            return;
        }

        setUploadingSlot(slot);
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const res = await fetch('/api/upload-banner', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || 'Upload gagal');

            setBanners(prev => ({
                ...prev,
                [slot]: [...(prev[slot] as string[]), data.url]
            }));
            
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setUploadingSlot(null);
            e.target.value = ''; // Reset input
        }
    };

    const removeImage = (slot: BannerSlot, index: number) => {
        if (!confirm('Hapus gambar ini dari slider?')) return;
        setBanners(prev => ({
            ...prev,
            [slot]: (prev[slot] as string[]).filter((_, i) => i !== index)
        }));
    };

    const saveChanges = async () => {
        setSaving(true);
        setStatus(null);
        try {
            const res = await fetch('/api/banners', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(banners)
            });
            
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);
            
            setOriginalBanners(JSON.parse(JSON.stringify(banners)));
            setStatus({ type: 'success', message: 'Setelan 3 Banner berhasil disimpan ke server!' });
            
            // Auto hide success
            setTimeout(() => setStatus(null), 3000);
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setSaving(false);
        }
    };

    const renderBannerSection = (title: string, desc: string, slotKey: BannerSlot) => {
        const images = banners[slotKey] as string[];
        return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                <div>
                    <h2 className="text-xl font-bold text-amber-500">{title}</h2>
                    <p className="text-gray-400 text-sm mt-1">{desc}</p>
                    <p className="text-gray-500 text-xs mt-1">
                        Sisa Kapasitas: <span className="text-white font-medium">{5 - images.length} slot</span> dari 5
                    </p>
                </div>
                
                <div>
                    <input 
                        type="file" 
                        id={`upload-${slotKey}`}
                        className="hidden" 
                        accept="image/jpeg, image/png, image/webp"
                        onChange={(e) => handleFileUpload(e, slotKey)}
                        disabled={uploadingSlot === slotKey || images.length >= 5}
                    />
                    <label 
                        htmlFor={`upload-${slotKey}`}
                        className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors
                            ${(images.length >= 5 || uploadingSlot === slotKey) 
                                ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
                                : 'bg-gray-800 hover:bg-gray-700 text-white cursor-pointer border border-gray-700'
                            }`}
                    >
                        {uploadingSlot === slotKey ? (
                            <><Loader2 size={16} className="animate-spin" /> Mengunggah...</>
                        ) : (
                            <><Plus size={16} /> Tambah Gambar</>
                        )}
                    </label>
                </div>
            </div>

            {images.length === 0 ? (
                <div className="border-2 border-dashed border-gray-800 rounded-xl p-8 text-center bg-gray-900/50 flex flex-col items-center justify-center">
                    <p className="text-gray-500 mb-2">Belum ada gambar yang diunggah</p>
                    <p className="text-xs text-gray-600">Tekan "Tambah Gambar" untuk memasukkan JPEG/PNG maksimal 5 file</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    {images.map((url, i) => (
                        <div key={i} className="group relative aspect-video bg-black rounded-lg overflow-hidden border border-gray-800">
                            {/* Ensure url works by skipping Next Image strict domains if external */}
                            <img src={url} alt={`Banner ${i+1}`} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                            
                            {/* Overlay Controls */}
                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                                <span className="absolute top-2 left-2 bg-black/80 px-2 py-1 rounded text-xs text-amber-500 font-bold border border-amber-900/50">
                                    Slide {i + 1}
                                </span>
                                
                                <button 
                                    onClick={() => removeImage(slotKey, i)}
                                    className="p-2 bg-red-900/80 hover:bg-red-600 rounded-full text-white backdrop-blur-sm"
                                    title="Hapus Slide"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
    };

    if (loading) {
        return (
            <div className="flex h-[60vh] flex-col items-center justify-center">
                <Loader2 className="w-10 h-10 text-amber-500 animate-spin mb-4" />
                <p className="text-gray-400">Memuat konfigurasi banner...</p>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto pb-20">
            {/* Header Sticky Action Bar */}
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 sticky top-0 z-10 bg-[#0d0d0d]/90 backdrop-blur-md py-4 border-b border-gray-800">
                <div>
                    <h1 className="text-2xl font-bold">Space Iklan & Banner Pribadi</h1>
                    <p className="text-gray-400 text-sm mt-1">Tata letak *Auto-Slide Banner* dengan rasio 5:2 untuk Monetisasi App.</p>
                </div>
                
                <div className="mt-4 md:mt-0 items-center flex gap-4">
                    {hasChanges && (
                        <span className="text-amber-500 text-sm font-medium animate-pulse hidden md:inline-block">
                            Ada perubahan belum disimpan
                        </span>
                    )}
                    <button 
                        onClick={saveChanges}
                        disabled={!hasChanges || saving}
                        className={`px-6 py-2 rounded-lg flex items-center gap-2 font-medium transition-all shadow-lg
                            ${hasChanges && !saving 
                                ? 'bg-amber-500 hover:bg-amber-400 text-black shadow-amber-500/20' 
                                : 'bg-gray-800 text-gray-500 cursor-not-allowed'}`}
                    >
                        {saving ? (
                            <><Loader2 size={18} className="animate-spin" /> Menyimpan...</>
                        ) : (
                            <><CheckCircle2 size={18} /> Simpan Semua Perubahan</>
                        )}
                    </button>
                </div>
            </div>

            {/* Notification Toast Status */}
            {status && (
                <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 border 
                    ${status.type === 'success' ? 'bg-green-900/30 border-green-800 text-green-400' : 'bg-red-900/30 border-red-800 text-red-400'}`}
                >
                    {status.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                    <p className="text-sm font-medium">{status.message}</p>
                </div>
            )}

            {/* Grid Tiga Kolom Banner */}
            {renderBannerSection(
                "Banner 1 (Tab Home - Atas)", 
                "Terletak di halaman Beranda paling atas dekat judul. Tempat ideal untuk promosi Event besar.",
                "banner_1"
            )}

            {renderBannerSection(
                "Banner 2 (Tab Home - Bawah)", 
                "Terletak di bagian paling bawah Home sebelum tombol Footer. Cocok untuk ajakan Top Up Coin.",
                "banner_2"
            )}

            {renderBannerSection(
                "Banner 3 (Tab Profil - Dompet)", 
                "Terletak tepat di bawah menu Pengaturan pengguna. Ruang yang sangat sering dilihat setiap nge-claim dompet profil.",
                "banner_3"
            )}
            
            {/* Extended Settings: Links */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mt-8">
                <div className="mb-4">
                    <h2 className="text-xl font-bold text-[#229ED9]">Pengaturan External Link</h2>
                    <p className="text-gray-400 text-sm mt-1">Konfigurasikan tautan tombol grup Telegram yang ada pada menu Profil.</p>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Tautan Grup Telegram</label>
                    <input 
                        type="url" 
                        value={banners.telegram_link || ''}
                        onChange={(e) => setBanners(prev => ({ ...prev, telegram_link: e.target.value }))}
                        className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#229ED9]"
                        placeholder="Contoh: https://t.me/asiandrama_id"
                    />
                </div>
            </div>
            
        </div>
    );
}
