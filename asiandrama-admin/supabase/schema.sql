-- AsianDrama Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  coin_balance INTEGER DEFAULT 0,
  is_vip BOOLEAN DEFAULT FALSE,
  vip_expires_at TIMESTAMP WITH TIME ZONE,
  is_banned BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Coin Transactions (audit trail)
CREATE TABLE coin_transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  reason TEXT,
  admin_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  display_order INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dramas
CREATE TABLE dramas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  synopsis TEXT,
  thumbnail_url TEXT,
  category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  total_episodes INTEGER DEFAULT 0,
  view_count INTEGER DEFAULT 0,
  is_published BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Episodes
CREATE TABLE episodes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  drama_id UUID REFERENCES dramas(id) ON DELETE CASCADE,
  episode_number INTEGER NOT NULL,
  title TEXT,
  duration INTEGER,
  video_url TEXT,
  thumbnail_url TEXT,
  is_vip BOOLEAN DEFAULT FALSE,
  coin_cost INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watch History
CREATE TABLE watch_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
  drama_id UUID REFERENCES dramas(id) ON DELETE CASCADE,
  progress INTEGER DEFAULT 0,
  completed BOOLEAN DEFAULT FALSE,
  watched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, episode_id)
);

-- Favorites
CREATE TABLE favorites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  drama_id UUID REFERENCES dramas(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, drama_id)
);

-- Banners
CREATE TABLE banners (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  image_url TEXT NOT NULL,
  drama_id UUID REFERENCES dramas(id) ON DELETE SET NULL,
  display_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- App Settings (key-value store)
CREATE TABLE app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default settings
INSERT INTO app_settings (key, value) VALUES
  ('app_name', 'AsianDrama'),
  ('maintenance_mode', 'false'),
  ('coin_price', '10000'),
  ('vip_monthly_price', '49000');

-- Insert default categories
INSERT INTO categories (name, slug, display_order) VALUES
  ('Romantis', 'romantis', 1),
  ('Aksi', 'aksi', 2),
  ('Komedi', 'komedi', 3),
  ('Drama', 'drama', 4),
  ('Dunia Persilatan', 'dunia-persilatan', 5);

-- RLS Policies (Row Level Security)

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE coin_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dramas ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE watch_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE banners ENABLE ROW LEVEL SECURITY;

-- Public read for published dramas
CREATE POLICY "Public can view published dramas" ON dramas
  FOR SELECT USING (is_published = true);

-- Public read for episodes of published dramas
CREATE POLICY "Public can view episodes" ON episodes
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM dramas WHERE dramas.id = episodes.drama_id AND dramas.is_published = true)
  );

-- Public read for categories
CREATE POLICY "Public can view categories" ON categories
  FOR SELECT TO PUBLIC USING (true);

-- Public read for active banners
CREATE POLICY "Public can view active banners" ON banners
  FOR SELECT USING (is_active = true);

-- Users can view/update their own profile
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Users can manage their own watch history
CREATE POLICY "Users can manage own watch history" ON watch_history
  FOR ALL USING (auth.uid() = user_id);

-- Users can manage their own favorites
CREATE POLICY "Users can manage own favorites" ON favorites
  FOR ALL USING (auth.uid() = user_id);

-- Function to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Indexes for performance
CREATE INDEX idx_dramas_category ON dramas(category_id);
CREATE INDEX idx_dramas_published ON dramas(is_published);
CREATE INDEX idx_episodes_drama ON episodes(drama_id);
CREATE INDEX idx_watch_history_user ON watch_history(user_id);
CREATE INDEX idx_watch_history_drama ON watch_history(drama_id);
CREATE INDEX idx_favorites_user ON favorites(user_id);
CREATE INDEX idx_coin_transactions_user ON coin_transactions(user_id);
