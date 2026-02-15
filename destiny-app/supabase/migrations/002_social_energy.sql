-- ============================================================
-- Add social_energy column to users table
-- Values: 'high', 'medium', 'low' (default: 'medium')
-- ============================================================

ALTER TABLE public.users
ADD COLUMN social_energy TEXT DEFAULT 'medium'
CHECK (social_energy IN ('high', 'medium', 'low'));
