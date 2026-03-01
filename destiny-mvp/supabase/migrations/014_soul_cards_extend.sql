-- Migration 014: extend soul_cards with yin_yang + profile cache fields
ALTER TABLE public.soul_cards
  ADD COLUMN IF NOT EXISTS yin_yang          TEXT NOT NULL DEFAULT 'yang',
  ADD COLUMN IF NOT EXISTS profile_card_data JSONB,
  ADD COLUMN IF NOT EXISTS ideal_match_data  JSONB,
  ADD COLUMN IF NOT EXISTS updated_at        TIMESTAMPTZ DEFAULT NOW();
