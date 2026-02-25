# -*- coding: utf-8 -*-
"""
DESTINY — Supabase Database Client
Thin wrapper around Supabase Python client for natal data caching,
psychology profiles, and match result storage.

Required environment variables (reads from Next.js .env.local convention):
  NEXT_PUBLIC_SUPABASE_URL       — e.g. https://xxxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY      — service_role key (NOT anon key)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from supabase import create_client, Client


def _get_client() -> Client:
    """Create or return a Supabase client using environment variables."""
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Check your .env.local or environment variables."
        )
    return create_client(url, key)


# ── Natal Data (user_natal_data) ─────────────────────────────────────────────

def upsert_natal_data(
    user_id: str,
    western_chart: dict,
    bazi_chart: dict,
    zwds_chart: dict,
) -> None:
    """Write or update raw natal chart data for a user.

    This data is NEVER exposed to the frontend.
    """
    client = _get_client()
    client.table("user_natal_data").upsert({
        "user_id": user_id,
        "western_chart": western_chart,
        "bazi_chart": bazi_chart,
        "zwds_chart": zwds_chart,
    }).execute()


def get_natal_data(user_id: str) -> Optional[dict]:
    """Retrieve raw natal chart data for a user.

    Returns dict with keys: western_chart, bazi_chart, zwds_chart.
    Returns None if no data found.
    """
    client = _get_client()
    result = client.table("user_natal_data") \
        .select("western_chart, bazi_chart, zwds_chart") \
        .eq("user_id", user_id) \
        .maybe_single() \
        .execute()
    return result.data if result.data else None


# ── Psychology Profiles (user_psychology_profiles) ───────────────────────────

def upsert_psychology_profile(user_id: str, profile: dict) -> None:
    """Write or update psychology profile for a user.

    profile should contain keys from ideal_avatar.extract_ideal_partner_profile:
      relationship_dynamic, psychological_needs, favorable_elements, etc.
    """
    client = _get_client()
    row = {"user_id": user_id}
    # Map known fields
    for field in [
        "relationship_dynamic", "psychological_needs",
        "favorable_elements", "dominant_elements",
        "karmic_boss", "llm_natal_report",
    ]:
        if field in profile:
            row[field] = profile[field]
    client.table("user_psychology_profiles").upsert(row).execute()


def get_psychology_profile(user_id: str) -> Optional[dict]:
    """Retrieve psychology profile for a user."""
    client = _get_client()
    result = client.table("user_psychology_profiles") \
        .select("*") \
        .eq("user_id", user_id) \
        .maybe_single() \
        .execute()
    return result.data if result.data else None


# ── Match Results (matches) ──────────────────────────────────────────────────

def get_cached_match(user_a_id: str, user_b_id: str) -> Optional[dict]:
    """Check if a match result already exists for this pair.

    Returns the cached match row if found, None otherwise.
    Checks both directions (A→B and B→A).
    """
    client = _get_client()

    # Check A→B direction
    result = client.table("matches") \
        .select("*") \
        .eq("user_a_id", user_a_id) \
        .eq("user_b_id", user_b_id) \
        .maybe_single() \
        .execute()
    if result.data:
        return result.data

    # Check B→A direction
    result = client.table("matches") \
        .select("*") \
        .eq("user_a_id", user_b_id) \
        .eq("user_b_id", user_a_id) \
        .maybe_single() \
        .execute()
    return result.data if result.data else None


def save_match_result(
    user_a_id: str,
    user_b_id: str,
    safe_result: dict,
    raw_result: dict,
) -> None:
    """Save a computed match result to the cache.

    safe_result: The DTO-sanitized result (what the frontend sees).
    raw_result:  The full compute_match_v2 output (backend-only archive).
    """
    client = _get_client()
    data = safe_result.get("data", safe_result)

    client.table("matches").upsert({
        "user_a_id": user_a_id,
        "user_b_id": user_b_id,
        "harmony_score": data.get("harmony_score"),
        "tension_level": data.get("tension_level"),
        "badges": data.get("badges", []),
        "tracks": data.get("tracks", {}),
        "llm_insight_report": data.get("ai_insight_report", ""),
        "raw_result": raw_result,
    }).execute()
