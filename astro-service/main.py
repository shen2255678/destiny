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


ARCHETYPE_PROMPT = """\
你是 DESTINY 平台的靈魂分析師。根據以下兩人的星盤相容性數據，生成配對解讀。

數據：
- VibeScore（肉體吸引力）: {lust_score}/100
- ChemistryScore（靈魂深度）: {soul_score}/100
- 主要連結類型: {primary_track}
- 四象限: {quadrant}
- 標籤: {labels}
- 四軌分數: friend={friend} passion={passion} partner={partner} soul={soul}
- 權力動態: {viewer_role}（{person_a}）→ {target_role}（{person_b}），RPV={rpv}
- 框架崩潰（Chiron觸發）: {frame_break}

請只回傳以下 JSON 格式，不要包含任何其他文字或 markdown：
{{
  "archetype_tags": ["tag1", "tag2", "tag3"],
  "report": "約150字的繁體中文解讀報告"
}}

規則：
- archetype_tags 為 3 個英文詞組（每個 2-4 個字），描述這段關係的本質
- report 用自然、有溫度的繁體中文，直接描述這兩人的連結特質
"""


class ArchetypeRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    language: str = "zh-TW"
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-archetype")
def generate_archetype(req: ArchetypeRequest):
    """Generate AI archetype tags + interpretation report via Claude or Gemini."""
    md = req.match_data
    tracks = md.get("tracks", {})
    power = md.get("power", {})

    prompt = ARCHETYPE_PROMPT.format(
        lust_score=round(md.get("lust_score", 0), 1),
        soul_score=round(md.get("soul_score", 0), 1),
        primary_track=md.get("primary_track", "unknown"),
        quadrant=md.get("quadrant", "unknown"),
        labels=", ".join(md.get("labels", [])),
        friend=tracks.get("friend", 0),
        passion=tracks.get("passion", 0),
        partner=tracks.get("partner", 0),
        soul=tracks.get("soul", 0),
        viewer_role=power.get("viewer_role", "Equal"),
        target_role=power.get("target_role", "Equal"),
        person_a=req.person_a_name,
        person_b=req.person_b_name,
        rpv=power.get("rpv", 0),
        frame_break=power.get("frame_break", False),
    )

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


PROFILE_CARD_PROMPT = """\
你是一個精通心理學與占星八字的現代交友顧問。請根據以下使用者的命理特徵參數，生成一份適合在交友軟體上展示的個人名片。
文案需要生活化、有吸引力，絕對不要使用生硬的算命術語（如：食神、七殺、刑衝剋害），請轉化為白話的性格描述。必須以 JSON 格式回傳。

使用者特徵：
- 太陽星座: {sun_sign}
- 月亮星座: {moon_sign}
- 上升星座: {ascendant_sign}
- 八字日主五行: {bazi_element}
- 依戀風格: {attachment_style}
- 衝突處理: {rpv_conflict}
- 權力偶好: {rpv_power}
- 能量模式: {rpv_energy}

請只回傳以下 JSON 格式，不要包含任何其他文字：
{{
  "headline": "3-6字的人格標題（例：靈魂探索者、溫柔颶風）",
  "tags": ["標籤1", "標籤2", "標籤3", "標籤4"],
  "bio": "約80字的交友自介，第一人稱，生活化，有個性",
  "vibe_keywords": ["氛圍關鍵字1", "氛圍關鍵字2", "氛圍關鍵字3"]
}}
"""


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
    """Generate a dating-app profile card via Claude or Gemini."""
    cd = req.chart_data
    rpv = req.rpv_data
    prompt = PROFILE_CARD_PROMPT.format(
        sun_sign=cd.get("sun_sign", "unknown"),
        moon_sign=cd.get("moon_sign", "unknown"),
        ascendant_sign=cd.get("ascendant_sign", "unknown"),
        bazi_element=cd.get("bazi_element", "unknown"),
        attachment_style=req.attachment_style,
        rpv_conflict=rpv.get("rpv_conflict", "unknown"),
        rpv_power=rpv.get("rpv_power", "unknown"),
        rpv_energy=rpv.get("rpv_energy", "unknown"),
    )

    raw = ""
    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=500, api_key=req.api_key, gemini_model=req.gemini_model)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


MATCH_REPORT_PROMPT = """\
你是一位高情商的關係諮商師。請根據 {person_a} 與 {person_b} 兩人的合盤分數與互動特徵，\
寫出一份雙方都能看懂的「關係潛力報告」。
請分為「閃光點（高分項目）」與「潛在雷區（低分項目）」，並給出具體的相處建議。
請客觀且帶有溫度，若有衝突點，請包裝成「成長課題」而非缺點。

合盤數據：
- VibeScore（肉體吸引力）: {lust_score}/100
- ChemistryScore（靈魂深度）: {soul_score}/100
- 主要連結類型: {primary_track}
- 四象限: {quadrant}
- 四軌: friend={friend} passion={passion} partner={partner} soul={soul}
- 權力動態: {person_a}={viewer_role}，{person_b}={target_role}，RPV={rpv}
- Chiron框架觸發: {frame_break}
- 系統標籤: {labels}

請只回傳以下 JSON，不要包含任何其他文字：
{{
  "title": "這段關係的標題（8字以內）",
  "sparks": ["閃光點1", "閃光點2", "閃光點3"],
  "landmines": ["成長課題1", "成長課題2"],
  "advice": "約100字的相處建議，具體可操作",
  "one_liner": "一句話描述這段關係的本質（詩意但直白）"
}}
"""


class MatchReportRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    provider: str = "anthropic"  # "anthropic" | "gemini"
    api_key: str = ""            # overrides server env var when provided
    gemini_model: str = "gemini-2.0-flash"  # used only when provider="gemini"


@app.post("/generate-match-report")
def generate_match_report(req: MatchReportRequest):
    """Generate a full synastry relationship report via Claude or Gemini."""
    md = req.match_data
    tracks = md.get("tracks", {})
    power = md.get("power", {})
    prompt = MATCH_REPORT_PROMPT.format(
        person_a=req.person_a_name,
        person_b=req.person_b_name,
        lust_score=round(md.get("lust_score", 0), 1),
        soul_score=round(md.get("soul_score", 0), 1),
        primary_track=md.get("primary_track", "unknown"),
        quadrant=md.get("quadrant", "unknown"),
        friend=tracks.get("friend", 0),
        passion=tracks.get("passion", 0),
        partner=tracks.get("partner", 0),
        soul=tracks.get("soul", 0),
        viewer_role=power.get("viewer_role", "Equal"),
        target_role=power.get("target_role", "Equal"),
        rpv=power.get("rpv", 0),
        frame_break=power.get("frame_break", False),
        labels=", ".join(md.get("labels", [])),
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
