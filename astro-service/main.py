# -*- coding: utf-8 -*-
"""
DESTINY — Astrology Microservice
FastAPI server for natal chart calculation.

Endpoints:
  GET  /health           → health check
  POST /calculate-chart  → compute zodiac signs from birth data
"""

from __future__ import annotations

import os
import json
from typing import Optional

import pathlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from chart import calculate_chart
from bazi import analyze_element_relation
from matching import compute_match_score, compute_match_v2
from zwds import compute_zwds_chart
from prompt_manager import get_match_report_prompt, get_simple_report_prompt, get_profile_prompt, get_ideal_match_prompt, build_synastry_report_prompt
from api_presenter import format_safe_match_response, format_safe_onboard_response
from ideal_avatar import extract_ideal_partner_profile
from anthropic import Anthropic
from google import genai as google_genai

anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

# Ensure Chinese characters are returned as-is (not escaped as \uXXXX)
class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        import json
        return json.dumps(content, ensure_ascii=False).encode("utf-8")

app = FastAPI(
    title="DESTINY Astro Service",
    version="0.3.0",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartRequest(BaseModel):
    birth_date: str                              # "1995-06-15"
    birth_time: Optional[str] = None             # "precise" | "morning" | "afternoon" | "evening" | "unknown"
    birth_time_exact: Optional[str] = None       # "14:30"
    lat: float = 25.033
    lng: float = 121.565
    data_tier: int = 3
    gender: str = "M"                            # "M" or "F" — needed for ZWDS computation
    birth_year: Optional[int] = None             # for ZWDS (if not parseable from birth_date)
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sandbox")
def serve_sandbox():
    """Serve sandbox.html at http://localhost:8001/sandbox (same-origin, no CORS needed)."""
    html_path = pathlib.Path(__file__).parent / "sandbox.html"
    return FileResponse(str(html_path), media_type="text/html")


@app.post("/calculate-chart")
def calc_chart(req: ChartRequest):
    try:
        result = calculate_chart(
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            birth_time_exact=req.birth_time_exact,
            lat=req.lat,
            lng=req.lng,
            data_tier=req.data_tier,
        )

        # For Tier 1, enrich emotional_capacity with ZWDS rules (4-6)
        if req.data_tier == 1 and req.birth_time_exact:
            try:
                from datetime import datetime as _dt
                dt = _dt.strptime(req.birth_date, "%Y-%m-%d")
                year = req.birth_year or dt.year
                month = req.birth_month or dt.month
                day = req.birth_day or dt.day
                zwds = compute_zwds_chart(year, month, day, req.birth_time_exact, req.gender)
                if zwds:
                    from chart import compute_emotional_capacity
                    result["emotional_capacity"] = compute_emotional_capacity(result, zwds)
            except Exception:
                pass  # never block the response for ZWDS failure

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RelationRequest(BaseModel):
    element_a: str  # "wood" | "fire" | "earth" | "metal" | "water"
    element_b: str


@app.post("/analyze-relation")
def relation(req: RelationRequest):
    """Analyze Five-Element relationship between two people's Day Masters."""
    valid = {"wood", "fire", "earth", "metal", "water"}
    if req.element_a not in valid or req.element_b not in valid:
        raise HTTPException(status_code=400, detail="Invalid element. Must be: wood/fire/earth/metal/water")
    return analyze_element_relation(req.element_a, req.element_b)


class MatchRequest(BaseModel):
    user_a: dict
    user_b: dict


@app.post("/compute-match")
def compute_match(req: MatchRequest):
    """Compute Phase G v2 match score between two user profiles.

    user_a / user_b should contain flat profile fields:
      Core:    data_tier, sun_sign, moon_sign, venus_sign, mars_sign, saturn_sign,
               ascendant_sign, bazi_element, bazi_month_branch,
               rpv_conflict, rpv_power, rpv_energy
      Phase G: mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign,
               house4_sign, house8_sign, attachment_style, emotional_capacity
      ZWDS (Tier 1 only — required for ZWDS synastry to fire):
               birth_year, birth_month, birth_day,
               birth_time (HH:MM format, e.g. "14:30"), gender ("M" or "F")

    Note: birth_time in this dict is the exact "HH:MM" string (not the slot type
    "precise"/"morning" used by /calculate-chart). Missing ZWDS fields degrade
    gracefully to zwds=null and spiciness_level="STABLE".

    Returns: lust_score, soul_score, power {rpv, frame_break, viewer_role, target_role},
             tracks {friend, passion, partner, soul}, primary_track, quadrant, labels
    """
    try:
        result = compute_match_v2(req.user_a, req.user_b)

        # Echo key chart fields for both persons into the result so they are
        # stored in report_json and available for prompt preview / LLM context.
        _ECHO_KEYS = [
            "sun_sign", "moon_sign", "venus_sign", "mars_sign",
            "mercury_sign", "jupiter_sign", "saturn_sign", "ascendant_sign",
            "chiron_sign", "juno_sign",
            "bazi_element", "bazi_month_branch", "bazi_day_branch",
            "attachment_style", "data_tier", "gender",
        ]
        result["user_a_chart"] = {k: v for k in _ECHO_KEYS if (v := req.user_a.get(k)) is not None}
        result["user_b_chart"] = {k: v for k in _ECHO_KEYS if (v := req.user_b.get(k)) is not None}

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ZwdsChartRequest(BaseModel):
    birth_year:  int
    birth_month: int
    birth_day:   int
    birth_time:  Optional[str] = None
    gender:      str = "M"


@app.post("/compute-zwds-chart")
async def get_zwds_chart(req: ZwdsChartRequest):
    """Compute ZiWei DouShu 12-palace chart (Tier 1 only).
    Returns null chart if birth_time is not provided.
    """
    chart = compute_zwds_chart(
        req.birth_year, req.birth_month, req.birth_day, req.birth_time, req.gender
    )
    return {"chart": chart}


# ── Algorithm Validation Sandbox Endpoints ─────────────────────────────────


def call_llm(
    prompt: str,
    provider: str = "anthropic",
    max_tokens: int = 600,
    api_key: str = "",
    gemini_model: str = "",
) -> str:
    """Call Claude (Anthropic) or Gemini based on provider.

    api_key: if provided, overrides the server environment variable.
    gemini_model: Gemini model name; defaults to gemini-2.0-flash.
    Raises HTTPException 400 if no API key is available.
    Returns raw text from the model.
    """
    if provider == "gemini":
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY not set")
        model_name = gemini_model or "gemini-2.0-flash"
        client = google_genai.Client(api_key=key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    else:  # anthropic (default)
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")
        client = Anthropic(api_key=key) if api_key else anthropic_client
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text




class ArchetypeRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    mode: str = "auto"           # "auto" | "hunt" | "nest" | "abyss" | "friend"
    language: str = "zh-TW"
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-archetype")
def generate_archetype(req: ArchetypeRequest):
    """Generate DESTINY archetype report (5-section) via Claude or Gemini.

    Returns: {archetype_tags, resonance, shadow, reality_check, evolution, core}
    Mode auto-selects track template from primary_track + high_voltage.
    """
    prompt, effective_mode = get_match_report_prompt(
        req.match_data, mode=req.mode,
        person_a=req.person_a_name, person_b=req.person_b_name,
    )
    raw = ""
    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=900, api_key=req.api_key, gemini_model=req.gemini_model)
        result = json.loads(raw)
        result["effective_mode"] = effective_mode
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProfileCardRequest(BaseModel):
    chart_data: dict
    rpv_data: dict
    attachment_style: str = "secure"
    person_name: str = "User"
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-profile-card")
def generate_profile_card(req: ProfileCardRequest):
    """Generate a DESTINY soul profile card via Claude or Gemini.

    Returns: {headline, shadow_trait, avoid_types, evolution, core}
    """
    prompt = get_profile_prompt(req.chart_data, req.rpv_data, req.attachment_style)

    raw = ""
    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=600, api_key=req.api_key, gemini_model=req.gemini_model)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PreviewPromptRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    mode: str = "auto"


@app.post("/preview-prompt")
def preview_prompt(req: PreviewPromptRequest):
    """Return the prompt that would be sent to LLM — no LLM call.

    Used by the MVP developer panel so users can inspect and tweak
    the prompt before triggering an actual LLM call.
    Returns: { prompt: str, effective_mode: str }
    """
    from prompt_manager import _pick_mode
    prompt = get_simple_report_prompt(
        req.match_data, mode=req.mode,
        person_a=req.person_a_name, person_b=req.person_b_name,
    )
    effective_mode = _pick_mode(req.match_data, req.mode)
    return {"prompt": prompt, "effective_mode": effective_mode}


class MatchReportRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    mode: str = "auto"           # "auto" | "hunt" | "nest" | "abyss" | "friend"
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-match-report")
def generate_match_report(req: MatchReportRequest):
    """Generate a DESTINY relationship report via Claude or Gemini.

    Returns: {title, one_liner, sparks, landmines, advice, core}
    Mode auto-selects track template from primary_track + high_voltage.
    """
    prompt = get_simple_report_prompt(
        req.match_data, mode=req.mode,
        person_a=req.person_a_name, person_b=req.person_b_name,
    )

    raw = ""
    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=700, api_key=req.api_key, gemini_model=req.gemini_model)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IdealMatchRequest(BaseModel):
    chart_data: dict
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-ideal-match")
def generate_ideal_match(req: IdealMatchRequest):
    """Generate an ideal partner profile based on a single person's natal chart.

    Returns: {antidote, reality_anchors, core_need}
    """
    prompt = get_ideal_match_prompt(req.chart_data)

    raw = ""
    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=600, api_key=req.api_key, gemini_model=req.gemini_model)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Sprint 4/8: Ideal Partner Profile Extraction ─────────────────────────────

@app.post("/extract-ideal-profile")
async def extract_ideal_profile(req: dict):
    """Extract ideal partner trait tags from a single person's natal chart.

    Expects JSON body with keys: western_chart, bazi_chart, zwds_chart,
    psychology_data (optional).

    Returns: {target_western_signs, target_bazi_elements, relationship_dynamic,
              psychological_needs, zwds_partner_tags, karmic_match_required,
              attachment_style, psychological_conflict, venus_mars_tags,
              favorable_elements}
    """
    from ideal_avatar import extract_ideal_partner_profile
    return extract_ideal_partner_profile(
        req.get("western_chart", {}),
        req.get("bazi_chart", {}),
        req.get("zwds_chart", {}),
        req.get("psychology_data", {}),
    )


# ── Production API: Onboarding + Match Compute (with DTO & Caching) ──────────

class OnboardRequest(BaseModel):
    user_id: str
    birth_date: str                              # "1995-06-15"
    birth_time: Optional[str] = None             # "precise" | "morning" | "afternoon" | "unknown"
    birth_time_exact: Optional[str] = None       # "14:30"
    lat: float = 25.033
    lng: float = 121.565
    data_tier: int = 3
    gender: str = "M"
    generate_report: bool = False                # whether to call LLM for natal report
    provider: str = "anthropic"
    api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


@app.post("/api/users/onboard")
async def onboard_user(req: OnboardRequest):
    """Compute natal chart & psychology profile, cache to Supabase, return safe DTO.

    Pipeline:
      1. chart.py → western chart
      2. bazi.py → BaZi four pillars
      3. zwds.py → ZWDS chart (Tier 1 only)
      4. ideal_avatar.py → psychology tags
      5. Write raw data → user_natal_data (black box)
      6. Write psychology → user_psychology_profiles
      7. (Optional) LLM → natal report
      8. Return safe DTO (no raw chart data)
    """
    try:
        # 1. Calculate western chart
        western = calculate_chart(
            birth_date=req.birth_date,
            birth_time=req.birth_time,
            birth_time_exact=req.birth_time_exact,
            lat=req.lat, lng=req.lng,
            data_tier=req.data_tier,
        )

        # 2. BaZi is embedded in the chart result
        bazi_data = western.get("bazi", {})

        # 3. ZWDS chart (Tier 1 only)
        zwds_data = {}
        if req.data_tier == 1 and req.birth_time_exact:
            try:
                from datetime import datetime as _dt
                dt = _dt.strptime(req.birth_date, "%Y-%m-%d")
                zwds_data = compute_zwds_chart(
                    dt.year, dt.month, dt.day,
                    req.birth_time_exact, req.gender,
                ) or {}
            except Exception:
                zwds_data = {}

        # 4. Extract psychology profile
        psychology = {}
        try:
            from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile
            psychology = {
                "sm_tags": western.get("sm_tags", []),
                "karmic_tags": western.get("karmic_tags", []),
                "element_profile": western.get("element_profile", {}),
            }
        except Exception:
            pass

        profile = extract_ideal_partner_profile(
            western_chart=western,
            bazi_chart=bazi_data,
            zwds_chart=zwds_data,
            psychology_data=psychology,
        )

        # 5 & 6. Write to Supabase (graceful failure)
        try:
            import db_client
            db_client.upsert_natal_data(
                user_id=req.user_id,
                western_chart=western,
                bazi_chart=bazi_data,
                zwds_chart=zwds_data,
            )
            db_client.upsert_psychology_profile(
                user_id=req.user_id,
                profile=profile,
            )
        except Exception as db_err:
            # Log but don't block — Supabase may not be configured
            import traceback
            traceback.print_exc()

        # 7. Optional LLM natal report
        llm_report = ""
        if req.generate_report:
            try:
                prompt = get_profile_prompt(
                    chart_data=western,
                    rpv_data={},
                    attachment_style=profile.get("attachment_style", "secure"),
                )
                raw = call_llm(prompt, provider=req.provider, max_tokens=600,
                               api_key=req.api_key, gemini_model=req.gemini_model)
                llm_report = raw
                # Update report in DB
                try:
                    import db_client as _dbc
                    _dbc.upsert_psychology_profile(req.user_id, {"llm_natal_report": raw})
                except Exception:
                    pass
            except Exception:
                pass

        # 8. Return safe DTO
        return format_safe_onboard_response(profile, llm_report)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MatchComputeRequest(BaseModel):
    user_a_id: str
    user_b_id: str
    force_recompute: bool = False                # bypass cache
    generate_report: bool = True                 # whether to call LLM
    provider: str = "anthropic"
    api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


@app.post("/api/matches/compute")
async def compute_match_cached(req: MatchComputeRequest):
    """Compute pairwise match with caching and DTO sanitization.

    Pipeline:
      1. Check matches table for cached result → return if found
      2. Load natal data from user_natal_data (no recomputation!)
      3. Flatten data and feed to compute_match_v2()
      4. (Optional) LLM → synastry insight report
      5. Sanitize via api_presenter → safe DTO
      6. Cache result in matches table
      7. Return safe DTO
    """
    try:
        import db_client

        # 1. Cache check
        if not req.force_recompute:
            try:
                cached = db_client.get_cached_match(req.user_a_id, req.user_b_id)
                if cached:
                    return {
                        "status": "success",
                        "cached": True,
                        "data": {
                            "harmony_score": cached.get("harmony_score"),
                            "tension_level": cached.get("tension_level"),
                            "badges": cached.get("badges", []),
                            "tracks": cached.get("tracks", {}),
                            "ai_insight_report": cached.get("llm_insight_report", ""),
                        }
                    }
            except Exception:
                pass  # If cache check fails, proceed to compute

        # 2. Load natal data
        natal_a = db_client.get_natal_data(req.user_a_id)
        natal_b = db_client.get_natal_data(req.user_b_id)

        if not natal_a or not natal_b:
            raise HTTPException(
                status_code=404,
                detail="Natal data not found. Both users must complete onboarding first."
            )

        # 3. Flatten chart data for compute_match_v2
        # compute_match_v2 expects flat user dicts with sign keys at top level
        def _flatten_natal(natal: dict) -> dict:
            """Merge western_chart + bazi_chart fields into a flat dict."""
            flat = {}
            wc = natal.get("western_chart", {})
            bc = natal.get("bazi_chart", {})
            flat.update(wc)
            # Add bazi fields that matching.py expects
            flat["bazi_element"] = bc.get("day_master_element", wc.get("bazi_element"))
            flat["bazi_month_branch"] = bc.get("bazi_month_branch", wc.get("bazi_month_branch"))
            flat["bazi_day_branch"] = bc.get("bazi_day_branch", wc.get("bazi_day_branch"))
            flat["bazi"] = bc
            # data_tier from western chart
            flat.setdefault("data_tier", wc.get("data_tier", 3))
            return flat

        user_a = _flatten_natal(natal_a)
        user_b = _flatten_natal(natal_b)

        # 3.5 Load or compute psychology profiles (non-blocking, cache-first)
        prof_a: dict = {}
        prof_b: dict = {}
        try:
            prof_a = db_client.get_or_compute_psychology_profile(req.user_a_id, natal_a)
            prof_b = db_client.get_or_compute_psychology_profile(req.user_b_id, natal_b)
        except Exception:
            pass  # Profile enrichment is non-critical; matching still works without it

        # 4. Compute match
        raw_result = compute_match_v2(user_a, user_b)

        # 5. Optional LLM report
        llm_report = ""
        if req.generate_report:
            try:
                prompt = build_synastry_report_prompt(raw_result, prof_a, prof_b)
                llm_report = call_llm(
                    prompt, provider=req.provider, max_tokens=400,
                    api_key=req.api_key, gemini_model=req.gemini_model,
                )
            except Exception:
                llm_report = ""  # Never block matching for LLM failure

        # 6. Sanitize
        safe_response = format_safe_match_response(raw_result, llm_report)

        # 7. Cache result (non-blocking)
        try:
            db_client.save_match_result(
                user_a_id=req.user_a_id,
                user_b_id=req.user_b_id,
                safe_result=safe_response,
                raw_result=raw_result,
            )
        except Exception:
            pass  # Cache failure is non-critical

        safe_response["cached"] = False
        return safe_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
