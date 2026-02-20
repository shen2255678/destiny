"""
DESTINY — Astrology Microservice
FastAPI server for natal chart calculation.

Endpoints:
  GET  /health           → health check
  POST /calculate-chart  → compute zodiac signs from birth data
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chart import calculate_chart
from bazi import analyze_element_relation
from matching import compute_match_score, compute_match_v2

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


class ChartRequest(BaseModel):
    birth_date: str                              # "1995-06-15"
    birth_time: Optional[str] = None             # "precise" | "morning" | "afternoon" | "evening" | "unknown"
    birth_time_exact: Optional[str] = None       # "14:30"
    lat: float = 25.033
    lng: float = 121.565
    data_tier: int = 3


@app.get("/health")
def health():
    return {"status": "ok"}


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
               ascendant_sign, bazi_element, rpv_conflict, rpv_power, rpv_energy
      Phase G: mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign,
               house4_sign, house8_sign, attachment_style

    Returns: lust_score, soul_score, power {rpv, frame_break, viewer_role, target_role},
             tracks {friend, passion, partner, soul}, primary_track, quadrant, labels
    """
    try:
        result = compute_match_v2(req.user_a, req.user_b)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
