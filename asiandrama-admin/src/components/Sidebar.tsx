'use client';

import { supabase } from '@/lib/supabase';
import {
    BarChart3,
    Bell,
    ClipboardList,
    Film,
    FolderOpen,
    Image as ImageIcon,
    LayoutDashboard,
    LogOut,
    Settings,
    Smartphone,
    Star,
    Users,
    Sparkles,
    Shield
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface NavGroup {
    groupLabel: string;
    items: {
        href: string;
        label: string;
        icon: any;
        badge?: string;
    }[];
}

const navGroups: NavGroup[] = [
    {
        groupLabel: 'Utama',
        items: [
            { href: '/', label: 'Dashboard', icon: LayoutDashboard },
            { href: '/traffic', label: 'Trafik & Analitik', icon: BarChart3 },
        ],
    },
    {
        groupLabel: 'Kurasi Konten',
        items: [
            { href: '/draft-dramas', label: 'Review Drama Baru', icon: ClipboardList },
            { href: '/dramas', label: 'Katalog Drama', icon: Film },
            { href: '/featured', label: 'Featured Beranda', icon: Star },
            { href: '/categories', label: 'Kategori Genre', icon: FolderOpen },
        ],
    },
    {
        groupLabel: 'Pengguna & Kampanye',
        items: [
            { href: '/users', label: 'Direktori User', icon: Users },
            { href: '/banners', label: 'Banner Aplikasi', icon: ImageIcon },
            { href: '/notifications', label: 'Notifikasi Banner', icon: Bell },
            { href: '/push-broadcast', label: 'Push Broadcast', icon: Smartphone },
        ],
    },
    {
        groupLabel: 'Konfigurasi',
        items: [
            { href: '/settings', label: 'Pengaturan Sistem', icon: Settings },
        ],
    },
];

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [adminEmail, setAdminEmail] = useState<string>('admin@asiandrama.cc');

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            if (user?.email) {
                setAdminEmail(user.email);
            }
        }).catch(() => {});
    }, []);

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push('/login');
    };

    // Don't show sidebar on login page
    if (pathname === '/login') return null;

    return (
        <aside className="w-72 bg-[#090D15]/95 backdrop-blur-2xl border-r border-white/[0.08] min-h-screen flex flex-col flex-shrink-0 z-40 transition-all select-none">
            {/* Logo Brand Header */}
            <div className="p-6 border-b border-white/[0.07] flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-yellow-300 p-0.5 shadow-[0_0_20px_rgba(229,169,60,0.3)] flex-shrink-0">
                    <div className="w-full h-full bg-[#090D15] rounded-[10px] flex items-center justify-center">
                        <Sparkles className="text-amber-400" size={20} />
                    </div>
                </div>
                <div>
                    <h1 className="text-lg font-bold tracking-tight gold-gradient-text leading-tight">
                        AsianDrama
                    </h1>
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                        <p className="text-[11px] font-medium tracking-wider uppercase text-gray-400">
                            Luxury Console
                        </p>
                    </div>
                </div>
            </div>

            {/* Navigation Menus with Group Hierarchy */}
            <nav className="flex-1 px-3 py-5 space-y-6 overflow-y-auto">
                {navGroups.map((group) => (
                    <div key={group.groupLabel} className="space-y-1">
                        <p className="px-4 text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2">
                            {group.groupLabel}
                        </p>
                        {group.items.map((item) => {
                            const isActive = pathname === item.href;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`relative flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                                        isActive
                                            ? 'bg-gradient-to-r from-amber-500/15 via-amber-500/10 to-transparent text-amber-300 border border-amber-500/30 shadow-[0_4px_16px_rgba(229,169,60,0.12)]'
                                            : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
                                    }`}
                                >
                                    {isActive && (
                                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-gradient-to-b from-amber-400 to-amber-600 rounded-r-full" />
                                    )}
                                    <Icon
                                        size={18}
                                        className={`transition-colors flex-shrink-0 ${
                                            isActive
                                                ? 'text-amber-400'
                                                : 'text-gray-400 group-hover:text-amber-300'
                                        }`}
                                    />
                                    <span className="truncate flex-1 tracking-tight">{item.label}</span>
                                    {item.badge && (
                                        <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-500/20 text-amber-300 rounded-full border border-amber-500/30">
                                            {item.badge}
                                        </span>
                                    )}
                                </Link>
                            );
                        })}
                    </div>
                ))}
            </nav>

            {/* User Profile & Logout Bottom Card */}
            <div className="p-4 border-t border-white/[0.07] bg-[#07090E]/60">
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-3 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 p-[1px] flex-shrink-0 shadow-[0_0_12px_rgba(229,169,60,0.25)]">
                        <div className="w-full h-full bg-[#090D15] rounded-[11px] flex items-center justify-center font-bold text-xs text-amber-400">
                            {adminEmail.charAt(0).toUpperCase()}
                        </div>
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="text-xs font-bold text-white truncate flex items-center gap-1">
                            Superadmin <Shield size={11} className="text-amber-400" />
                        </p>
                        <p className="text-[10px] text-gray-400 truncate">{adminEmail}</p>
                    </div>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-rose-400/90 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl w-full transition-all"
                >
                    <LogOut size={14} />
                    <span>Keluar dari Admin</span>
                </button>
            </div>
        </aside>
    );
}
