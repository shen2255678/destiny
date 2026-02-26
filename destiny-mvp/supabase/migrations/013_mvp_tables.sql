-- ============================================================
-- DESTINY MVP — Migration 013
-- Tables: soul_cards, mvp_matches
-- Run this in Supabase SQL Editor for project masninqgihbazjirweiy
-- ============================================================

-- Extend users with token balance
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tokens INT DEFAULT 3;

-- Soul cards: cached natal chart per person-entry
CREATE TABLE IF NOT EXISTS public.soul_cards (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  birth_date   DATE NOT NULL,
  birth_time   TIME,
  lat          DECIMAL(9,6),
  lng          DECIMAL(9,6),
  timezone     TEXT,
  data_tier    SMALLINT DEFAULT 3 CHECK (data_tier IN (1,2,3)),
  gender       CHAR(1) CHECK (gender IN ('M','F')),
  natal_cache  JSONB,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.soul_cards ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'soul_cards'
      AND policyname = 'soul_cards_owner_all'
  ) THEN
    CREATE POLICY "soul_cards_owner_all" ON public.soul_cards
      FOR ALL USING (auth.uid() = owner_id)
      WITH CHECK (auth.uid() = owner_id);
  END IF;
END
$$;

-- Matches: synastry results
CREATE TABLE IF NOT EXISTS public.mvp_matches (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name_a          TEXT,
  name_b          TEXT,
  harmony_score   INT,
  lust_score      INT,
  soul_score      INT,
  tracks          JSONB,
  labels          JSONB,
  report_json     JSONB,
  share_token     TEXT UNIQUE DEFAULT encode(gen_random_bytes(12), 'hex'),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.mvp_matches ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'mvp_matches'
      AND policyname = 'mvp_matches_owner_select'
  ) THEN
    CREATE POLICY "mvp_matches_owner_select" ON public.mvp_matches
      FOR SELECT USING (auth.uid() = user_id);
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'mvp_matches'
      AND policyname = 'mvp_matches_owner_insert'
  ) THEN
    CREATE POLICY "mvp_matches_owner_insert" ON public.mvp_matches
      FOR INSERT WITH CHECK (auth.uid() = user_id);
  END IF;
END
$$;
