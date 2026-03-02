-- 015: ranking_cache — pre-computed quick-score results for the ranking page
CREATE TABLE IF NOT EXISTS public.ranking_cache (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_a_id     UUID NOT NULL REFERENCES public.soul_cards(id) ON DELETE CASCADE,
  card_b_id     UUID NOT NULL REFERENCES public.soul_cards(id) ON DELETE CASCADE,
  harmony       SMALLINT NOT NULL,
  lust          SMALLINT NOT NULL,
  soul          SMALLINT NOT NULL,
  primary_track TEXT NOT NULL,
  quadrant      TEXT,
  labels        JSONB DEFAULT '[]',
  tracks        JSONB DEFAULT '{}',
  computed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(card_a_id, card_b_id)
);

CREATE INDEX idx_ranking_cache_card_a ON ranking_cache(card_a_id);

ALTER TABLE ranking_cache ENABLE ROW LEVEL SECURITY;

-- SELECT only: users can read rows where card_a belongs to them
-- INSERT/UPDATE/DELETE: only via service_role (server-side)
CREATE POLICY ranking_cache_owner_select ON ranking_cache
  FOR SELECT USING (
    card_a_id IN (SELECT id FROM soul_cards WHERE owner_id = auth.uid())
  );
