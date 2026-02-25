-- ============================================================
-- Migration 014: Natal Data Cache + Psychology Profiles + Match Results
-- Implements "compute once, query forever" architecture.
--
-- 3 new tables:
--   user_natal_data           — raw chart JSONB (backend-only black box)
--   user_psychology_profiles  — ideal_avatar tags for search/recommendation
--   matches                   — cached pairwise match results
-- ============================================================

-- ============================================================
-- 1. USER_NATAL_DATA — Raw chart data (never exposed to frontend)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.user_natal_data (
    user_id       UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    western_chart JSONB NOT NULL DEFAULT '{}',
    bazi_chart    JSONB NOT NULL DEFAULT '{}',
    zwds_chart    JSONB NOT NULL DEFAULT '{}',
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  public.user_natal_data IS 'Raw natal chart data from chart.py/bazi.py/zwds.py. Backend-only — NEVER expose to frontend.';
COMMENT ON COLUMN public.user_natal_data.western_chart IS 'Full western astrology chart JSON (planet signs, degrees, aspects)';
COMMENT ON COLUMN public.user_natal_data.bazi_chart    IS 'BaZi four pillars + ten gods + day master strength';
COMMENT ON COLUMN public.user_natal_data.zwds_chart    IS 'ZiWei DouShu 12-palace chart (Tier 1 only, empty {} for Tier 2/3)';

-- ============================================================
-- 2. USER_PSYCHOLOGY_PROFILES — Searchable trait tags
-- ============================================================
CREATE TABLE IF NOT EXISTS public.user_psychology_profiles (
    user_id              UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    relationship_dynamic TEXT,                    -- 'stable' or 'high_voltage'
    psychological_needs  JSONB DEFAULT '[]',      -- LLM-readable tag array
    favorable_elements   JSONB DEFAULT '[]',      -- 喜用神 e.g. ["火", "木"]
    dominant_elements    JSONB DEFAULT '[]',      -- 強勢五行
    karmic_boss          TEXT,                    -- 最終定位星 e.g. 'Pluto'
    llm_natal_report     TEXT,                    -- Pre-generated personal insight
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  public.user_psychology_profiles IS 'Derived psychological tags from ideal_avatar.py. Used for search/recommendation.';

-- ============================================================
-- 3. MATCHES — Cached pairwise match results
-- ============================================================
CREATE TABLE IF NOT EXISTS public.matches (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a_id          UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    user_b_id          UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    harmony_score      INTEGER,                  -- Soul Score (0-100)
    tension_level      INTEGER CHECK (tension_level BETWEEN 1 AND 5),
    badges             JSONB DEFAULT '[]',       -- Resonance badges
    tracks             JSONB DEFAULT '{}',       -- {friend, passion, partner, soul} as integers
    llm_insight_report TEXT,                     -- LLM-generated relationship report
    raw_result         JSONB DEFAULT '{}',       -- Full compute_match_v2 output (backend-only)
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_a_id, user_b_id)
);

COMMENT ON TABLE  public.matches IS 'Cached pairwise match results. Check before recomputing.';
COMMENT ON COLUMN public.matches.raw_result IS 'Full compute_match_v2 JSON — backend-only, never sent to frontend.';

-- ============================================================
-- 4. RLS POLICIES
-- ============================================================

-- user_natal_data: service role only (no direct user access)
ALTER TABLE public.user_natal_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can manage natal data"
  ON public.user_natal_data FOR ALL
  USING (true)
  WITH CHECK (true);

-- user_psychology_profiles: users can read own, service role can write
ALTER TABLE public.user_psychology_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own psychology profile"
  ON public.user_psychology_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage psychology profiles"
  ON public.user_psychology_profiles FOR ALL
  USING (true)
  WITH CHECK (true);

-- matches: users can read own matches
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own matches"
  ON public.matches FOR SELECT
  USING (auth.uid() = user_a_id OR auth.uid() = user_b_id);

CREATE POLICY "Service role can manage matches"
  ON public.matches FOR ALL
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- 5. INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_matches_user_a ON public.matches(user_a_id);
CREATE INDEX IF NOT EXISTS idx_matches_user_b ON public.matches(user_b_id);
CREATE INDEX IF NOT EXISTS idx_matches_pair   ON public.matches(user_a_id, user_b_id);

CREATE INDEX IF NOT EXISTS idx_psychology_dynamic
  ON public.user_psychology_profiles(relationship_dynamic);

-- GIN index for JSONB array queries (e.g. WHERE favorable_elements ? '火')
CREATE INDEX IF NOT EXISTS idx_psychology_favorable_elements
  ON public.user_psychology_profiles USING GIN (favorable_elements);

CREATE INDEX IF NOT EXISTS idx_psychology_dominant_elements
  ON public.user_psychology_profiles USING GIN (dominant_elements);
