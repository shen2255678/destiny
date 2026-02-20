-- ============================================================
-- Migration 005: Fix birth_time CHECK constraint (add 'evening')
-- The original constraint in 001_initial_schema.sql was missing
-- 'evening' as a valid value, causing DB errors for evening users.
-- ============================================================

ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_birth_time_check;

ALTER TABLE public.users
  ADD CONSTRAINT users_birth_time_check
  CHECK (birth_time IN ('precise', 'morning', 'afternoon', 'evening', 'unknown'));
