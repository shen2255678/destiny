-- Migration 016: add avatar_icon and avatar_url to soul_cards
ALTER TABLE public.soul_cards
  ADD COLUMN IF NOT EXISTS avatar_icon TEXT NOT NULL DEFAULT '✦',
  ADD COLUMN IF NOT EXISTS avatar_url  TEXT;

COMMENT ON COLUMN public.soul_cards.avatar_icon IS 'Emoji icon for soul card display. Default ✦.';
COMMENT ON COLUMN public.soul_cards.avatar_url  IS 'Custom uploaded image URL (Phase 2). Overrides avatar_icon when set.';
