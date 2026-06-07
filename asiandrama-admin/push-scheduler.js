/**
 * push-scheduler.js
 * Automated Push Notification Scheduler for AsianDrama
 *
 * Runs as a standalone Node.js service on VPS.
 *
 * Schedule (all WIB = UTC+7):
 *   - 09:00 daily        → Absen harian + koin reminder (only to users who haven't checked in)
 *   - 10:00 daily        → Re-engagement (users inactive 2+ days)
 *   - 19:00 daily        → Resume watching (users with unfinished dramas)
 *   - 10:00 Sat & Sun    → Weekend special notification
 */

const { createClient } = require('@supabase/supabase-js');

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
    || 'http://supabasekong-ik8wccc844k48ogks8g844sg.141.11.160.187.sslip.io';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY
    || 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc3MjM4MTM0MCwiZXhwIjo0OTI4MDU0OTQwLCJyb2xlIjoic2VydmljZV9yb2xlIn0.i0ZTgS2IzqYdMLzpNsSWmpqYuT8YnTxXe1c3R0OJAp4';
const EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send';
const BATCH_SIZE = 100;
const WIB_OFFSET_MS = 7 * 60 * 60 * 1000; // UTC+7 in milliseconds

// ─── SUPABASE ─────────────────────────────────────────────────────────────────
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// ─── HELPERS ──────────────────────────────────────────────────────────────────

/** Returns current Date object with time adjusted to WIB (UTC+7) */
function nowWIB() {
    return new Date(Date.now() + WIB_OFFSET_MS);
}

/** Returns today's date string in WIB as YYYY-MM-DD */
function todayWIB() {
    return nowWIB().toISOString().split('T')[0];
}

function log(msg) {
    console.log(`[${new Date().toISOString()}] ${msg}`);
}

/**
 * Send push notifications in batches.
 * @param {string[]} tokens - Array of ExponentPushToken strings
 * @param {string} title
 * @param {string} body
 * @param {object} data - Extra data payload
 */
async function sendPushBatch(tokens, title, body, data = {}) {
    const validTokens = (tokens || []).filter(t => t && t.startsWith('ExponentPushToken['));

    if (validTokens.length === 0) {
        log('No valid tokens — skipping send.');
        return { sent: 0, failed: 0 };
    }

    log(`Sending "${title}" to ${validTokens.length} devices...`);
    let sent = 0;
    let failed = 0;

    for (let i = 0; i < validTokens.length; i += BATCH_SIZE) {
        const batch = validTokens.slice(i, i + BATCH_SIZE);
        const messages = batch.map(token => ({
            to: token,
            title,
            body,
            data,
            sound: 'default',
            priority: 'high',
            channelId: 'default',
        }));

        try {
            const res = await fetch(EXPO_PUSH_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(messages),
            });
            const result = await res.json();
            if (result.data) {
                const batchFailed = result.data.filter(r => r.status === 'error').length;
                sent += batch.length - batchFailed;
                failed += batchFailed;
            }
        } catch (err) {
            log(`Batch send error: ${err.message}`);
            failed += batch.length;
        }
    }

    log(`Result: ${sent} sent, ${failed} failed`);
    return { sent, failed };
}

// ─── JOB 1: DAILY CHECK-IN REMINDER ─────────────────────────────────────────
/**
 * 09:00 WIB — Remind users who have NOT checked in today yet.
 */
async function jobDailyCheckinReminder() {
    log('▶️  JOB 1: Daily Check-in Reminder');
    const today = todayWIB();

    // All users with push token
    const { data: allUsers, error: userErr } = await supabase
        .from('profiles')
        .select('id, expo_push_token')
        .not('expo_push_token', 'is', null)
        .neq('expo_push_token', '');

    if (userErr) {
        log(`Error fetching users: ${userErr.message}`);
        return;
    }

    // Users who already checked in today
    const { data: checkedIn } = await supabase
        .from('daily_checkins')
        .select('user_id')
        .eq('checkin_date', today);

    const checkedInIds = new Set((checkedIn || []).map(c => c.user_id));

    // Only users who have NOT checked in
    const tokens = (allUsers || [])
        .filter(u => !checkedInIds.has(u.id))
        .map(u => u.expo_push_token);

    log(`Total users: ${(allUsers || []).length}, checked in: ${checkedInIds.size}, to notify: ${tokens.length}`);

    const VARIANTS = [
        {
            title: '🎁 Absen Harian Menunggumu!',
            body: 'Klaim koinmu hari ini dan tonton iklan untuk koin tambahan. Gratis!',
        },
        {
            title: '💰 Jangan Lewatkan Koinmu!',
            body: 'Absen harian dan tonton iklan untuk kumpulkan koin. Buka AsianDrama sekarang!',
        },
        {
            title: '⭐ Reward Harianmu Sudah Siap!',
            body: 'Tap absen sekarang dan nonton iklan singkat untuk dapat koin gratis!',
        },
    ];
    // Rotate variant by day of week so messages don't feel repetitive
    const variant = VARIANTS[new Date().getDay() % VARIANTS.length];

    await sendPushBatch(tokens, variant.title, variant.body, { screen: 'daily_checkin' });
}

// ─── JOB 2: RE-ENGAGEMENT (INACTIVE 2+ DAYS) ─────────────────────────────────
/**
 * 10:00 WIB — Remind users who haven't opened the app in 2+ days.
 */
async function jobReEngagement() {
    log('▶️  JOB 2: Re-engagement (Inactive 2+ days)');

    // Calculate date 2 days ago in UTC (activity_date is stored as DATE)
    const twoDaysAgo = new Date();
    twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
    const twoDaysAgoStr = twoDaysAgo.toISOString().split('T')[0];

    // Users active in last 2 days
    const { data: recentActive } = await supabase
        .from('user_activity_log')
        .select('user_id')
        .gte('activity_date', twoDaysAgoStr);

    const recentActiveIds = new Set((recentActive || []).map(a => a.user_id));

    // All users with push token
    const { data: allUsers, error } = await supabase
        .from('profiles')
        .select('id, expo_push_token')
        .not('expo_push_token', 'is', null)
        .neq('expo_push_token', '');

    if (error) {
        log(`Error: ${error.message}`);
        return;
    }

    // Users NOT seen in last 2 days
    const tokens = (allUsers || [])
        .filter(u => !recentActiveIds.has(u.id))
        .map(u => u.expo_push_token);

    log(`Inactive users to notify: ${tokens.length}`);

    const VARIANTS = [
        { title: '👋 Hei, kami kangen kamu!', body: 'Ada banyak drama seru yang menunggu. Yuk balik nonton di AsianDrama!' },
        { title: '🎬 Sudah lama tidak nonton nih!', body: 'Drama-drama pilihan terbaik sudah siap untukmu. Buka sekarang!' },
        { title: '✨ Ada drama menarik untukmu!', body: 'Sudah beberapa hari kamu pergi. Ayo balik dan nikmati drama favoritmu!' },
        { title: '🍿 Waktu nonton drama!', body: 'Jangan sampai ketinggalan cerita seru. AsianDrama menunggumu!' },
    ];
    const variant = VARIANTS[Math.floor(Math.random() * VARIANTS.length)];

    await sendPushBatch(tokens, variant.title, variant.body, { screen: 'home' });
}

// ─── JOB 3: RESUME WATCHING ───────────────────────────────────────────────────
/**
 * 19:00 WIB — Remind users who have unfinished dramas and haven't watched in 1+ day.
 * Personalized: includes drama title and episode number.
 */
async function jobResumeWatching() {
    log('▶️  JOB 3: Resume Watching Reminder');

    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);

    // Get watch_progress rows where last watched > 1 day ago
    // Join with profiles to get the push token
    const { data, error } = await supabase
        .from('watch_progress')
        .select('user_id, drama_title, last_episode, total_episodes, last_watched_at, profiles!inner(expo_push_token)')
        .lt('last_watched_at', oneDayAgo.toISOString())
        .not('profiles.expo_push_token', 'is', null)
        .neq('profiles.expo_push_token', '');

    if (error) {
        log(`Error fetching watch_progress: ${error.message}`);
        return;
    }

    // Deduplicate: one notification per user — their most recent unfinished drama
    // (Supabase returns sorted by created_at by default, we take first unfinished per user)
    const perUser = new Map();
    for (const row of (data || [])) {
        // Skip if drama is already fully watched
        if (row.total_episodes && row.last_episode >= row.total_episodes) continue;

        // Only keep first occurrence per user (most recent unfinished)
        if (!perUser.has(row.user_id)) {
            perUser.set(row.user_id, row);
        }
    }

    const entries = Array.from(perUser.values());
    log(`Users with unfinished drama: ${entries.length}`);

    if (entries.length === 0) return;

    // Build personalized messages — send as one batch
    const messages = entries.map(row => {
        const totalInfo = row.total_episodes ? `/${row.total_episodes}` : '';
        return {
            to: row.profiles.expo_push_token,
            title: '▶️ Lanjutkan Menonton!',
            body: `Kamu baru sampai EP ${row.last_episode}${totalInfo} di "${row.drama_title}". Lanjutkan sekarang!`,
            data: { screen: 'collection' },
            sound: 'default',
            priority: 'high',
            channelId: 'default',
        };
    });

    let sent = 0;
    let failed = 0;
    for (let i = 0; i < messages.length; i += BATCH_SIZE) {
        const batch = messages.slice(i, i + BATCH_SIZE);
        try {
            const res = await fetch(EXPO_PUSH_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(batch),
            });
            const result = await res.json();
            if (result.data) {
                const batchFailed = result.data.filter(r => r.status === 'error').length;
                sent += batch.length - batchFailed;
                failed += batchFailed;
            }
        } catch (err) {
            log(`Batch error: ${err.message}`);
            failed += batch.length;
        }
    }
    log(`Result: ${sent} sent, ${failed} failed`);
}

// ─── JOB 4: WEEKEND NOTIFICATION ─────────────────────────────────────────────
/**
 * 10:00 WIB Saturday & Sunday — Send weekend greeting to all users.
 * Checked hourly; fires once per day when conditions are met.
 */
async function jobWeekend() {
    log('▶️  JOB 4: Weekend Special Notification');

    const { data: allUsers, error } = await supabase
        .from('profiles')
        .select('expo_push_token')
        .not('expo_push_token', 'is', null)
        .neq('expo_push_token', '');

    if (error) {
        log(`Error: ${error.message}`);
        return;
    }

    const tokens = (allUsers || []).map(u => u.expo_push_token);
    log(`Weekend notif to ${tokens.length} users`);

    const wib = nowWIB();
    const isSaturday = wib.getDay() === 6;

    const SATURDAY_VARIANTS = [
        { title: '🎉 Selamat Weekend!', body: 'Isi Sabtu seru dengan drama pilihan terbaik di AsianDrama. Enjoy!' },
        { title: '🍿 Weekend = Waktu Nonton!', body: 'Sabtu santai? Tonton drama favoritmu di AsianDrama sekarang!' },
    ];
    const SUNDAY_VARIANTS = [
        { title: '☀️ Selamat Hari Minggu!', body: 'Sebelum pekan baru dimulai, santai dulu dengan drama seru di AsianDrama!' },
        { title: '🎬 Akhiri Weekend dengan Seru!', body: 'Nikmati sisa Minggu dengan drama-drama pilihan terbaik. Buka AsianDrama!' },
    ];

    const pool = isSaturday ? SATURDAY_VARIANTS : SUNDAY_VARIANTS;
    const variant = pool[Math.floor(Math.random() * pool.length)];

    await sendPushBatch(tokens, variant.title, variant.body, { screen: 'home' });
}

// ─── SCHEDULER ────────────────────────────────────────────────────────────────

/**
 * Returns milliseconds until the next occurrence of targetHourWIB:targetMinuteWIB.
 */
function msUntilWIB(targetHourWIB, targetMinuteWIB = 0) {
    const now = Date.now();
    const wibNow = nowWIB(); // Date object with WIB time in UTC fields

    // Build next run time in WIB
    const nextRun = new Date(wibNow);
    nextRun.setUTCHours(targetHourWIB, targetMinuteWIB, 0, 0);

    // If that time has already passed today (WIB), push to tomorrow
    if (nextRun <= wibNow) {
        nextRun.setUTCDate(nextRun.getUTCDate() + 1);
    }

    // Convert back to real milliseconds (subtract the offset we added)
    const nextRunReal = nextRun.getTime() - WIB_OFFSET_MS;
    return nextRunReal - now;
}

/**
 * Schedule a job to run daily at a fixed WIB time.
 */
function scheduleDailyAt(hourWIB, minuteWIB = 0, jobFn, jobName) {
    const delay = msUntilWIB(hourWIB, minuteWIB);
    const hh = String(hourWIB).padStart(2, '0');
    const mm = String(minuteWIB).padStart(2, '0');
    log(`⏰ "${jobName}" → first run in ${Math.round(delay / 60000)} min (daily at ${hh}:${mm} WIB)`);

    setTimeout(async () => {
        await jobFn();
        // After first run, repeat exactly every 24 hours
        setInterval(jobFn, 24 * 60 * 60 * 1000);
    }, delay);
}

/**
 * Weekend job: checked every hour; fires when it's Sat or Sun and the clock
 * hits the target hour in WIB. Guard prevents double-fire within the same hour.
 */
function scheduleWeekendAt(hourWIB) {
    let lastFiredDate = ''; // Track last fire date to prevent double-fire

    const check = async () => {
        const wib = nowWIB();
        const day = wib.getUTCDay();     // 0=Sun, 6=Sat (getDay on WIB Date uses UTC fields)
        const hour = wib.getUTCHours();
        const dateStr = wib.toISOString().split('T')[0];

        if ((day === 6 || day === 0) && hour === hourWIB && dateStr !== lastFiredDate) {
            lastFiredDate = dateStr;
            await jobWeekend();
        }
    };

    setInterval(check, 60 * 60 * 1000); // Check every hour
    log(`⏰ "Weekend Special" → fires every Sat & Sun at ${String(hourWIB).padStart(2, '0')}:00 WIB (hourly check)`);
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────
log('🚀 AsianDrama Push Scheduler starting...');

scheduleDailyAt(9,  0, jobDailyCheckinReminder, 'Daily Check-in Reminder');
scheduleDailyAt(10, 0, jobReEngagement,         'Re-engagement (Inactive 2d+)');
scheduleDailyAt(19, 0, jobResumeWatching,       'Resume Watching Reminder');
scheduleWeekendAt(10);

log('✅ All jobs scheduled. Scheduler running.');

// Keep process alive and handle errors gracefully
process.on('SIGTERM', () => { log('SIGTERM received — shutting down.'); process.exit(0); });
process.on('SIGINT',  () => { log('SIGINT received — shutting down.'); process.exit(0); });
process.on('uncaughtException', err => log(`Uncaught exception: ${err.message}\n${err.stack}`));
process.on('unhandledRejection', reason => log(`Unhandled rejection: ${reason}`));
