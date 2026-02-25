# -*- coding: utf-8 -*-
"""Tests for db_client helper functions — no Supabase required (mocked)."""
import pytest
from unittest.mock import patch


def test_returns_cached_when_available():
    """Cache hit: return DB profile, never call extract_ideal_partner_profile."""
    cached = {"psychological_needs": ["安全感"], "relationship_dynamic": "stable"}
    with patch("db_client.get_psychology_profile", return_value=cached) as mock_get, \
         patch("db_client.upsert_psychology_profile") as mock_upsert:
        from db_client import get_or_compute_psychology_profile
        result = get_or_compute_psychology_profile("user-123", {})
        mock_get.assert_called_once_with("user-123")
        mock_upsert.assert_not_called()
        assert result == cached


def test_computes_and_saves_on_cache_miss():
    """Cache miss: call extract_ideal_partner_profile, save result, return it."""
    fake_profile = {"psychological_needs": ["自由"], "relationship_dynamic": "high_voltage"}
    natal = {
        "western_chart": {"sun_sign": "aries"},
        "bazi_chart": {"day_master_element": "fire"},
        "zwds_chart": {},
    }
    with patch("db_client.get_psychology_profile", return_value=None), \
         patch("db_client.upsert_psychology_profile") as mock_upsert, \
         patch("ideal_avatar.extract_ideal_partner_profile", return_value=fake_profile) as mock_extract:
        from db_client import get_or_compute_psychology_profile
        result = get_or_compute_psychology_profile("user-456", natal)
        mock_extract.assert_called_once_with(
            natal["western_chart"],
            natal["bazi_chart"],
            natal["zwds_chart"],
        )
        mock_upsert.assert_called_once_with("user-456", fake_profile)
        assert result == fake_profile


def test_returns_empty_dict_on_exception():
    """Any exception (e.g. Supabase down) → return {} without crashing."""
    with patch("db_client.get_psychology_profile", side_effect=RuntimeError("supabase down")):
        from db_client import get_or_compute_psychology_profile
        result = get_or_compute_psychology_profile("user-789", {})
        assert result == {}
