'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { supabase } from '@/lib/supabase';
import { Lock, Mail, Sparkles, ShieldCheck, ArrowRight, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const { data, error: authError } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (authError) {
            setError(authError.message);
            setLoading(false);
            return;
        }

        // Redirect to dashboard
        router.push('/');
        router.refresh();
    };

    return (
        <div className="min-h-screen bg-[#07090E] flex items-center justify-center p-4 relative overflow-hidden">
            {/* Ambient Background Glow Orbs */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-gradient-to-tr from-amber-500/15 via-yellow-500/10 to-transparent rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-[400px] h-[400px] bg-amber-600/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                {/* Brand Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500 to-yellow-300 p-0.5 shadow-[0_0_30px_rgba(229,169,60,0.35)] mb-4">
                        <div className="w-full h-full bg-[#090D15] rounded-[14px] overflow-hidden flex items-center justify-center">
                            <Image
                                src="/freedrama-icon-full.png"
                                alt="FreeDrama"
                                width={64}
                                height={64}
                                className="w-full h-full object-cover"
                                priority
                            />
                        </div>
                    </div>
                    <h1 className="text-3xl font-extrabold tracking-tight gold-gradient-text">
                        FreeDrama
                    </h1>
                    <p className="text-xs font-medium tracking-wider uppercase text-gray-400 mt-1">
                        Executive Management Console
                    </p>
                </div>

                {/* Login Glass Card */}
                <div className="glass-panel rounded-2xl p-8 border border-white/[0.09] shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                    <div className="flex items-center justify-between pb-6 mb-6 border-b border-white/[0.07]">
                        <div>
                            <h2 className="text-lg font-bold text-white tracking-tight">Login Administrator</h2>
                            <p className="text-xs text-gray-400 mt-0.5">Akses khusus pengelola platform</p>
                        </div>
                        <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-semibold flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            Live Engine
                        </span>
                    </div>

                    {error && (
                        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs px-4 py-3 rounded-xl mb-6 flex items-start gap-2.5 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
                            <span className="text-rose-400 font-bold">•</span>
                            <span className="flex-1 leading-relaxed">{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                                Email Akses
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={17} />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full glass-input rounded-xl pl-11 pr-4 py-3 text-sm focus:border-amber-400"
                                    placeholder="admin@asiandrama.cc"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                                Kata Sandi
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={17} />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full glass-input rounded-xl pl-11 pr-4 py-3 text-sm focus:border-amber-400"
                                    placeholder="••••••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full gold-btn py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2 group"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={18} className="animate-spin text-[#07090E]" />
                                    <span>Memverifikasi Akses...</span>
                                </>
                            ) : (
                                <>
                                    <span>Masuk ke Konsol</span>
                                    <ArrowRight size={16} className="text-[#07090E] group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                {/* Security Footer Badge */}
                <div className="flex items-center justify-center gap-2 text-[11px] text-gray-400 mt-6 font-medium">
                    <ShieldCheck size={14} className="text-amber-500/80" />
                    <span>Secure Gateway • FreeDrama Standalone Architecture</span>
                </div>
            </div>
        </div>
    );
}
