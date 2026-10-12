'use client';

import { useState, useEffect } from 'react';
import { 
    Plus, 
    Trash2, 
    CheckCircle2, 
    AlertCircle, 
    Loader2, 
    Sparkles, 
    Image as ImageIcon, 
    Link2, 
    ExternalLink, 
    Send, 
    Layers, 
    Info 
} from 'lucide-react';

interface AppBanners {
    banner_1: string[];
    banner_2: string[];
    banner_3: string[];
    banner_1_links?: string[];
    banner_2_links?: string[];
    banner_3_links?: string[];
    telegram_link?: string;
}

type BannerSlot = 'banner_1' | 'banner_2' | 'banner_3';

interface SlotMeta {
    title: string;
    badge: string;
    desc: string;
    placement: string;
}

const SLOT_CONFIG: Record<BannerSlot, SlotMeta> = {
    banner_1: {
        title: 'Banner Hero Beranda (Atas)',
        badge: 'SLOT 01 • HERO TOP',
        desc: 'Terletak di puncak halaman Beranda mobile app. Ruang tayang premium dengan impresi paling tinggi untuk promosi drama unggulan atau sponsor.',
        placement: 'Beranda Utama (Top)'
    },
    banner_2: {
        title: 'Banner Feed Beranda (Bawah)',
        badge: 'SLOT 02 • FEED FOOTER',
        desc: 'Terletak di bagian paling bawah katalog Beranda sebelum navigasi tab. Sangat efektif untuk kampanye top-up koin dan event mingguan.',
        placement: 'Beranda Utama (Bottom)'
    },
    banner_3: {
        title: 'Banner Profil & Dompet Koin',
        badge: 'SLOT 03 • WALLET & PROFIL',
        desc: 'Terletak tepat di bawah widget saldo koin pada tab Profil. Tempat strategis untuk ajakan upgrade VIP Pass dan penukaran reward.',
        placement: 'Tab Profil & Dompet'
    }
};

export default function BannersPage() {
    const [banners, setBanners] = useState<AppBanners>({
        banner_1: [],
        banner_2: [],
        banner_3: [],
        banner_1_links: [],
        banner_2_links: [],
        banner_3_links: [],
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
                banner_1_links: raw.banner_1_links || [],
                banner_2_links: raw.banner_2_links || [],
                banner_3_links: raw.banner_3_links || [],
                telegram_link: raw.telegram_link || 'https://t.me/asiandrama_id',
            };
            setBanners(data);
            setOriginalBanners(JSON.parse(JSON.stringify(data)));
        } catch (e) {
            console.error('Failed to load banners', e);
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
            setStatus({ type: 'error', message: `Slot ini telah mencapai kapasitas maksimal 5 gambar banner!` });
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
            
            if (!res.ok) throw new Error(data.error || 'Upload gagal diproses server');

            setBanners(prev => {
                const linkKey = `${slot}_links` as keyof AppBanners;
                const currentLinks = (prev[linkKey] as string[] || []);
                return {
                    ...prev,
                    [slot]: [...(prev[slot] as string[]), data.url],
                    [linkKey]: [...currentLinks, ''],
                };
            });

            setStatus({ type: 'success', message: 'Gambar banner berhasil diunggah! Jangan lupa simpan perubahan.' });
            setTimeout(() => setStatus(null), 3000);
            
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message || 'Gagal mengunggah banner' });
        } finally {
            setUploadingSlot(null);
            e.target.value = ''; // Reset input
        }
    };

    const removeImage = (slot: BannerSlot, index: number) => {
        if (!confirm('Hapus slide banner ini dari rotasi tayang?')) return;
        setBanners(prev => {
            const linkKey = `${slot}_links` as keyof AppBanners;
            const currentLinks = (prev[linkKey] as string[] || []);
            return {
                ...prev,
                [slot]: (prev[slot] as string[]).filter((_, i) => i !== index),
                [linkKey]: currentLinks.filter((_, i) => i !== index),
            };
        });
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
            if (!res.ok) throw new Error(data.error || 'Gagal menyimpan konfigurasi');
            
            setOriginalBanners(JSON.parse(JSON.stringify(banners)));
            setStatus({ type: 'success', message: 'Seluruh konfigurasi banner dan tautan berhasil disimpan ke server!' });
            
            setTimeout(() => setStatus(null), 3500);
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message || 'Gagal menyimpan perubahan' });
        } finally {
            setSaving(false);
        }
    };

    const renderBannerSection = (slotKey: BannerSlot) => {
        const meta = SLOT_CONFIG[slotKey];
        const images = banners[slotKey] as string[];
        const linkKey = `${slotKey}_links` as keyof AppBanners;
        const links = (banners[linkKey] as string[] || []);
        const isFull = images.length >= 5;
        const isCurrentUploading = uploadingSlot === slotKey;
        
        const updateLink = (index: number, value: string) => {
            setBanners(prev => {
                const currentLinks = [...(prev[linkKey] as string[] || [])];
                while (currentLinks.length <= index) currentLinks.push('');
                currentLinks[index] = value;
                return { ...prev, [linkKey]: currentLinks };
            });
        };
        
        return (
            <div className="glass-panel p-6 sm:p-7 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-80 h-40 bg-amber-500/[0.02] rounded-full blur-3xl pointer-events-none" />

                {/* Slot Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 mb-6 border-b border-white/[0.06] gap-4">
                    <div className="space-y-1.5 max-w-2xl">
                        <div className="flex items-center gap-3">
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                {meta.badge}
                            </span>
                            <span className="text-xs text-slate-400 flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                {meta.placement}
                            </span>
                        </div>
                        <h2 className="text-lg font-bold text-white tracking-tight">{meta.title}</h2>
                        <p className="text-xs text-slate-400 leading-relaxed">{meta.desc}</p>
                    </div>
                    
                    <div className="flex items-center gap-3 self-start md:self-center">
                        {/* Capacity meter */}
                        <div className="px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-right">
                            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Kapasitas</div>
                            <div className="text-xs font-bold text-white">
                                <span className={images.length === 5 ? 'text-amber-400' : 'text-white'}>{images.length}</span>
                                <span className="text-slate-500"> / 5 Slide</span>
                            </div>
                        </div>

                        {/* Upload trigger */}
                        <input 
                            type="file" 
                            id={`upload-${slotKey}`}
                            className="hidden" 
                            accept="image/jpeg, image/png, image/webp"
                            onChange={(e) => handleFileUpload(e, slotKey)}
                            disabled={isCurrentUploading || isFull}
                        />
                        <label 
                            htmlFor={`upload-${slotKey}`}
                            className={`px-4 py-2 rounded-xl flex items-center gap-2 text-xs font-semibold transition-all ${
                                isFull || isCurrentUploading
                                    ? 'bg-white/[0.04] text-slate-500 border border-white/[0.04] cursor-not-allowed' 
                                    : 'gold-btn cursor-pointer shadow-lg'
                            }`}
                        >
                            {isCurrentUploading ? (
                                <><Loader2 size={14} className="animate-spin text-black" /> Mengunggah...</>
                            ) : (
                                <><Plus size={14} /> Tambah Slide</>
                            )}
                        </label>
                    </div>
                </div>

                {/* Slides Grid or Empty State */}
                {images.length === 0 ? (
                    <div className="border border-dashed border-white/10 rounded-2xl p-10 text-center bg-white/[0.01] flex flex-col items-center justify-center">
                        <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-3">
                            <ImageIcon size={22} />
                        </div>
                        <p className="text-sm font-semibold text-slate-300 mb-1">Belum Ada Banner di Slot Ini</p>
                        <p className="text-xs text-slate-500 max-w-md mb-4">
                            Format disarankan rasio 5:2 (contoh: 1000x400 px), format WebP, JPG atau PNG maks 2MB.
                        </p>
                        <label
                            htmlFor={`upload-${slotKey}`}
                            className="text-xs text-amber-400 hover:text-amber-300 font-semibold cursor-pointer underline underline-offset-4"
                        >
                            Unggah Slide Pertama Sekarang →
                        </label>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                        {images.map((url, i) => (
                            <div key={i} className="flex flex-col gap-2 group/card">
                                <div className="group relative aspect-video bg-black/60 rounded-xl overflow-hidden border border-white/10 shadow-md">
                                    <img 
                                        src={url} 
                                        alt={`Slide ${i + 1}`} 
                                        className="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105" 
                                    />
                                    
                                    {/* Slide pill */}
                                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-[10px] font-bold text-amber-400 border border-amber-500/30 flex items-center gap-1">
                                        <Layers size={10} /> Slide {i + 1}
                                    </div>
                                    
                                    {/* Action overlay */}
                                    <div className="absolute inset-0 bg-black/70 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                        <button 
                                            type="button"
                                            onClick={() => removeImage(slotKey, i)}
                                            className="px-3 py-1.5 rounded-lg bg-rose-500/80 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg"
                                            title="Hapus Slide"
                                        >
                                            <Trash2 size={13} /> Hapus
                                        </button>
                                    </div>
                                </div>

                                {/* Link target input */}
                                <div className="relative">
                                    <Link2 size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                                    <input 
                                        type="url"
                                        value={links[i] || ''}
                                        onChange={(e) => updateLink(i, e.target.value)}
                                        className="w-full bg-[#0B0F17] border border-white/10 rounded-lg pl-7 pr-2.5 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors"
                                        placeholder="Tautan klik (opsional)"
                                    />
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
            <div className="flex h-[60vh] flex-col items-center justify-center space-y-4">
                <div className="relative w-12 h-12 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border-2 border-amber-500/20 border-t-amber-400 animate-spin" />
                    <Sparkles className="w-5 h-5 text-amber-400" />
                </div>
                <div className="text-center">
                    <p className="text-sm font-semibold text-white">Memuat Visual Banner Studio...</p>
                    <p className="text-xs text-slate-500 mt-1">Mengambil konfigurasi rotasi iklan dan external links</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-16">
            {/* Header Sticky Action Bar */}
            <div className="sticky top-20 z-20 -mx-6 sm:-mx-8 px-6 sm:px-8 py-4 bg-[#07090E]/85 backdrop-blur-xl border-b border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all">
                <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                            <span className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                                <ImageIcon size={20} />
                            </span>
                            Space Iklan & Banner Studio
                        </h1>
                        <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            3 Slot Auto-Slide
                        </span>
                    </div>
                    <p className="text-xs text-slate-400">
                        Atur tata letak carousel banner monetisasi app (rasio 5:2) dan external link affiliate.
                    </p>
                </div>
                
                <div className="flex items-center gap-3 self-end sm:self-center">
                    {hasChanges && (
                        <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 animate-pulse bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                            Perubahan belum disimpan
                        </span>
                    )}
                    <button 
                        onClick={saveChanges}
                        disabled={!hasChanges || saving}
                        className={`px-5 py-2.5 rounded-xl flex items-center gap-2 text-xs font-bold transition-all ${
                            hasChanges && !saving 
                                ? 'gold-btn shadow-lg' 
                                : 'bg-white/[0.04] text-slate-500 border border-white/[0.06] cursor-not-allowed'
                        }`}
                    >
                        {saving ? (
                            <><Loader2 size={15} className="animate-spin text-black" /> Menyimpan...</>
                        ) : (
                            <><CheckCircle2 size={15} /> Simpan Semua Perubahan</>
                        )}
                    </button>
                </div>
            </div>

            {/* Notification Toast Status */}
            {status && (
                <div className={`p-4 rounded-xl flex items-center gap-3 border backdrop-blur-md transition-all ${
                    status.type === 'success' 
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                        : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}>
                    {status.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                    <p className="text-xs font-medium">{status.message}</p>
                </div>
            )}

            {/* Banner Slots */}
            <div className="space-y-6">
                {renderBannerSection('banner_1')}
                {renderBannerSection('banner_2')}
                {renderBannerSection('banner_3')}
            </div>
            
            {/* Extended Settings: External Community Links */}
            <div className="glass-panel p-6 sm:p-7 relative overflow-hidden">
                <div className="flex items-start gap-4 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-[#229ED9]/15 border border-[#229ED9]/30 flex items-center justify-center text-[#229ED9] flex-shrink-0">
                        <Send size={18} />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-base font-bold text-white tracking-tight">Tautan Komunitas Telegram</h2>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#229ED9]/10 text-[#229ED9] border border-[#229ED9]/20">
                                External Link
                            </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                            Tautan ini akan dibuka saat pengguna menekan tombol "Gabung Telegram AsianDrama" pada tab Profil.
                        </p>
                    </div>
                </div>

                <div className="max-w-xl">
                    <label className="block text-xs font-medium text-slate-300 mb-2">
                        URL Grup / Channel Telegram
                    </label>
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <Send size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input 
                                type="url" 
                                value={banners.telegram_link || ''}
                                onChange={(e) => setBanners(prev => ({ ...prev, telegram_link: e.target.value }))}
                                className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-[#229ED9]/70 transition-colors"
                                placeholder="https://t.me/asiandrama_id"
                            />
                        </div>
                        {banners.telegram_link && (
                            <a
                                href={banners.telegram_link}
                                target="_blank"
                                rel="noreferrer"
                                className="px-4 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 text-xs font-semibold text-slate-300 hover:text-white flex items-center gap-1.5 transition-colors"
                            >
                                <ExternalLink size={14} /> Uji Buka
                            </a>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
