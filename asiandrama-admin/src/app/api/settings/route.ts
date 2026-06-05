import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function POST(req: Request) {
    try {
        const settings = await req.json();

        if (!Array.isArray(settings)) {
            return NextResponse.json({ error: 'Invalid payload' }, { status: 400 });
        }

        for (const setting of settings) {
            const { error } = await supabaseAdmin
                .from('app_settings')
                .upsert({ 
                    key: setting.key, 
                    value: setting.value, 
                    updated_at: new Date().toISOString() 
                });
            
            if (error) {
                console.error(`Failed to update setting ${setting.key}:`, error);
                return NextResponse.json({ error: error.message }, { status: 500 });
            }
        }

        return NextResponse.json({ success: true });
    } catch (error: any) {
        console.error('Settings API Error:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
