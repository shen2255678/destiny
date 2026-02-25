# -*- coding: utf-8 -*-
"""
DESTINY — API Presenter (DTO Sanitization Layer)
Data sanitization & semantic translation for safe frontend delivery.

Core principle: NEVER expose raw astrology/bazi/zwds data to the frontend.
Only return UI-friendly labels, scores (as integers), and LLM-generated text.

Two public functions:
  format_safe_match_response(raw_match_data, llm_report_text)
      → Safe JSON for match results
  format_safe_onboard_response(psychology_profile, llm_natal_report)
      → Safe JSON for onboarding results
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# ── Sensitive keyword blacklist ──────────────────────────────────────────────
# If any of these strings appear as keys in the response JSON,
# the data is considered "leaked" and must be stripped.
SENSITIVE_KEYS = frozenset({
    "bazi", "bazi_chart", "bazi_relation", "bazi_day_branch_relation",
    "bazi_element", "bazi_four_pillars", "bazi_day_master",
    "zwds", "zwds_chart", "zwds_result",
    "western_chart", "chart",
    "aspects", "natal_aspects",
    "degrees", "planet_degrees",
    "ten_gods", "palaces",
    "day_master", "day_master_element",
    "sun_sign", "moon_sign", "venus_sign", "mars_sign", "saturn_sign",
    "mercury_sign", "jupiter_sign", "pluto_sign", "chiron_sign",
    "ascendant_sign", "juno_sign",
    "house4_sign", "house8_sign", "house12_sign",
    "north_node_sign", "south_node_sign",
    "house7_sign",
    "sm_tags", "karmic_tags",
    "element_profile",
    "useful_god_complement",
    "spiciness_level",
    "defense_mechanisms", "layered_analysis",
    "power",  # RPV internals
    "lust_score",  # raw axis score
    "soul_score",  # raw axis score (use harmony_score instead)
})

# Sensitive substrings — if found in string VALUES, the data is leaked
SENSITIVE_VALUE_PATTERNS = [
    "偏印", "正印", "食神", "傷官", "比肩", "劫財", "正財", "偏財", "正官", "七殺",
    "貪狼", "紫微", "天機", "太陽", "武曲", "天同", "廉貞", "天府", "太陰",
    "巨門", "天相", "天梁", "破軍", "七殺",
    "化祿", "化權", "化科", "化忌",
    "_degree",
]


def _karmic_tension_to_level(tension: float) -> int:
    """Convert karmic_tension (0-100) to tension_level (1-5).

    Mapping:
      0-19  → 1 (low tension)
      20-39 → 2
      40-59 → 3
      60-79 → 4
      80-100→ 5 (extreme tension)
    """
    return max(1, min(5, int(tension / 20) + 1))


def _sanitize_deep(obj: Any) -> Any:
    """Recursively strip any sensitive keys from nested dicts/lists."""
    if isinstance(obj, dict):
        return {
            k: _sanitize_deep(v)
            for k, v in obj.items()
            if k not in SENSITIVE_KEYS
        }
    if isinstance(obj, list):
        return [_sanitize_deep(item) for item in obj]
    return obj


def format_safe_match_response(
    raw_match_data: dict,
    llm_report_text: str = "",
) -> dict:
    """Format a safe, frontend-ready match response (DTO).

    Extracts only UI-safe data from compute_match_v2() output:
      - harmony_score (integer)
      - tension_level (1-5 star rating)
      - badges (resonance badge strings)
      - tracks (integer scores for 4 tracks)
      - psychological_needs (if available)
      - ai_insight_report (LLM-generated text)

    All raw astrology/bazi/zwds data is stripped.
    """
    # 1. Extract safe track scores (convert to integers)
    raw_tracks = raw_match_data.get("tracks", {})
    safe_tracks = {}
    for k, v in raw_tracks.items():
        if isinstance(v, (int, float)):
            safe_tracks[k] = int(round(v))

    # 2. Convert karmic_tension to 1-5 level
    karmic_tension = raw_match_data.get("karmic_tension", 0)
    tension_level = _karmic_tension_to_level(karmic_tension)

    # 3. Extract safe badges
    badges = raw_match_data.get("resonance_badges", [])

    # 4. Harmony score (integer)
    harmony = int(round(raw_match_data.get("harmony_score", 0)))

    # 5. Primary track & quadrant (UI labels)
    primary_track = raw_match_data.get("primary_track", "")
    quadrant = raw_match_data.get("quadrant", "")
    labels = raw_match_data.get("labels", [])

    # 6. Psychological tags (safe — these are Chinese descriptive strings)
    psych_tags = raw_match_data.get("psychological_tags", [])

    # 7. High voltage flag (boolean, safe for UI)
    high_voltage = raw_match_data.get("high_voltage", False)

    return {
        "status": "success",
        "data": {
            "harmony_score": harmony,
            "tension_level": tension_level,
            "badges": badges,
            "tracks": safe_tracks,
            "primary_track": primary_track,
            "quadrant": quadrant,
            "labels": labels,
            "high_voltage": high_voltage,
            "psychological_tags": psych_tags,
            "ai_insight_report": llm_report_text,
        }
    }


def format_safe_onboard_response(
    psychology_profile: dict,
    llm_natal_report: str = "",
) -> dict:
    """Format a safe onboarding response (DTO).

    Only returns psychology profile labels and LLM-generated text.
    No raw chart data, no planet degrees, no ten gods.
    """
    return {
        "status": "success",
        "data": {
            "relationship_dynamic": psychology_profile.get("relationship_dynamic", "unknown"),
            "psychological_needs": psychology_profile.get("psychological_needs", []),
            "favorable_elements": psychology_profile.get("favorable_elements", []),
            "attachment_style": psychology_profile.get("attachment_style", "unknown"),
            "ai_natal_report": llm_natal_report,
        }
    }


def assert_no_sensitive_data(response: dict) -> bool:
    """Security audit helper — assert response contains no sensitive data.

    Returns True if clean. Raises AssertionError with details if leaked.
    Used in test_api_presenter.py.
    """
    response_str = json.dumps(response, ensure_ascii=False)

    # Check for sensitive keys
    if isinstance(response, dict):
        _check_keys_recursive(response)

    # Check for sensitive value patterns
    for pattern in SENSITIVE_VALUE_PATTERNS:
        if pattern in response_str:
            raise AssertionError(
                f"SECURITY LEAK: sensitive pattern '{pattern}' found in response"
            )

    return True


def _check_keys_recursive(obj: Any, path: str = "") -> None:
    """Recursively check all keys in nested dict for sensitive entries."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if k in SENSITIVE_KEYS:
                raise AssertionError(
                    f"SECURITY LEAK: sensitive key '{k}' found at path '{current_path}'"
                )
            _check_keys_recursive(v, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_keys_recursive(item, f"{path}[{i}]")
