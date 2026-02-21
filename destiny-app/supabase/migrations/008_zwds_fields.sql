-- Migration 008: ZWDS (紫微斗數) pre-computed chart summary
-- Cached on Tier 1 onboarding to avoid recomputing on every match

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS zwds_life_palace_stars   TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_spouse_palace_stars  TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_karma_palace_stars   TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_four_transforms      JSONB,
  ADD COLUMN IF NOT EXISTS zwds_five_element         TEXT,
  ADD COLUMN IF NOT EXISTS zwds_body_palace_name     TEXT,
  ADD COLUMN IF NOT EXISTS zwds_defense_triggers     TEXT[];

COMMENT ON COLUMN public.users.zwds_life_palace_stars  IS '命宮主星 (Tier 1 only)';
COMMENT ON COLUMN public.users.zwds_spouse_palace_stars IS '夫妻宮主星';
COMMENT ON COLUMN public.users.zwds_karma_palace_stars  IS '福德宮主星';
COMMENT ON COLUMN public.users.zwds_four_transforms     IS '四化飛星 {hua_lu,hua_quan,hua_ke,hua_ji}';
COMMENT ON COLUMN public.users.zwds_five_element        IS '五行局';
COMMENT ON COLUMN public.users.zwds_body_palace_name    IS '身宮宮位';
COMMENT ON COLUMN public.users.zwds_defense_triggers    IS '煞星防禦機制 tags';
