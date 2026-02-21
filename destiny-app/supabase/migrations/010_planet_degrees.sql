-- Migration 010: Add planet_degrees JSONB column
-- Stores exact ecliptic longitudes (0-360°) for all planets, asteroids, and house cusps.
-- Used by the matching algorithm for orb-based exact degree aspect scoring.
-- Replaces the sign-only approximation and enables compute_exact_aspect() in matching.py.
--
-- Schema: { sun_degree: float, moon_degree: float, ..., house4_degree: float, ... }
-- Populated by the astro-service /calculate-chart endpoint via the birth-data API route.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS planet_degrees JSONB;
