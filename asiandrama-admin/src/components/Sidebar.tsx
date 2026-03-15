'use client';

import { supabase } from '@/lib/supabase';
import {
    BarChart3,
    Bell,
    Film,
    FolderOpen,
    Image,
    LayoutDashboard,
    LogOut,
    Settings,
    Star,
    Users
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';

const navItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/traffic', label: 'Trafik', icon: BarChart3 },
    { href: '/dramas', label: 'Drama', icon: Film },
    { href: '/featured', label: 'Featured', icon: Star },
    { href: '/users', label: 'Users', icon: Users },
    { href: '/categories', label: 'Kategori', icon: FolderOpen },
    { href: '/banners', label: 'Banner', icon: Image },
    { href: '/notifications', label: 'Notifikasi', icon: Bell },
    { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push('/login');
    };

    // Don't show sidebar on login page
    if (pathname === '/login') return null;

    return (
        <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
            {/* Logo */}
            <div className="p-6 border-b border-gray-800">
                <h1 className="text-xl font-bold text-amber-500">AsianDrama</h1>
                <p className="text-xs text-gray-500">Admin Portal</p>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-4">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-6 py-3 transition-colors ${isActive
                                ? 'bg-gradient-to-r from-amber-500 to-yellow-600 text-white'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                }`}
                        >
                            <Icon size={20} />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Logout */}
            <div className="p-4 border-t border-gray-800">
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-2 py-2 text-gray-400 hover:text-white w-full"
                >
                    <LogOut size={20} />
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}
