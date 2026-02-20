-- Migration 006: Dynamic Birth Time Rectification Data Layer
-- Adds accuracy_type, window fields, rectification state columns to users,
-- and creates rectification_events table.

-- -----------------------------------------------------------------------
-- 1. Add new columns to users table
-- -----------------------------------------------------------------------

ALTER TABLE public.users
  -- Birth time precision input
  ADD COLUMN IF NOT EXISTS accuracy_type TEXT
    CHECK (accuracy_type IN ('PRECISE', 'TWO_HOUR_SLOT', 'FUZZY_DAY')),

  -- Time window provided by user (HH:mm strings stored as TIME)
  ADD COLUMN IF NOT EXISTS window_start TIME,
  ADD COLUMN IF NOT EXISTS window_end TIME,
  ADD COLUMN IF NOT EXISTS window_size_minutes INTEGER,

  -- Rectification state
  ADD COLUMN IF NOT EXISTS rectification_status TEXT
    NOT NULL DEFAULT 'unrectified'
    CHECK (rectification_status IN (
      'unrectified', 'collecting_signals', 'narrowed_to_2hr',
      'narrowed_to_d9', 'locked', 'needs_review'
    )),
  ADD COLUMN IF NOT EXISTS current_confidence NUMERIC(4,3)
    NOT NULL DEFAULT 0.000,

  -- Active candidate time range (system's current best estimate)
  ADD COLUMN IF NOT EXISTS active_range_start TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS active_range_end TIMESTAMPTZ,

  -- Final locked result
  ADD COLUMN IF NOT EXISTS calibrated_time TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS active_d9_slot INTEGER,

  -- Boundary case flag + personalization signals
  ADD COLUMN IF NOT EXISTS is_boundary_case BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS dealbreakers TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS priorities TEXT
    CHECK (priorities IN ('Achievement', 'LifeQuality'));

-- -----------------------------------------------------------------------
-- 2. Create rectification_events table
-- -----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.rectification_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  source      TEXT NOT NULL
    CHECK (source IN ('signup', 'daily_quiz', 'interaction', 'post_date_feedback', 'admin')),
  event_type  TEXT NOT NULL
    CHECK (event_type IN (
      'range_initialized', 'range_narrowed', 'candidate_eliminated',
      'confidence_updated', 'locked', 'flagged_needs_review'
    )),
  payload     JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------
-- 3. RLS for rectification_events
-- -----------------------------------------------------------------------

ALTER TABLE public.rectification_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own rectification events"
  ON public.rectification_events FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own rectification events"
  ON public.rectification_events FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- -----------------------------------------------------------------------
-- 4. Indexes
-- -----------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_rectification_events_user_id
  ON public.rectification_events(user_id);

CREATE INDEX IF NOT EXISTS idx_rectification_events_user_ts
  ON public.rectification_events(user_id, ts DESC);
