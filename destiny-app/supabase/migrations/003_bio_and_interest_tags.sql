-- ============================================================
-- Add bio and interest_tags columns to users table
-- ============================================================

ALTER TABLE public.users
ADD COLUMN bio TEXT CHECK (char_length(bio) <= 500);

ALTER TABLE public.users
ADD COLUMN interest_tags JSONB DEFAULT '[]'::jsonb;
