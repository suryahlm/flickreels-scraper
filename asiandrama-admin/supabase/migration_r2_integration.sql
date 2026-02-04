-- Migration: Add R2 Integration Fields to Dramas Table
-- Run this in Supabase SQL Editor

-- Add FlickReels ID (original source ID)
ALTER TABLE dramas ADD COLUMN IF NOT EXISTS flickreels_id VARCHAR(20);

-- Add R2 folder name for video storage
ALTER TABLE dramas ADD COLUMN IF NOT EXISTS r2_folder VARCHAR(255);

-- Add scraped timestamp
ALTER TABLE dramas ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP WITH TIME ZONE;

-- Add source metadata (original FlickReels data)
ALTER TABLE dramas ADD COLUMN IF NOT EXISTS source_data JSONB;

-- Create index for flickreels_id lookups
CREATE INDEX IF NOT EXISTS idx_dramas_flickreels_id ON dramas(flickreels_id);

-- Update existing dramas to be published by default
UPDATE dramas SET is_published = true WHERE is_published IS NULL;

-- Set default for new dramas to be unpublished (draft)
ALTER TABLE dramas ALTER COLUMN is_published SET DEFAULT false;

-- Comment: After running this migration:
-- 1. New scraped dramas will have is_published = false (draft)
-- 2. Admin must click "Publish" to make them visible in app
-- 3. flickreels_id links to original FlickReels drama ID
-- 4. r2_folder stores the R2 folder path for video streaming
