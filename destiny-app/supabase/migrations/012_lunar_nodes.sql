-- Algorithm v1.8: Lunar Node columns for karmic synastry triggers
-- North Node (北交點) + South Node (南交點) — available at all data tiers

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS north_node_sign   TEXT,
  ADD COLUMN IF NOT EXISTS north_node_degree DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS south_node_sign   TEXT,
  ADD COLUMN IF NOT EXISTS south_node_degree DOUBLE PRECISION;
