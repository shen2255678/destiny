-- ============================================================
-- Add BaZi (八字) columns to users table
-- ============================================================

-- Day Master: the Heavenly Stem of the Day Pillar (甲-癸)
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS bazi_day_master TEXT;

-- Day Master element (wood/fire/earth/metal/water)
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS bazi_element TEXT
CHECK (bazi_element IN ('wood', 'fire', 'earth', 'metal', 'water'));

-- Full four pillars data as JSON
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS bazi_four_pillars JSONB;
