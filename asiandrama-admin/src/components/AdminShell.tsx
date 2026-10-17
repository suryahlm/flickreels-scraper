'use client';

import { usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';

export default function AdminShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isAuthPage = pathname === '/login' || pathname.startsWith('/privacy');

    if (isAuthPage) {
        return (
            <main className="h-screen w-full overflow-y-auto">
                {children}
            </main>
        );
    }

    return (
        <div className="flex h-screen w-full overflow-hidden bg-[#07090E]">
            {/* 1. Independent Scrollable Sidebar on the Left */}
            <Sidebar />

            {/* 2. Independent Scrollable Content Area on the Right */}
            <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-[#07090E]">
                <Header />
                <main className="flex-1 overflow-y-auto overscroll-contain px-8 pt-8 pb-12 min-w-0">
                    {children}
                </main>
            </div>
        </div>
    );
}
