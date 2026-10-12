'use client';

import { supabase } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface AuthProviderProps {
    children: React.ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check current session with safe error fallback
        supabase.auth.getSession()
            .then(({ data: { session } }) => {
                setUser(session?.user ?? null);
                setLoading(false);
            })
            .catch(() => {
                setUser(null);
                setLoading(false);
            });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);
        });

        return () => subscription.unsubscribe();
    }, []);

    useEffect(() => {
        if (!loading) {
            if (!user && pathname !== '/login' && !pathname.startsWith('/privacy')) {
                router.push('/login');
            } else if (user && pathname === '/login') {
                router.push('/');
            }
        }
    }, [user, loading, pathname, router]);

    if (loading) {
        return (
            <div className="min-h-screen bg-[#07090E] flex flex-col items-center justify-center relative overflow-hidden">
                {/* Ambient glow */}
                <div className="absolute w-96 h-96 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none animate-pulse" />
                <div className="relative z-10 flex flex-col items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500/20 to-yellow-400/20 border border-amber-500/30 flex items-center justify-center p-2.5 shadow-[0_0_25px_rgba(229,169,60,0.2)]">
                        <div className="w-full h-full border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <div className="text-center">
                        <p className="text-sm font-semibold text-white tracking-wide">AsianDrama</p>
                        <p className="text-xs text-amber-500/70 font-medium mt-0.5">Memuat konsol admin...</p>
                    </div>
                </div>
            </div>
        );
    }

    // Show login page without sidebar
    if (pathname === '/login') {
        return <>{children}</>;
    }

    // Show protected content
    if (!user) {
        return null;
    }

    return <>{children}</>;
}
