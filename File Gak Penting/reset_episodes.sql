-- Reset all drama episode counts after R2 wipe
-- Run this in Supabase SQL Editor

-- Set all episodes to 0 (will be updated after re-scraping)
UPDATE dramas SET total_episodes = 0;

-- Optional: Set is_published = false for all dramas  
-- UPDATE dramas SET is_published = false;

-- Show result
SELECT id, title, total_episodes FROM dramas LIMIT 10;
