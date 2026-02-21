-- Migration 009: BaZi branch fields, emotional capacity, Uranus/Neptune
-- Phase H v1.4/v1.5 algorithm additions

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS house12_sign        TEXT,
  ADD COLUMN IF NOT EXISTS uranus_sign         TEXT,
  ADD COLUMN IF NOT EXISTS neptune_sign        TEXT,
  ADD COLUMN IF NOT EXISTS bazi_month_branch   TEXT,
  ADD COLUMN IF NOT EXISTS bazi_day_branch     TEXT,
  ADD COLUMN IF NOT EXISTS emotional_capacity  INTEGER DEFAULT 50;

COMMENT ON COLUMN public.users.house12_sign       IS '第12宮星座 (Tier 1 only)';
COMMENT ON COLUMN public.users.uranus_sign        IS '天王星星座 (generational, ~7 yr/sign)';
COMMENT ON COLUMN public.users.neptune_sign       IS '海王星星座 (generational, ~14 yr/sign)';
COMMENT ON COLUMN public.users.bazi_month_branch  IS '八字月支 調候喜用神 e.g. 卯, 午';
COMMENT ON COLUMN public.users.bazi_day_branch    IS '八字日支 夫妻宮 e.g. 申, 午 — used for 刑沖破害 matching';
COMMENT ON COLUMN public.users.emotional_capacity IS '情緒容量 0-100 (auto-computed from chart + ZWDS)';
