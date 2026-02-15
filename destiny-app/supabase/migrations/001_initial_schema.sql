-- ============================================================
-- DESTINY MVP — Initial Database Schema
-- 5 Tables: users, photos, daily_matches, connections, messages
-- + RLS policies, triggers, indexes, storage bucket
-- ============================================================

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE public.users (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT UNIQUE NOT NULL,
  display_name    TEXT,
  gender          TEXT NOT NULL CHECK (gender IN ('male', 'female', 'non-binary')),
  birth_date      DATE NOT NULL,
  birth_time      TEXT CHECK (birth_time IN ('precise', 'morning', 'afternoon', 'unknown')),
  birth_time_exact TIME,
  birth_city      TEXT NOT NULL,
  birth_lat       DECIMAL(9,6),
  birth_lng       DECIMAL(9,6),
  data_tier       INT DEFAULT 3 CHECK (data_tier IN (1, 2, 3)),

  -- RPV test results
  rpv_conflict    TEXT CHECK (rpv_conflict IN ('cold_war', 'argue')),
  rpv_power       TEXT CHECK (rpv_power IN ('control', 'follow')),
  rpv_energy      TEXT CHECK (rpv_energy IN ('home', 'out')),

  -- Chart parameters (calculated by Python)
  sun_sign        TEXT,
  moon_sign       TEXT,
  venus_sign      TEXT,
  mars_sign       TEXT,
  saturn_sign     TEXT,
  ascendant_sign  TEXT,

  -- Derived psychological parameters
  attachment_style TEXT CHECK (attachment_style IN ('anxious', 'avoidant', 'secure', 'disorganized')),
  power_dynamic   TEXT CHECK (power_dynamic IN ('dominant', 'submissive', 'switch')),
  energy_level    INT,
  element_primary TEXT CHECK (element_primary IN ('fire', 'earth', 'air', 'water')),

  -- Profile
  archetype_name  TEXT,
  archetype_desc  TEXT,

  -- Onboarding status
  onboarding_step TEXT DEFAULT 'birth_data' CHECK (onboarding_step IN ('birth_data', 'rpv_test', 'photos', 'soul_report', 'complete')),

  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_users_updated
  BEFORE UPDATE ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 2. PHOTOS TABLE
-- ============================================================
CREATE TABLE public.photos (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  storage_path      TEXT NOT NULL,
  blurred_path      TEXT NOT NULL,
  half_blurred_path TEXT,
  upload_order      INT NOT NULL CHECK (upload_order IN (1, 2)),
  created_at        TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, upload_order)
);

-- ============================================================
-- 3. DAILY_MATCHES TABLE
-- ============================================================
CREATE TABLE public.daily_matches (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES public.users(id),
  matched_user_id     UUID NOT NULL REFERENCES public.users(id),
  match_date          DATE NOT NULL DEFAULT CURRENT_DATE,

  -- Score breakdown
  kernel_score        DECIMAL(4,2),
  power_score         DECIMAL(4,2),
  glitch_score        DECIMAL(4,2),
  total_score         DECIMAL(4,2),
  match_type          TEXT CHECK (match_type IN ('complementary', 'similar', 'tension')),

  -- Chameleon tags (AI-generated, relative to viewer)
  tags                JSONB DEFAULT '[]'::jsonb,
  radar_passion       INT CHECK (radar_passion BETWEEN 0 AND 100),
  radar_stability     INT CHECK (radar_stability BETWEEN 0 AND 100),
  radar_communication INT CHECK (radar_communication BETWEEN 0 AND 100),

  -- Card visual
  card_color          TEXT CHECK (card_color IN ('coral', 'blue', 'purple')),

  -- User actions
  user_action         TEXT DEFAULT 'pending' CHECK (user_action IN ('pending', 'accept', 'pass')),

  created_at          TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, matched_user_id, match_date)
);

-- ============================================================
-- 4. CONNECTIONS TABLE
-- ============================================================
CREATE TABLE public.connections (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id           UUID NOT NULL REFERENCES public.users(id),
  user_b_id           UUID NOT NULL REFERENCES public.users(id),
  match_id            UUID REFERENCES public.daily_matches(id),

  -- Ice-breaker
  icebreaker_question TEXT,
  user_a_answer       TEXT,
  user_b_answer       TEXT,
  icebreaker_tags     JSONB,

  -- Sync rate
  sync_level          INT DEFAULT 1 CHECK (sync_level IN (1, 2, 3)),
  message_count       INT DEFAULT 0,
  call_duration       INT DEFAULT 0,

  -- Status
  status              TEXT DEFAULT 'icebreaker' CHECK (status IN ('icebreaker', 'active', 'expired')),
  last_activity       TIMESTAMPTZ DEFAULT NOW(),

  created_at          TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT different_users CHECK (user_a_id != user_b_id)
);

-- ============================================================
-- 5. MESSAGES TABLE
-- ============================================================
CREATE TABLE public.messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id   UUID NOT NULL REFERENCES public.connections(id) ON DELETE CASCADE,
  sender_id       UUID NOT NULL REFERENCES public.users(id),
  content         TEXT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TRIGGER: On message insert → update connection stats
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.connections
  SET
    message_count = message_count + 1,
    last_activity = NOW(),
    sync_level = CASE
      WHEN message_count + 1 >= 50 THEN 3
      WHEN message_count + 1 >= 10 THEN 2
      ELSE 1
    END
  WHERE id = NEW.connection_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_message_insert
  AFTER INSERT ON public.messages
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_message();

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_photos_user_id ON public.photos(user_id);
CREATE INDEX idx_daily_matches_user_date ON public.daily_matches(user_id, match_date);
CREATE INDEX idx_daily_matches_matched_user ON public.daily_matches(matched_user_id, match_date);
CREATE INDEX idx_connections_users ON public.connections(user_a_id, user_b_id);
CREATE INDEX idx_connections_status ON public.connections(status);
CREATE INDEX idx_connections_last_activity ON public.connections(last_activity) WHERE status = 'active';
CREATE INDEX idx_messages_connection ON public.messages(connection_id, created_at);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- USERS: read own, update own
CREATE POLICY "Users can read own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Allow reading matched users' basic info (for match cards)
CREATE POLICY "Users can read matched users"
  ON public.users FOR SELECT
  USING (
    id IN (
      SELECT matched_user_id FROM public.daily_matches WHERE user_id = auth.uid()
      UNION
      SELECT user_a_id FROM public.connections WHERE user_b_id = auth.uid()
      UNION
      SELECT user_b_id FROM public.connections WHERE user_a_id = auth.uid()
    )
  );

-- PHOTOS: own photos + matched users' photos
CREATE POLICY "Users can manage own photos"
  ON public.photos FOR ALL
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view matched users photos"
  ON public.photos FOR SELECT
  USING (
    user_id IN (
      SELECT matched_user_id FROM public.daily_matches WHERE user_id = auth.uid()
      UNION
      SELECT user_a_id FROM public.connections WHERE user_b_id = auth.uid()
      UNION
      SELECT user_b_id FROM public.connections WHERE user_a_id = auth.uid()
    )
  );

-- DAILY_MATCHES: read own matches
CREATE POLICY "Users can read own matches"
  ON public.daily_matches FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own match actions"
  ON public.daily_matches FOR UPDATE
  USING (auth.uid() = user_id);

-- CONNECTIONS: read/update own connections
CREATE POLICY "Users can read own connections"
  ON public.connections FOR SELECT
  USING (auth.uid() = user_a_id OR auth.uid() = user_b_id);

CREATE POLICY "Users can update own connections"
  ON public.connections FOR UPDATE
  USING (auth.uid() = user_a_id OR auth.uid() = user_b_id);

-- MESSAGES: read/insert in own connections
CREATE POLICY "Users can read messages in own connections"
  ON public.messages FOR SELECT
  USING (
    connection_id IN (
      SELECT id FROM public.connections
      WHERE user_a_id = auth.uid() OR user_b_id = auth.uid()
    )
  );

CREATE POLICY "Users can send messages in own connections"
  ON public.messages FOR INSERT
  WITH CHECK (
    auth.uid() = sender_id
    AND connection_id IN (
      SELECT id FROM public.connections
      WHERE (user_a_id = auth.uid() OR user_b_id = auth.uid())
        AND status = 'active'
    )
  );

-- ============================================================
-- STORAGE BUCKET: photos
-- ============================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('photos', 'photos', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Users can upload own photos"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'photos'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Users can view photos through app"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'photos');

CREATE POLICY "Users can delete own photos"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'photos'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );
