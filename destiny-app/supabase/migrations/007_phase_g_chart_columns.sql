-- Migration 007: Phase G — Expanded matching columns
-- New celestial bodies + House cusps + Attachment role
-- Note: attachment_style already defined in 001_initial_schema.sql

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS mercury_sign      TEXT,
  ADD COLUMN IF NOT EXISTS jupiter_sign      TEXT,
  ADD COLUMN IF NOT EXISTS pluto_sign        TEXT,
  ADD COLUMN IF NOT EXISTS chiron_sign       TEXT,
  ADD COLUMN IF NOT EXISTS juno_sign         TEXT,
  ADD COLUMN IF NOT EXISTS house4_sign       TEXT,
  ADD COLUMN IF NOT EXISTS house8_sign       TEXT,
  ADD COLUMN IF NOT EXISTS attachment_role   TEXT
    CHECK (attachment_role IN ('dom_secure', 'sub_secure', 'balanced'));
