-- Migration 013: Add House 7 (Descendant) columns
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS house7_sign TEXT,
  ADD COLUMN IF NOT EXISTS house7_degree DOUBLE PRECISION;
