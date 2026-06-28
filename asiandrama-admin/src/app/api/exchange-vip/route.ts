import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const { userId, durationDays, planType, cost } = body;

        if (!userId || !durationDays || !planType || !cost) {
            return NextResponse.json({ success: false, message: 'Invalid payload' }, { status: 400 });
        }

        // 1. Cek saldo koin
        const { data: userCoins, error: coinError } = await supabaseAdmin
            .from('user_coins')
            .select('balance')
            .eq('user_id', userId)
            .single();

        if (coinError || !userCoins) {
            return NextResponse.json({ success: false, message: 'Gagal mengambil saldo koin' }, { status: 400 });
        }

        if (userCoins.balance < cost) {
            return NextResponse.json({ success: false, message: 'Koin tidak cukup' }, { status: 400 });
        }

        const newBalance = userCoins.balance - cost;

        // 2. Potong koin
        const { error: deductError } = await supabaseAdmin
            .from('user_coins')
            .update({ balance: newBalance })
            .eq('user_id', userId);

        if (deductError) {
            return NextResponse.json({ success: false, message: 'Gagal memotong koin' }, { status: 500 });
        }

        // Update profiles coin_balance agar sinkron dengan dashboard admin
        await supabaseAdmin
            .from('profiles')
            .update({ coin_balance: newBalance })
            .eq('id', userId);

        // 3. Catat riwayat transaksi
        await supabaseAdmin.from('coin_transactions').insert({
            user_id: userId,
            amount: -cost,
            type: 'EXCHANGE_VIP',
            description: `Exchange VIP ${durationDays} Days`
        });

        // 4. Berikan akses VIP
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + durationDays);

        const { error: insertSubError } = await supabaseAdmin.from('subscriptions').insert({
            user_id: userId,
            plan_type: planType,
            status: 'active',
            expires_at: expiresAt.toISOString(),
        });

        if (insertSubError) {
            return NextResponse.json({ success: false, message: 'Gagal menyimpan langganan: ' + insertSubError.message }, { status: 500 });
        }

        await supabaseAdmin.from('profiles').update({
            is_vip: true,
            vip_expires_at: expiresAt.toISOString(),
        }).eq('id', userId);

        return NextResponse.json({ success: true, message: 'Berhasil tukar VIP' });
    } catch (error: any) {
        return NextResponse.json({ success: false, message: error.message }, { status: 500 });
    }
}
