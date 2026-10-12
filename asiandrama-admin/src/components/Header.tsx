'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { ExternalLink, ShieldCheck, Sparkles, Activity } from 'lucide-react';

const PAGE_TITLES: Record<string, { title: string; subtitle: string; category: string }> = {
    '/': { title: 'Executive Overview', subtitle: 'Statistik performa real-time dan ringkasan aktivitas sistem', category: 'Dashboard' },
    '/traffic': { title: 'Trafik & Analitik', subtitle: 'Metrik audiens, tren pendaftaran user, dan popularitas drama', category: 'Analytics' },
    '/draft-dramas': { title: 'Review Drama Baru', subtitle: 'Antrian kurasi konten hasil scraper sebelum dipublikasikan', category: 'Content' },
    '/dramas': { title: 'Katalog Drama', subtitle: 'Manajemen metadata, status publikasi, dan episode', category: 'Content' },
    '/featured': { title: 'Featured Curator', subtitle: 'Kurasi dan susun urutan 18 drama unggulan di beranda aplikasi', category: 'Content' },
    '/users': { title: 'Manajemen Pengguna', subtitle: 'Direktori akun terdaftar, status akses VIP, dan moderasi', category: 'Users' },
    '/categories': { title: 'Kategori Drama', subtitle: 'Kelola taksonomi genre dan pengelompokan tayangan', category: 'Content' },
    '/banners': { title: 'Banner & Kampanye', subtitle: 'Slot visual promo beranda dan integrasi channel Telegram', category: 'Marketing' },
    '/notifications': { title: 'Notifikasi Banner In-App', subtitle: 'Siaran pengumuman pop-up langsung di layar pemirsa', category: 'Marketing' },
    '/push-broadcast': { title: 'Push Notification Broadcast', subtitle: 'Kirim notifikasi langsung ke notification center ponsel user', category: 'Marketing' },
    '/settings': { title: 'Pengaturan Sistem', subtitle: 'Konfigurasi provider streaming, identitas aplikasi, dan pemeliharaan', category: 'System' },
};

export default function Header() {
    const pathname = usePathname();
    const [adminEmail, setAdminEmail] = useState<string>('admin@asiandrama.cc');

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            if (user?.email) {
                setAdminEmail(user.email);
            }
        }).catch(() => {});
    }, []);

    if (pathname === '/login') return null;

    const pageInfo = PAGE_TITLES[pathname] || {
        title: 'AsianDrama Console',
        subtitle: 'Sistem Manajemen Streaming Asia',
        category: 'Portal'
    };

    return (
        <header className="sticky top-0 z-30 mb-8 backdrop-blur-xl bg-[#07090E]/80 border-b border-white/[0.07] px-8 py-4 transition-all">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Title & Breadcrumb */}
                <div>
                    <div className="flex items-center gap-2 text-xs font-semibold tracking-wider uppercase text-amber-500/80 mb-1">
                        <span>{pageInfo.category}</span>
                        <span className="text-white/20">/</span>
                        <span className="text-white/60">{pageInfo.title}</span>
                    </div>
                    <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                        {pageInfo.title}
                    </h1>
                    <p className="text-xs text-gray-400 mt-0.5 max-w-xl hidden sm:block">
                        {pageInfo.subtitle}
                    </p>
                </div>

                {/* Status Badges & Quick Links */}
                <div className="flex items-center gap-3">
                    {/* Live System Indicator */}
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium shadow-[0_0_12px_rgba(16,185,129,0.12)]">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="hidden sm:inline">Engine:</span> Online (Free Mode)
                    </div>

                    {/* View Live Web Button */}
                    <a
                        href="https://asiandrama.cc"
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-amber-500/40 text-xs font-medium text-gray-300 hover:text-white transition-all group"
                        title="Buka Website Pengguna"
                    >
                        <span>Lihat Web</span>
                        <ExternalLink size={12} className="text-gray-400 group-hover:text-amber-400 transition-colors" />
                    </a>

                    {/* Admin Avatar Pill */}
                    <div className="hidden lg:flex items-center gap-2.5 pl-2 border-l border-white/10">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-[#07090E] font-bold text-xs shadow-[0_0_10px_rgba(229,169,60,0.25)]">
                            {adminEmail.charAt(0).toUpperCase()}
                        </div>
                        <div className="text-left text-xs">
                            <p className="font-semibold text-white leading-tight flex items-center gap-1">
                                Surya Admin <ShieldCheck size={12} className="text-amber-400" />
                            </p>
                            <p className="text-[10px] text-gray-400 truncate max-w-[120px]">{adminEmail}</p>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
