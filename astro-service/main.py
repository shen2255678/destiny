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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chart import calculate_chart
from bazi import analyze_element_relation
from matching import compute_match_score, compute_match_v2
from anthropic import Anthropic
import google.generativeai as genai

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


# ── Algorithm Validation Sandbox Endpoints ─────────────────────────────────


def call_llm(prompt: str, provider: str = "anthropic", max_tokens: int = 600) -> str:
    """Call Claude (Anthropic) or Gemini based on provider.

    Raises HTTPException 400 if the required API key is not set.
    Returns raw text from the model.
    """
    if provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY not set")
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    else:  # anthropic (default)
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")
        message = anthropic_client.messages.create(
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

    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=600)
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

    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=500)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


MATCH_REPORT_PROMPT = """\
\u4f60\u662f\u4e00\u4f4d\u9ad8\u60c5\u5546\u7684\u95dc\u4fc2\u8ae6\u5546\u5e2b\u3002\u8acb\u6839\u64da {person_a} \u8207 {person_b} \u5169\u4eba\u7684\u5408\u76e4\u5206\u6578\u8207\u4e92\u52d5\u7279\u5fb5\uff0c\
\u5beb\u51fa\u4e00\u4efd\u96d9\u65b9\u90fd\u80fd\u770b\u61c2\u7684\u300c\u95dc\u4fc2\u6f5b\u529b\u5831\u544a\u300d\u3002
\u8acb\u5206\u70ba\u300c\u9583\u5149\u9ede\uff08\u9ad8\u5206\u9805\u76ee\uff09\u300d\u8207\u300c\u6f5b\u5728\u96f7\u5340\uff08\u4f4e\u5206\u9805\u76ee\uff09\u300d\uff0c\u4e26\u7d66\u51fa\u5177\u9ad4\u7684\u76f8\u8655\u5efa\u8b70\u3002
\u8acb\u5ba2\u89c0\u4e14\u5e36\u6709\u6eab\u5ea6\uff0c\u82e5\u6709\u885d\u7a81\u9ede\uff0c\u8acb\u5305\u88dd\u6210\u300c\u6210\u9577\u8ab2\u984c\u300d\u800c\u975e\u7f3a\u9ede\u3002

\u5408\u76e4\u6578\u64da\uff1a
- VibeScore\uff08\u8089\u9ad4\u5438\u5f15\u529b\uff09: {lust_score}/100
- ChemistryScore\uff08\u9748\u9b42\u6df1\u5ea6\uff09: {soul_score}/100
- \u4e3b\u8981\u9023\u7d50\u985e\u578b: {primary_track}
- \u56db\u8c61\u9650: {quadrant}
- \u56db\u8ecc: friend={friend} passion={passion} partner={partner} soul={soul}
- \u6b0a\u529b\u52d5\u614b: {person_a}={viewer_role}\uff0c{person_b}={target_role}\uff0cRPV={rpv}
- Chiron\u6846\u67b6\u89f8\u767c: {frame_break}
- \u7cfb\u7d71\u6a19\u7c64: {labels}

\u8acb\u53ea\u56de\u50b3\u4ee5\u4e0b JSON\uff0c\u4e0d\u8981\u5305\u542b\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\uff1a
{{
  "title": "\u9019\u6bb5\u95dc\u4fc2\u7684\u6a19\u984c\uff088\u5b57\u4ee5\u5167\uff09",
  "sparks": ["\u9583\u5149\u96621", "\u9583\u5149\u96622", "\u9583\u5149\u96623"],
  "landmines": ["\u6210\u9577\u8ab2\u98981", "\u6210\u9577\u8ab2\u98982"],
  "advice": "\u7d0460\u5b57\u7684\u76f8\u8655\u5efa\u8b70\uff0c\u5177\u9ad4\u53ef\u64cd\u4f5c",
  "one_liner": "\u4e00\u53e5\u8a71\u63cf\u8ff0\u9019\u6bb5\u95dc\u4fc2\u7684\u672c\u8cea\uff08\u8a69\u610f\u4f46\u76f4\u767d\uff09"
}}
"""


class MatchReportRequest(BaseModel):
    match_data: dict
    person_a_name: str = "A"
    person_b_name: str = "B"
    provider: str = "anthropic"  # "anthropic" | "gemini"


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

    try:
        raw = call_llm(prompt, provider=req.provider, max_tokens=700)
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
