import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Provide fallback for build time when env vars aren't available
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

// Public client (anon key) - subject to RLS
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey);

// Admin client (service_role key) - bypasses ALL RLS policies
// Use this for admin operations like storage upload, settings update, etc.
export const supabaseAdmin: SupabaseClient = supabaseServiceKey
    ? createClient(supabaseUrl, supabaseServiceKey)
    : supabase; // Fallback to anon if no service key

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
