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
from prompt_manager import get_match_report_prompt, get_simple_report_prompt, get_profile_prompt, get_ideal_match_prompt
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
