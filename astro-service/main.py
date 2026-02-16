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
from pydantic import BaseModel
from chart import calculate_chart

app = FastAPI(title="DESTINY Astro Service", version="0.1.0")


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
