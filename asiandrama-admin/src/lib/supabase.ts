import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Database types
export interface Drama {
    id: string;
    title: string;
    synopsis: string | null;
    thumbnail_url: string | null;
    category_id: string | null;
    total_episodes: number;
    view_count: number;
    is_published: boolean;
    created_at: string;
}

export interface Episode {
    id: string;
    drama_id: string;
    episode_number: number;
    title: string | null;
    duration: number | null;
    video_url: string | null;
    thumbnail_url: string | null;
    created_at: string;
}

export interface Category {
    id: string;
    name: string;
    slug: string;
    display_order: number;
}

export interface Profile {
    id: string;
    email: string | null;
    full_name: string | null;
    avatar_url: string | null;
    coin_balance: number;
    is_vip: boolean;
    vip_expires_at: string | null;
    is_banned: boolean;
    created_at: string;
}

export interface CoinTransaction {
    id: string;
    user_id: string;
    amount: number;
    reason: string | null;
    admin_id: string | null;
    created_at: string;
}

export interface Banner {
    id: string;
    image_url: string;
    drama_id: string | null;
    display_order: number;
    is_active: boolean;
}
