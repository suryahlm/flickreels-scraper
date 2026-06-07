import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

const EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send';
const BATCH_SIZE = 100; // Expo recommends max 100 per request

export async function POST(req: Request) {
    try {
        const { title, body, data } = await req.json();

        if (!title || !body) {
            return NextResponse.json({ error: 'title and body required' }, { status: 400 });
        }

        // Fetch all valid expo push tokens from profiles
        const { data: profiles, error } = await supabaseAdmin
            .from('profiles')
            .select('expo_push_token')
            .not('expo_push_token', 'is', null)
            .neq('expo_push_token', '');

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        const tokens = profiles
            .map((p: any) => p.expo_push_token)
            .filter((t: string) => t && t.startsWith('ExponentPushToken['));

        if (tokens.length === 0) {
            return NextResponse.json({ 
                success: true, 
                sent: 0, 
                message: 'No registered devices found' 
            });
        }

        // Split into batches of 100
        const batches: string[][] = [];
        for (let i = 0; i < tokens.length; i += BATCH_SIZE) {
            batches.push(tokens.slice(i, i + BATCH_SIZE));
        }

        let totalSent = 0;
        let errors: any[] = [];

        for (const batch of batches) {
            const messages = batch.map((token) => ({
                to: token,
                title,
                body,
                data: data || {},
                sound: 'default',
                priority: 'high',
                channelId: 'default',
            }));

            const response = await fetch(EXPO_PUSH_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate',
                },
                body: JSON.stringify(messages),
            });

            const result = await response.json();

            if (result.data) {
                // Count successful sends
                const batchErrors = result.data.filter((r: any) => r.status === 'error');
                totalSent += batch.length - batchErrors.length;
                errors = [...errors, ...batchErrors];
            }
        }

        return NextResponse.json({
            success: true,
            total_devices: tokens.length,
            sent: totalSent,
            failed: errors.length,
        });

    } catch (error: any) {
        console.error('[Send Push] Error:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
