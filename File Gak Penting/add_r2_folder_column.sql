-- Add r2_folder column to dramas table
ALTER TABLE dramas ADD COLUMN IF NOT EXISTS r2_folder TEXT;
