'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

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
        <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-amber-500">AsianDrama</h1>
                    <p className="text-gray-500 mt-2">Admin Portal</p>
                </div>

                {/* Login Form */}
                <form onSubmit={handleLogin} className="bg-gray-900 rounded-xl p-8 border border-gray-800">
                    <h2 className="text-xl font-bold mb-6 text-center">Login Admin</h2>

                    {error && (
                        <div className="bg-red-900/50 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">
                            {error}
                        </div>
                    )}

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-amber-500"
                                placeholder="admin@example.com"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:border-amber-500"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-amber-500 to-yellow-600 hover:from-amber-600 hover:to-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-3 rounded-lg font-semibold mt-4"
                        >
                            {loading ? 'Logging in...' : 'Login'}
                        </button>
                    </div>
                </form>

                <p className="text-center text-gray-600 text-sm mt-6">
                    © 2024 AsianDrama. All rights reserved.
                </p>
            </div>
        </div>
    );
}
