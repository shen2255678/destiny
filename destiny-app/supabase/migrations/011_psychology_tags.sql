-- Migration 011: Psychology Layer tags
-- Phase I: per-user SM dynamics, karmic degree flags, and elemental profile
-- Populated by astro-service /calculate-chart via the birth-data onboarding API.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS sm_tags         JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS karmic_tags     JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS element_profile JSONB DEFAULT NULL;

COMMENT ON COLUMN public.users.sm_tags         IS 'S/M role tags from natal chart aspects (backend-only). e.g. ["Natural_Dom","Anxious_Sub"]';
COMMENT ON COLUMN public.users.karmic_tags      IS '0°/29° karmic degree tags (backend-only). e.g. ["Karmic_Crisis_VENUS"]';
COMMENT ON COLUMN public.users.element_profile  IS 'Western element counts + deficiency/dominant. {counts:{Fire,Earth,Air,Water}, deficiency:[], dominant:[]}';
