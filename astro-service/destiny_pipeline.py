# -*- coding: utf-8 -*-
"""
destiny_pipeline.py — DestinyPipeline class

One-stop pipeline: BirthInput → charts → match → profiles → prompts → enriched DTO.
Collapses the 5 HTTP round-trips that lounge/run_ideal_match_prompt.py previously made.

Usage (single person):
    pipeline = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
    pipeline.compute_charts().extract_profiles().build_prompts()
    dto = pipeline.to_enriched_dto()

Usage (synastry):
    pipeline = DestinyPipeline(
        BirthInput("1996-11-05", "02:00", "F"),
        BirthInput("1996-12-10", None, "M"),
    )
    pipeline.compute_charts().compute_match().extract_profiles().build_prompts()
    dto = pipeline.to_enriched_dto()
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from chart import calculate_chart
from zwds import compute_zwds_chart
from matching import compute_match_v2
from ideal_avatar import extract_ideal_partner_profile
from prompt_manager import (
    get_ideal_match_prompt,
    get_simple_report_prompt,
    get_profile_prompt,
    build_synastry_report_prompt,
    _translate_psych_tags,
    _PSYCH_TAG_ZH,
)


# ── Tier inference ─────────────────────────────────────────────────────────────

def _infer_tier(birth_time: Optional[str]) -> int:
    """
    Tier 1: exact time "HH:MM"
    Tier 2: fuzzy slot "morning" | "afternoon" | "evening"
    Tier 3: None | "unknown"
    """
    if birth_time and ":" in birth_time:
        return 1
    if birth_time in ("morning", "afternoon", "evening"):
        return 2
    return 3


def _tier_missing_fields(tier: int) -> list[str]:
    """Return list of fields unavailable at this tier."""
    if tier == 1:
        return []
    if tier == 2:
        return ["moon", "ascendant", "houses", "hour_pillar"]
    return ["moon", "ascendant", "houses", "zwds", "hour_pillar"]


# ── BirthInput ─────────────────────────────────────────────────────────────────

@dataclass
class BirthInput:
    birth_date: str           # "1996-11-05"
    birth_time: Optional[str] = None   # "14:30" | "morning" | None
    gender: str = "M"         # "M" | "F"
    lat: float = 25.033       # default: Taipei
    lng: float = 121.565

    @property
    def tier(self) -> int:
        return _infer_tier(self.birth_time)

    @property
    def birth_time_exact(self) -> Optional[str]:
        """Returns exact HH:MM only if Tier 1, else None."""
        return self.birth_time if self.tier == 1 else None

    @property
    def birth_time_slot(self) -> Optional[str]:
        """Returns slot string ("precise"/"morning"/…) for calculate_chart."""
        if self.tier == 1:
            return "precise"
        return self.birth_time  # "morning" | "afternoon" | "evening" | None

    def parsed_date(self) -> tuple[int, int, int]:
        dt = datetime.strptime(self.birth_date, "%Y-%m-%d")
        return dt.year, dt.month, dt.day


# ── DestinyPipeline ────────────────────────────────────────────────────────────

class DestinyPipeline:
    """
    One-stop pipeline from birth data to prompt-ready enriched DTO.

    Chain pattern:
        pipeline.compute_charts().compute_match().extract_profiles().build_prompts()
    """

    def __init__(
        self,
        person_a: BirthInput,
        person_b: Optional[BirthInput] = None,
    ) -> None:
        self._a = person_a
        self._b = person_b
        self._mode = "single" if person_b is None else "synastry"

        # Internal state — populated by each step
        self._chart_a: dict = {}
        self._chart_b: dict = {}
        self._zwds_a: Optional[dict] = None
        self._zwds_b: Optional[dict] = None
        self._match: dict = {}
        self._avatar_a: dict = {}
        self._avatar_b: dict = {}
        self._prompts: dict = {}

    # ── Step 1: Compute Charts ──────────────────────────────────────────────

    def compute_charts(self) -> "DestinyPipeline":
        """Calculate western + BaZi chart for each person, plus ZWDS for Tier 1."""
        self._chart_a = self._calc_chart(self._a)
        self._zwds_a = self._calc_zwds(self._a)

        if self._b is not None:
            self._chart_b = self._calc_chart(self._b)
            self._zwds_b = self._calc_zwds(self._b)

        return self

    def _calc_chart(self, p: BirthInput) -> dict:
        chart = calculate_chart(
            birth_date=p.birth_date,
            birth_time=p.birth_time_slot,
            birth_time_exact=p.birth_time_exact,
            lat=p.lat,
            lng=p.lng,
            data_tier=p.tier,
        )
        return chart

    def _calc_zwds(self, p: BirthInput) -> Optional[dict]:
        if p.tier != 1 or not p.birth_time_exact:
            return None
        year, month, day = p.parsed_date()
        try:
            return compute_zwds_chart(year, month, day, p.birth_time_exact, p.gender)
        except Exception:
            return None

    # ── Step 2: Compute Match (synastry only) ───────────────────────────────

    def compute_match(self) -> "DestinyPipeline":
        """Compute v2 synastry match. No-op in single-person mode."""
        if self._mode == "single":
            return self

        flat_a = self._flat_for_match(self._a, self._chart_a)
        flat_b = self._flat_for_match(self._b, self._chart_b)
        self._match = compute_match_v2(flat_a, flat_b)
        return self

    def _flat_for_match(self, person: BirthInput, chart: dict) -> dict:
        """Flatten chart + BaZi + person meta into the dict compute_match_v2 expects."""
        bazi = chart.get("bazi") or {}
        year, month, day = person.parsed_date()

        flat: dict = {
            "data_tier": person.tier,
            "gender": person.gender,
            "birth_year": year,
            "birth_month": month,
            "birth_day": day,
            # birth_time for ZWDS eligibility check (must be HH:MM)
            "birth_time": person.birth_time_exact or "",
        }

        # Western signs + degrees
        _SIGN_FIELDS = [
            "sun_sign", "moon_sign", "mercury_sign", "venus_sign", "mars_sign",
            "jupiter_sign", "saturn_sign", "uranus_sign", "neptune_sign",
            "pluto_sign", "chiron_sign", "juno_sign",
            "north_node_sign", "south_node_sign",
            "ascendant_sign", "house4_sign", "house7_sign", "house8_sign", "house12_sign",
            "vertex_sign", "lilith_sign",
        ]
        _DEGREE_FIELDS = [
            "sun_degree", "moon_degree", "venus_degree", "mars_degree",
            "ascendant_degree", "north_node_degree", "south_node_degree",
            "house7_degree", "vertex_degree", "lilith_degree", "chiron_degree",
        ]
        for k in _SIGN_FIELDS + _DEGREE_FIELDS:
            v = chart.get(k)
            if v is not None:
                flat[k] = v

        # Retrograde flags
        for k in ("mars_rx", "venus_rx", "mercury_rx"):
            v = chart.get(k)
            if v is not None:
                flat[k] = v

        # BaZi
        flat["bazi_element"] = bazi.get("day_master_element")
        flat["bazi_month_branch"] = bazi.get("bazi_month_branch")
        flat["bazi_day_branch"] = bazi.get("bazi_day_branch")
        flat["day_master"] = bazi.get("day_master")

        # Psychology
        flat["attachment_style"] = chart.get("attachment_style")
        flat["emotional_capacity"] = chart.get("emotional_capacity")
        flat["natal_aspects"] = chart.get("natal_aspects")

        # Remove None values
        return {k: v for k, v in flat.items() if v is not None}

    # ── Step 3: Extract Profiles ────────────────────────────────────────────

    def extract_profiles(self) -> "DestinyPipeline":
        """Extract ideal partner profile for each person."""
        self._avatar_a = self._extract_avatar(self._chart_a, self._zwds_a)
        if self._b is not None:
            self._avatar_b = self._extract_avatar(self._chart_b, self._zwds_b)
        return self

    def _extract_avatar(self, chart: dict, zwds: Optional[dict]) -> dict:
        bazi = chart.get("bazi") or {}
        try:
            return extract_ideal_partner_profile(
                western_chart=chart,
                bazi_chart=bazi,
                zwds_chart=zwds or {},
                psychology_data={},
            )
        except Exception:
            return {}

    # ── Step 4: Build Prompts ───────────────────────────────────────────────

    def build_prompts(self) -> "DestinyPipeline":
        """Build all relevant prompts (no LLM call)."""
        prompts: dict = {}

        # Merge zwds into chart for prompt functions
        chart_a_with_zwds = {**self._chart_a}
        if self._zwds_a:
            chart_a_with_zwds["zwds"] = self._zwds_a

        prompts["ideal_a"] = get_ideal_match_prompt(chart_a_with_zwds, self._avatar_a or None)
        prompts["profile_a"] = get_profile_prompt(
            chart_a_with_zwds,
            rpv_data={},
            attachment_style=chart_a_with_zwds.get("attachment_style", "secure"),
        )

        if self._b is not None:
            chart_b_with_zwds = {**self._chart_b}
            if self._zwds_b:
                chart_b_with_zwds["zwds"] = self._zwds_b

            prompts["ideal_b"] = get_ideal_match_prompt(chart_b_with_zwds, self._avatar_b or None)
            prompts["profile_b"] = get_profile_prompt(
                chart_b_with_zwds,
                rpv_data={},
                attachment_style=chart_b_with_zwds.get("attachment_style", "secure"),
            )

            if self._match:
                prompts["synastry"] = build_synastry_report_prompt(
                    self._match,
                    user_a_profile=chart_a_with_zwds,
                    user_b_profile=chart_b_with_zwds,
                )

        self._prompts = prompts
        return self

    # ── Output: Enriched DTO ────────────────────────────────────────────────

    def to_enriched_dto(self) -> dict:
        """
        Safe DTO for API / frontend.

        Excludes: *_degree fields, natal_aspects, raw chart dicts.
        Includes: sign names, Chinese tags, scores, prompts.
        """
        dto: dict = {
            "mode": self._mode,
            "data_quality": self._build_data_quality(),
        }

        if self._mode == "synastry" and self._match:
            dto["scores"] = self._build_scores()
            dto["tags_zh"] = self._build_tags_zh()

        dto["person_a_summary"] = self._person_summary(
            self._a, self._chart_a, self._zwds_a, self._avatar_a
        )

        if self._b is not None:
            dto["person_b_summary"] = self._person_summary(
                self._b, self._chart_b, self._zwds_b, self._avatar_b
            )

        if self._prompts:
            dto["prompts"] = self._prompts

        return dto

    def _build_data_quality(self) -> dict:
        dq: dict = {
            "person_a": {
                "tier": self._a.tier,
                "missing": _tier_missing_fields(self._a.tier),
            }
        }
        if self._b is not None:
            dq["person_b"] = {
                "tier": self._b.tier,
                "missing": _tier_missing_fields(self._b.tier),
            }
        return dq

    def _build_scores(self) -> dict:
        m = self._match
        return {
            "harmony": round(m.get("harmony_score", 0), 1),
            "lust": round(m.get("lust_score", 0), 1),
            "soul": round(m.get("soul_score", 0), 1),
            "karmic_tension": round(m.get("karmic_tension", 0), 1),
            "tracks": m.get("tracks", {}),
            "primary_track": m.get("primary_track"),
            "quadrant": m.get("quadrant"),
            "spiciness_level": m.get("spiciness_level"),
            "high_voltage": m.get("high_voltage", False),
        }

    def _build_tags_zh(self) -> dict:
        m = self._match
        psych_tags_a = m.get("psychological_tags", [])

        # Translate element profiles to Chinese
        ep_a = m.get("element_profile_a") or self._chart_a.get("element_profile") or {}
        ep_b = m.get("element_profile_b") or self._chart_b.get("element_profile") or {}

        return {
            "resonance_badges": m.get("resonance_badges", []),
            "labels": m.get("labels", []),
            "psychological": [_PSYCH_TAG_ZH.get(t, t) for t in psych_tags_a if t],
            "element_a": _element_zh_summary(ep_a),
            "element_b": _element_zh_summary(ep_b),
            "power_dynamic": _power_zh(m.get("power", {})),
        }

    def _person_summary(
        self,
        person: BirthInput,
        chart: dict,
        zwds: Optional[dict],
        avatar: dict,
    ) -> dict:
        """Build person summary (no raw degrees, no natal_aspects)."""
        bazi = chart.get("bazi") or {}
        fp = bazi.get("four_pillars") or {}

        def _pstr(p) -> str:
            if isinstance(p, dict):
                return p.get("full", p.get("stem", "") + p.get("branch", ""))
            return str(p or "")

        pillars_str = " ".join(
            _pstr(fp.get(k)) for k in ("year", "month", "day", "hour") if fp.get(k)
        )

        summary: dict = {
            # Western signs (public info, safe to include)
            "sun": chart.get("sun_sign"),
            "moon": chart.get("moon_sign"),
            "ascendant": chart.get("ascendant_sign"),
            "venus": chart.get("venus_sign"),
            "mars": chart.get("mars_sign"),
            "jupiter": chart.get("jupiter_sign"),
            "saturn": chart.get("saturn_sign"),
            "juno": chart.get("juno_sign"),
            "descendant": chart.get("house7_sign"),
            # BaZi summary (no raw digits)
            "day_master": bazi.get("day_master"),
            "pillars": pillars_str or None,
            # ZWDS spouse palace (Tier 1 only)
            "zwds_spouse": _zwds_spouse_stars(zwds),
            "zwds_ming": _zwds_ming_stars(zwds),
            # Psychology tags (Chinese)
            "sm_tags_zh": [_PSYCH_TAG_ZH.get(t, t) for t in chart.get("sm_tags", []) if t],
            "karmic_tags_zh": chart.get("karmic_tags", []),
            "element_profile": chart.get("element_profile"),
        }

        if avatar:
            summary["ideal_partner_profile"] = {
                "target_signs": avatar.get("target_western_signs", []),
                "psychological_needs": avatar.get("psychological_needs", []),
                "relationship_dynamic": avatar.get("relationship_dynamic"),
                "venus_mars_tags": avatar.get("venus_mars_tags", []),
            }

        # Remove None values
        return {k: v for k, v in summary.items() if v is not None}

    # ── Output: Raw ─────────────────────────────────────────────────────────

    def to_raw(self) -> dict:
        """Full internal state — CLI / debug use only."""
        return {
            "mode": self._mode,
            "chart_a": self._chart_a,
            "chart_b": self._chart_b,
            "zwds_a": self._zwds_a,
            "zwds_b": self._zwds_b,
            "match": self._match,
            "avatar_a": self._avatar_a,
            "avatar_b": self._avatar_b,
            "prompts": self._prompts,
        }

    # ── Output: Files ───────────────────────────────────────────────────────

    def to_json_file(self, path: str) -> None:
        """Write enriched DTO to UTF-8 JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_enriched_dto(), f, ensure_ascii=False, indent=2)

    def to_prompt_file(self, prompt_key: str, path: str) -> None:
        """Write a specific prompt to UTF-8 text file."""
        prompt = self._prompts.get(prompt_key)
        if prompt is None:
            raise KeyError(f"Prompt key {prompt_key!r} not found. Available: {list(self._prompts)}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _element_zh_summary(ep: dict) -> str:
    """Convert element_profile dict to short Chinese summary."""
    if not ep:
        return "（無資料）"
    dominant = ep.get("dominant", [])
    deficiency = ep.get("deficiency", [])
    if not dominant and not deficiency:
        return "四元素均衡"
    parts = []
    if dominant:
        parts.append("過剩: " + "、".join(dominant))
    if deficiency:
        parts.append("缺: " + "、".join(deficiency))
    return "；".join(parts)


def _power_zh(power: dict) -> str:
    """Convert power dict to Chinese summary string."""
    if not power:
        return "（無資料）"
    viewer = power.get("viewer_role", "")
    target = power.get("target_role", "")
    rpv = power.get("rpv", 0)
    if not viewer and not target:
        return f"RPV 均衡 ({rpv})"
    return f"{viewer} × {target}（RPV {rpv}）"


def _zwds_spouse_stars(zwds: Optional[dict]) -> Optional[str]:
    if not zwds:
        return None
    palaces = zwds.get("palaces") or {}
    spouse = palaces.get("spouse") or {}
    stars = spouse.get("main_stars", [])
    return "、".join(stars) if stars else None


def _zwds_ming_stars(zwds: Optional[dict]) -> Optional[str]:
    if not zwds:
        return None
    palaces = zwds.get("palaces") or {}
    ming = palaces.get("life") or {}
    stars = ming.get("main_stars", [])
    return "、".join(stars) if stars else None
