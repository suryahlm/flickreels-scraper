import { createClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';

// Force dynamic rendering - don't pre-render this route
export const dynamic = 'force-dynamic';

// Create admin client inside function to avoid build-time errors
function getSupabaseAdmin() {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!url || !key) {
        throw new Error('Missing Supabase environment variables');
    }

    return createClient(url, key, {
        auth: {
            autoRefreshToken: false,
            persistSession: false
        }
    });
}

export async function POST(request: NextRequest) {
    try {
        const { userId } = await request.json();

        if (!userId) {
            return NextResponse.json(
                { error: 'Missing userId' },
                { status: 400 }
            );
        }

        const supabaseAdmin = getSupabaseAdmin();

        // Delete from auth.users — this will CASCADE delete:
        // - profiles (ON DELETE CASCADE)
        // - user_coins (ON DELETE CASCADE)
        // - coin_transactions (ON DELETE CASCADE)
        // - daily_checkins (ON DELETE CASCADE)
        // - subscriptions (ON DELETE CASCADE)
        // - episode_unlocks (ON DELETE CASCADE)
        // - ad_unlocks (ON DELETE CASCADE)
        // - user_activity_log (ON DELETE CASCADE)
        const { error } = await supabaseAdmin.auth.admin.deleteUser(userId);

        if (error) {
            console.error('Delete user error:', error);
            return NextResponse.json(
                { error: error.message },
                { status: 500 }
            );
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Delete user error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
