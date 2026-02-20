# Algorithm Validation Sandbox Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `astro-service/sandbox.html` — a standalone internal testing page that validates the Phase G matching algorithm against real-world couples, with three LLM-powered generation tools (archetype tags, user profile card, synastry match report).

**Architecture:** Single HTML file (`astro-service/sandbox.html`) calls `astro-service:8001` via fetch. Four new capabilities added to FastAPI: CORS middleware + three LLM endpoints (`/generate-archetype`, `/generate-profile-card`, `/generate-match-report`) that proxy to Claude API. Two-tab UI: Mechanism A (positive control) + Mechanism B (rectification simulation).

**Tech Stack:** Vanilla HTML/CSS/JS, FastAPI, Python `anthropic` SDK (>=0.40.0), pyswisseph (already installed), Anthropic claude-haiku-4-5-20251001.

**Design doc:** `docs/plans/2026-02-20-algorithm-validation-sandbox-design.md`

---

## Context You Must Know

**astro-service** runs at `http://localhost:8001`. Key endpoints:
- `POST /calculate-chart` — takes birth data, returns all planetary signs + bazi_element
- `POST /compute-match` — takes `{user_a: dict, user_b: dict}`, returns Phase G v2 result
- `GET /health` — health check

**compute_match_v2 output shape:**
```json
{
  "lust_score": 82.0,
  "soul_score": 71.0,
  "power": {"rpv": 25.0, "frame_break": false, "viewer_role": "Dom", "target_role": "Sub"},
  "tracks": {"friend": 45.0, "passion": 78.0, "partner": 62.0, "soul": 55.0},
  "primary_track": "passion",
  "quadrant": "lover",
  "labels": ["✦ 激情型連結"]
}
```

**MATCH/MISMATCH thresholds (tunable in UI):**
| ground_truth | MATCH condition |
|---|---|
| 已婚（穩定）| `soul_score >= 65` AND `primary_track in ["partner","soul"]` |
| 已分手（慘烈）| `(lust_score + soul_score) / 2 <= 55` |
| 已分手（和平）| `lust_score <= 60` AND `soul_score < 65` |
| 萬年好友 | `primary_track == "friend"` AND `lust_score <= 60` |

**Sign aspect JS helper (needed for component logs):**
```javascript
const SIGNS = ["aries","taurus","gemini","cancer","leo","virgo",
               "libra","scorpio","sagittarius","capricorn","aquarius","pisces"];
const ASPECT_SCORES = {0:0.90, 1:0.65, 2:0.75, 3:0.50, 4:0.85, 5:0.65, 6:0.60};
function signAspect(a, b) {
  if (!a || !b) return 0.65;
  const ia = SIGNS.indexOf(a), ib = SIGNS.indexOf(b);
  if (ia < 0 || ib < 0) return 0.65;
  let d = Math.abs(ia - ib) % 12;
  if (d > 6) d = 12 - d;
  return ASPECT_SCORES[d] ?? 0.65;
}
```

---

## Task 1: Add CORS Middleware + anthropic Dependency

**Files:**
- Modify: `astro-service/main.py` (add after `app = FastAPI(...)` block ~line 31)
- Modify: `astro-service/requirements.txt` (append one line)

**Step 1: Add `anthropic` to requirements.txt**

Append this line to `astro-service/requirements.txt`:
```
anthropic>=0.40.0
```

**Step 2: Install the new dependency**

```bash
cd astro-service
pip install anthropic
```
Expected: `Successfully installed anthropic-...`

**Step 3: Add CORS middleware to main.py**

In `astro-service/main.py`, add this import at the top (after existing imports):
```python
from fastapi.middleware.cors import CORSMiddleware
```

Then add these lines immediately after the `app = FastAPI(...)` block (around line 31, before `class ChartRequest`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 4: Verify CORS works**

Start the service and test with curl:
```bash
cd astro-service
uvicorn main:app --port 8001 &
curl -s -X OPTIONS http://localhost:8001/health \
  -H "Origin: null" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i "access-control"
```
Expected output contains: `access-control-allow-origin: *`

**Step 5: Run existing tests to verify nothing broke**

```bash
cd astro-service
pytest test_chart.py test_matching.py -v
```
Expected: all 71 tests PASS

**Step 6: Commit**

```bash
git add astro-service/main.py astro-service/requirements.txt
git commit -m "feat: add CORS middleware + anthropic dependency to astro-service"
```

---

## Task 2: Add /generate-archetype Endpoint

**Files:**
- Modify: `astro-service/main.py` (append imports + new endpoint at end of file)
- Create: `astro-service/test_sandbox.py`

**Step 1: Write the failing test**

Create `astro-service/test_sandbox.py`:
```python
"""Tests for sandbox-specific endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_MATCH_DATA = {
    "lust_score": 82.0,
    "soul_score": 71.0,
    "power": {"rpv": 25.0, "frame_break": False, "viewer_role": "Dom", "target_role": "Sub"},
    "tracks": {"friend": 45.0, "passion": 78.0, "partner": 62.0, "soul": 55.0},
    "primary_track": "passion",
    "quadrant": "lover",
    "labels": ["✦ 激情型連結"],
}


def test_generate_archetype_returns_tags_and_report():
    """Endpoint returns archetype_tags list + report string."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='{"archetype_tags": ["Mirror Twins", "Power Clash", "Slow Burn"], "report": "測試報告內容"}')]

    with patch("main.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_msg

        resp = client.post("/generate-archetype", json={
            "match_data": SAMPLE_MATCH_DATA,
            "person_a_name": "Person A",
            "person_b_name": "Person B",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "archetype_tags" in data
    assert "report" in data
    assert isinstance(data["archetype_tags"], list)
    assert len(data["archetype_tags"]) == 3
    assert isinstance(data["report"], str)
    assert len(data["report"]) > 10


def test_generate_archetype_no_api_key_returns_400():
    """Returns 400 when ANTHROPIC_API_KEY is not set."""
    import os
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        resp = client.post("/generate-archetype", json={
            "match_data": SAMPLE_MATCH_DATA,
        })
        assert resp.status_code == 400
        assert "ANTHROPIC_API_KEY" in resp.json()["detail"]
    finally:
        if original:
            os.environ["ANTHROPIC_API_KEY"] = original
```

**Step 2: Run test to verify it fails**

```bash
cd astro-service
pytest test_sandbox.py -v
```
Expected: FAIL (ImportError: cannot import name 'anthropic_client' from 'main')

**Step 3: Add imports and endpoint to main.py**

At the top of `astro-service/main.py`, add after existing imports:
```python
import os
import json
from anthropic import Anthropic

anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
```

At the **end** of `astro-service/main.py`, append:
```python

# ── Algorithm Validation Sandbox Endpoints ─────────────────────────────────

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


@app.post("/generate-archetype")
def generate_archetype(req: ArchetypeRequest):
    """Generate AI archetype tags + interpretation report via Claude API."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")

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
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        result = json.loads(raw)
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Run tests**

```bash
cd astro-service
pytest test_sandbox.py -v
```
Expected: 2 tests PASS

**Step 5: Run ALL tests to make sure nothing broke**

```bash
cd astro-service
pytest test_chart.py test_matching.py test_sandbox.py -v
```
Expected: 73 tests PASS (71 original + 2 new)

**Step 6: Commit**

```bash
git add astro-service/main.py astro-service/test_sandbox.py
git commit -m "feat: add /generate-archetype endpoint with Claude API proxy + tests"
```

---

## Task 3: Build sandbox.html — Mechanism A (Partner Validation)

**Files:**
- Create: `astro-service/sandbox.html`

**Step 1: Create the file**

Create `astro-service/sandbox.html` with the complete content below.

Key sections:
1. CSS: dark theme, two-column layout, badge styles
2. HTML: Tab bar + Tab A content (two-person form + thresholds + results)
3. JS: signAspect helper, fetchChart(), runMatch(), computeMatchResult(), renderResults(), generateArchetype()

**Complete `astro-service/sandbox.html`:**

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>DESTINY — Algorithm Validation Sandbox</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; color: #e0dff8; font-family: 'Courier New', monospace; font-size: 13px; padding: 20px; }
  h1 { color: #c084fc; font-size: 18px; margin-bottom: 4px; letter-spacing: 2px; }
  .subtitle { color: #6b7280; font-size: 11px; margin-bottom: 20px; }
  .tabs { display: flex; gap: 4px; margin-bottom: 16px; }
  .tab-btn { background: #1a1a2e; color: #9ca3af; border: 1px solid #374151; padding: 6px 16px; cursor: pointer; border-radius: 4px 4px 0 0; font-size: 12px; }
  .tab-btn.active { background: #2d1b4e; color: #c084fc; border-color: #7c3aed; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
  .person-card { background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 14px; }
  .person-card h3 { color: #818cf8; font-size: 12px; margin-bottom: 10px; letter-spacing: 1px; }
  .field { margin-bottom: 8px; }
  .field label { display: block; color: #9ca3af; font-size: 11px; margin-bottom: 2px; }
  .field input, .field select { width: 100%; background: #1f2937; border: 1px solid #374151; color: #e0dff8; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: inherit; }
  .field input:focus, .field select:focus { outline: none; border-color: #7c3aed; }
  .lat-lng { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .threshold-row { background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
  .threshold-row h3 { color: #6b7280; font-size: 11px; margin-bottom: 8px; }
  .threshold-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .threshold-item label { color: #6b7280; font-size: 10px; display: block; margin-bottom: 2px; }
  .threshold-item input { width: 100%; background: #1f2937; border: 1px solid #374151; color: #e0dff8; padding: 3px 6px; border-radius: 4px; font-size: 11px; }
  .ground-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .ground-row label { color: #9ca3af; font-size: 12px; white-space: nowrap; }
  .ground-row select { background: #1f2937; border: 1px solid #374151; color: #e0dff8; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-family: inherit; }
  .btn { background: #7c3aed; color: white; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; font-size: 12px; font-family: inherit; letter-spacing: 1px; }
  .btn:hover { background: #6d28d9; }
  .btn-sm { background: #1e3a5f; color: #93c5fd; border: 1px solid #1e40af; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-family: inherit; }
  .btn-sm:hover { background: #1e40af; }
  .btn-sm:disabled { opacity: 0.5; cursor: not-allowed; }
  .results { display: none; background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 16px; margin-top: 16px; }
  .results.show { display: block; }
  .result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #374151; }
  .test-id { color: #6b7280; font-size: 11px; }
  .gt-label { color: #d1d5db; font-size: 12px; }
  .badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
  .badge.match { background: #065f46; color: #6ee7b7; border: 1px solid #059669; }
  .badge.mismatch { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }
  .score-section { margin-bottom: 12px; }
  .score-label { color: #a78bfa; font-size: 11px; margin-bottom: 4px; }
  .score-bar-wrap { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .score-bar { flex: 1; background: #374151; border-radius: 4px; height: 8px; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
  .score-val { color: #e0dff8; font-size: 13px; font-weight: bold; min-width: 50px; text-align: right; }
  .score-logs { color: #6b7280; font-size: 10px; line-height: 1.6; margin-top: 2px; }
  .tracks-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; }
  .track-item { text-align: center; }
  .track-name { color: #6b7280; font-size: 10px; margin-bottom: 3px; }
  .track-val { font-size: 14px; font-weight: bold; }
  .track-item.primary .track-name { color: #c084fc; }
  .track-item.primary .track-val { color: #c084fc; }
  .meta-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; font-size: 11px; }
  .meta-item .meta-k { color: #6b7280; }
  .meta-item .meta-v { color: #d1d5db; margin-left: 4px; }
  .labels-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .label-tag { background: #1e1b4b; color: #a78bfa; border: 1px solid #4338ca; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
  .archetype-section { border-top: 1px solid #374151; padding-top: 12px; }
  .archetype-section h4 { color: #6b7280; font-size: 11px; margin-bottom: 8px; }
  .archetype-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
  .archetype-tag { background: #1f2d4a; color: #60a5fa; border: 1px solid #2563eb; padding: 2px 10px; border-radius: 10px; font-size: 11px; }
  .report-text { color: #d1d5db; font-size: 12px; line-height: 1.7; background: #0f172a; padding: 10px; border-radius: 6px; border-left: 3px solid #7c3aed; }
  .loading { color: #6b7280; font-size: 11px; font-style: italic; }
  .error-msg { color: #fca5a5; font-size: 11px; margin-top: 4px; }
  /* Mechanism B */
  .mech-b-card { background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 16px; max-width: 500px; }
  .mech-b-card h3 { color: #818cf8; font-size: 12px; margin-bottom: 12px; }
  .rect-log { margin-top: 16px; }
  .rect-step { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; padding: 8px; background: #0f172a; border-radius: 6px; }
  .rect-q { color: #d1d5db; font-size: 12px; flex: 1; }
  .rect-q .q-text { margin-bottom: 6px; }
  .rect-q .q-window { color: #6b7280; font-size: 10px; }
  .rect-q .q-conf { color: #a78bfa; font-size: 10px; }
  .answer-btns { display: flex; gap: 6px; margin-top: 6px; }
  .answer-btn { padding: 3px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 11px; font-family: inherit; }
  .answer-btn.yes { background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }
  .answer-btn.no  { background: #450a0a; color: #fca5a5; border: 1px solid #dc2626; }
  .rect-result { margin-top: 14px; padding: 10px; border-radius: 6px; font-size: 12px; }
  .rect-result.pass { background: #065f46; color: #6ee7b7; border: 1px solid #059669; }
  .rect-result.fail { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }
  .conf-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
  .conf-label { color: #6b7280; font-size: 10px; min-width: 80px; }
  .conf-bar { flex: 1; background: #374151; border-radius: 4px; height: 6px; overflow: hidden; }
  .conf-bar-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #c084fc); border-radius: 4px; transition: width 0.4s; }
  .api-key-row { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding: 8px; background: #1a1a2e; border-radius: 6px; border: 1px solid #374151; }
  .api-key-row label { color: #6b7280; font-size: 11px; white-space: nowrap; }
  .api-key-row input { flex: 1; background: #0f172a; border: 1px solid #374151; color: #9ca3af; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-family: monospace; }
</style>
</head>
<body>

<h1>⬡ DESTINY — Algorithm Validation Sandbox</h1>
<p class="subtitle">Internal tool · Phase G matching algorithm validation · Not for production</p>

<!-- API Key Row (shared) -->
<div class="api-key-row">
  <label>ANTHROPIC_API_KEY (for archetype generation):</label>
  <input type="password" id="apiKeyInput" placeholder="sk-ant-... (optional, only needed for AI archetype generation)" />
</div>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('a')">Mechanism A — 伴侶驗證</button>
  <button class="tab-btn" onclick="switchTab('b')">Mechanism B — 校時模擬</button>
</div>

<!-- ═══ TAB A ═══ -->
<div id="tab-a" class="tab-content active">

  <div class="two-col">
    <!-- Person A -->
    <div class="person-card">
      <h3>PERSON A</h3>
      <div class="field"><label>顯示名稱</label><input type="text" id="a_name" value="Person A"></div>
      <div class="field"><label>出生日期</label><input type="date" id="a_birth_date" value="1990-03-15"></div>
      <div class="field"><label>出生時間（精確，可留空）</label><input type="time" id="a_birth_time_exact" value="14:30"></div>
      <div class="field lat-lng">
        <div><label>緯度</label><input type="number" id="a_lat" value="25.033" step="0.001"></div>
        <div><label>經度</label><input type="number" id="a_lng" value="121.565" step="0.001"></div>
      </div>
      <div class="field"><label>Data Tier</label>
        <select id="a_data_tier">
          <option value="1" selected>Tier 1（精確出生時間）</option>
          <option value="2">Tier 2（模糊時段）</option>
          <option value="3">Tier 3（只有日期）</option>
        </select>
      </div>
      <div class="field"><label>RPV 衝突風格</label>
        <select id="a_rpv_conflict">
          <option value="cold_war">冷戰 (cold_war)</option>
          <option value="argue">直接開吵 (argue)</option>
        </select>
      </div>
      <div class="field"><label>RPV 權力偏好</label>
        <select id="a_rpv_power">
          <option value="control">主導 (control)</option>
          <option value="follow">跟隨 (follow)</option>
        </select>
      </div>
      <div class="field"><label>RPV 能量模式</label>
        <select id="a_rpv_energy">
          <option value="home">宅 (home)</option>
          <option value="out">出門 (out)</option>
        </select>
      </div>
      <div class="field"><label>依戀風格</label>
        <select id="a_attachment_style">
          <option value="secure">安全型 (secure)</option>
          <option value="anxious">焦慮型 (anxious)</option>
          <option value="avoidant">迴避型 (avoidant)</option>
        </select>
      </div>
    </div>

    <!-- Person B -->
    <div class="person-card">
      <h3>PERSON B</h3>
      <div class="field"><label>顯示名稱</label><input type="text" id="b_name" value="Person B"></div>
      <div class="field"><label>出生日期</label><input type="date" id="b_birth_date" value="1992-08-22"></div>
      <div class="field"><label>出生時間（精確，可留空）</label><input type="time" id="b_birth_time_exact" value="09:15"></div>
      <div class="field lat-lng">
        <div><label>緯度</label><input type="number" id="b_lat" value="25.033" step="0.001"></div>
        <div><label>經度</label><input type="number" id="b_lng" value="121.565" step="0.001"></div>
      </div>
      <div class="field"><label>Data Tier</label>
        <select id="b_data_tier">
          <option value="1" selected>Tier 1（精確出生時間）</option>
          <option value="2">Tier 2（模糊時段）</option>
          <option value="3">Tier 3（只有日期）</option>
        </select>
      </div>
      <div class="field"><label>RPV 衝突風格</label>
        <select id="b_rpv_conflict">
          <option value="cold_war">冷戰 (cold_war)</option>
          <option value="argue">直接開吵 (argue)</option>
        </select>
      </div>
      <div class="field"><label>RPV 權力偏好</label>
        <select id="b_rpv_power">
          <option value="control">主導 (control)</option>
          <option value="follow" selected>跟隨 (follow)</option>
        </select>
      </div>
      <div class="field"><label>RPV 能量模式</label>
        <select id="b_rpv_energy">
          <option value="home">宅 (home)</option>
          <option value="out" selected>出門 (out)</option>
        </select>
      </div>
      <div class="field"><label>依戀風格</label>
        <select id="b_attachment_style">
          <option value="secure" selected>安全型 (secure)</option>
          <option value="anxious">焦慮型 (anxious)</option>
          <option value="avoidant">迴避型 (avoidant)</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Ground Truth + Thresholds -->
  <div class="threshold-row">
    <h3>MATCH/MISMATCH 閾值（可調整）</h3>
    <div class="threshold-grid">
      <div class="threshold-item">
        <label>已婚穩定 min_soul</label>
        <input type="number" id="th_married_soul" value="65" min="0" max="100">
      </div>
      <div class="threshold-item">
        <label>慘烈分手 max_avg</label>
        <input type="number" id="th_bad_avg" value="55" min="0" max="100">
      </div>
      <div class="threshold-item">
        <label>和平分手 max_lust</label>
        <input type="number" id="th_ok_lust" value="60" min="0" max="100">
      </div>
      <div class="threshold-item">
        <label>好友 max_lust</label>
        <input type="number" id="th_friend_lust" value="60" min="0" max="100">
      </div>
    </div>
  </div>

  <div class="ground-row">
    <label>Ground Truth:</label>
    <select id="ground_truth">
      <option value="married_stable">已婚（穩定）</option>
      <option value="divorced_ok">已分手（和平）</option>
      <option value="divorced_bad">已分手（慘烈）</option>
      <option value="friends">萬年好友</option>
    </select>
    <button class="btn" onclick="runMatch()">▶ Run Match</button>
    <span id="run_status" class="loading"></span>
  </div>

  <div id="results-a" class="results"></div>

</div><!-- end tab-a -->

<!-- ═══ TAB B ═══ -->
<div id="tab-b" class="tab-content">
  <div class="mech-b-card">
    <h3>MECHANISM B — Birth Time Rectification Simulation</h3>
    <p style="color:#6b7280;font-size:11px;margin-bottom:12px;">輸入一個已知的精確出生時間，模擬當系統只知道「時段」時，經過 Via Negativa 問題序列能否將視窗縮小並涵蓋原始時間。</p>
    <div class="field"><label>姓名</label><input type="text" id="b2_name" value="Test Person"></div>
    <div class="field"><label>出生日期</label><input type="date" id="b2_date" value="1990-03-15"></div>
    <div class="field"><label>精確出生時間（Ground Truth）</label><input type="time" id="b2_precise" value="14:30"></div>
    <div style="margin-top:12px">
      <button class="btn" onclick="startRectSim()">▶ Simulate Rectification</button>
    </div>
    <div id="rect-log" class="rect-log"></div>
  </div>
</div><!-- end tab-b -->

<script>
// ── Constants ──────────────────────────────────────────────────
const BASE = 'http://localhost:8001';

const SIGNS = ["aries","taurus","gemini","cancer","leo","virgo",
               "libra","scorpio","sagittarius","capricorn","aquarius","pisces"];
const ASPECT_SCORES = {0:0.90, 1:0.65, 2:0.75, 3:0.50, 4:0.85, 5:0.65, 6:0.60};

function signAspect(a, b) {
  if (!a || !b) return 0.65;
  const ia = SIGNS.indexOf(a), ib = SIGNS.indexOf(b);
  if (ia < 0 || ib < 0) return 0.65;
  let d = Math.abs(ia - ib) % 12;
  if (d > 6) d = 12 - d;
  return ASPECT_SCORES[d] ?? 0.65;
}

function fmt(v) { return (v * 100).toFixed(0); }
function fmtScore(v) { return v.toFixed(1); }

// ── Tab switching ──────────────────────────────────────────────
function switchTab(id) {
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', ['a','b'][i] === id));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
}

// ── Test ID generation ─────────────────────────────────────────
let testCounter = 1;
function genTestId() {
  const d = new Date();
  const s = d.toISOString().slice(0,10).replace(/-/g,'');
  return `A-${s}-${String(testCounter++).padStart(3,'0')}`;
}

// ── Mechanism A ────────────────────────────────────────────────
async function fetchChart(prefix) {
  const date   = document.getElementById(`${prefix}_birth_date`).value;
  const time   = document.getElementById(`${prefix}_birth_time_exact`).value;
  const lat    = parseFloat(document.getElementById(`${prefix}_lat`).value);
  const lng    = parseFloat(document.getElementById(`${prefix}_lng`).value);
  const tier   = parseInt(document.getElementById(`${prefix}_data_tier`).value);

  const body = { birth_date: date, lat, lng, data_tier: tier };
  if (time) {
    body.birth_time_exact = time;
    body.birth_time = 'precise';
  }

  const r = await fetch(`${BASE}/calculate-chart`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(`/calculate-chart failed: ${await r.text()}`);
  return r.json();
}

function getRpv(prefix) {
  return {
    rpv_conflict:     document.getElementById(`${prefix}_rpv_conflict`).value,
    rpv_power:        document.getElementById(`${prefix}_rpv_power`).value,
    rpv_energy:       document.getElementById(`${prefix}_rpv_energy`).value,
    attachment_style: document.getElementById(`${prefix}_attachment_style`).value,
    data_tier:        parseInt(document.getElementById(`${prefix}_data_tier`).value),
  };
}

function computeIsMatch(gt, lust, soul, primaryTrack) {
  const minSoul  = parseInt(document.getElementById('th_married_soul').value);
  const maxAvg   = parseInt(document.getElementById('th_bad_avg').value);
  const maxLust  = parseInt(document.getElementById('th_ok_lust').value);
  const maxFLust = parseInt(document.getElementById('th_friend_lust').value);

  if (gt === 'married_stable')
    return soul >= minSoul && (primaryTrack === 'partner' || primaryTrack === 'soul');
  if (gt === 'divorced_bad')
    return (lust + soul) / 2 <= maxAvg;
  if (gt === 'divorced_ok')
    return lust <= maxLust && soul < 65;
  if (gt === 'friends')
    return primaryTrack === 'friend' && lust <= maxFLust;
  return false;
}

const GT_LABELS = {
  married_stable: '已婚（穩定）',
  divorced_ok:    '已分手（和平）',
  divorced_bad:   '已分手（慘烈）',
  friends:        '萬年好友',
};

function buildLogs(chartA, chartB) {
  const lust_logs = [
    `venus ${fmtScore(signAspect(chartA.venus_sign, chartB.venus_sign))} × 0.20`,
    `mars  ${fmtScore(signAspect(chartA.mars_sign,  chartB.mars_sign))}  × 0.25`,
    `pluto ${fmtScore(signAspect(chartA.pluto_sign, chartB.pluto_sign))} × 0.25`,
    (chartA.house8_sign && chartB.house8_sign)
      ? `house8 ${fmtScore(signAspect(chartA.house8_sign, chartB.house8_sign))} × 0.15`
      : `house8 N/A (no precise time)`,
  ];
  const soul_logs = [
    `moon     ${fmtScore(signAspect(chartA.moon_sign,    chartB.moon_sign))}    × 0.25`,
    `mercury  ${fmtScore(signAspect(chartA.mercury_sign, chartB.mercury_sign))} × 0.20`,
    `saturn   ${fmtScore(signAspect(chartA.saturn_sign,  chartB.saturn_sign))}  × 0.20`,
    (chartA.house4_sign && chartB.house4_sign)
      ? `house4   ${fmtScore(signAspect(chartA.house4_sign, chartB.house4_sign))} × 0.15`
      : `house4   N/A (no precise time)`,
    (chartA.juno_sign && chartB.juno_sign)
      ? `juno     ${fmtScore(signAspect(chartA.juno_sign, chartB.juno_sign))}    × 0.20`
      : `juno     N/A`,
  ];
  return { lust_logs, soul_logs };
}

function renderResults(testId, gt, match, matchData, chartA, chartB, nameA, nameB) {
  const { lust_score, soul_score, power, tracks, primary_track, quadrant, labels } = matchData;
  const { lust_logs, soul_logs } = buildLogs(chartA, chartB);

  const trackColors = { friend: '#34d399', passion: '#f87171', partner: '#60a5fa', soul: '#c084fc' };
  const tracksHtml = ['friend','passion','partner','soul'].map(k => {
    const isPrimary = k === primary_track;
    const color = trackColors[k];
    return `<div class="track-item${isPrimary?' primary':''}">
      <div class="track-name">${k}</div>
      <div class="track-val" style="color:${color}">${tracks[k].toFixed(1)}</div>
    </div>`;
  }).join('');

  const labelsHtml = labels.map(l => `<span class="label-tag">${l}</span>`).join('');

  const container = document.getElementById('results-a');
  container.className = 'results show';
  container.innerHTML = `
    <div class="result-header">
      <span class="test-id">${testId}</span>
      <span class="gt-label">${GT_LABELS[gt]}</span>
      <span class="badge ${match ? 'match' : 'mismatch'}">${match ? 'MATCH ✓' : 'MISMATCH ✗'}</span>
    </div>

    <div class="score-section">
      <div class="score-label">VibeScore (lust_score)</div>
      <div class="score-bar-wrap">
        <div class="score-bar"><div class="score-bar-fill" style="width:${lust_score}%;background:linear-gradient(90deg,#f87171,#fb923c)"></div></div>
        <div class="score-val" style="color:#f87171">${lust_score.toFixed(1)} / 100</div>
      </div>
      <div class="score-logs">${lust_logs.join('<br>')}</div>
    </div>

    <div class="score-section">
      <div class="score-label">ChemistryScore (soul_score)</div>
      <div class="score-bar-wrap">
        <div class="score-bar"><div class="score-bar-fill" style="width:${soul_score}%;background:linear-gradient(90deg,#818cf8,#c084fc)"></div></div>
        <div class="score-val" style="color:#818cf8">${soul_score.toFixed(1)} / 100</div>
      </div>
      <div class="score-logs">${soul_logs.join('<br>')}</div>
    </div>

    <div class="score-section">
      <div class="score-label" style="margin-bottom:6px">四軌分數 (Tracks)</div>
      <div class="tracks-row">${tracksHtml}</div>
    </div>

    <div class="meta-row">
      <div class="meta-item"><span class="meta-k">primary_track</span><span class="meta-v" style="color:#c084fc">${primary_track}</span></div>
      <div class="meta-item"><span class="meta-k">quadrant</span><span class="meta-v">${quadrant}</span></div>
      <div class="meta-item"><span class="meta-k">RPV</span><span class="meta-v">${power.rpv > 0 ? '+' : ''}${power.rpv}</span></div>
      <div class="meta-item"><span class="meta-k">${nameA}</span><span class="meta-v">${power.viewer_role}</span></div>
      <div class="meta-item"><span class="meta-k">${nameB}</span><span class="meta-v">${power.target_role}</span></div>
      <div class="meta-item"><span class="meta-k">frame_break</span><span class="meta-v" style="color:${power.frame_break?'#f87171':'#34d399'}">${power.frame_break}</span></div>
    </div>

    <div class="labels-row">${labelsHtml}</div>

    <div class="archetype-section">
      <h4>AI ARCHETYPE + 解讀報告</h4>
      <button class="btn-sm" id="archetype-btn" onclick="generateArchetype(${JSON.stringify(matchData).replace(/"/g,'&quot;')}, '${nameA}', '${nameB}')">✦ Generate</button>
      <div id="archetype-output" style="margin-top:8px"></div>
    </div>
  `;

  // Store match data for archetype generation
  window._lastMatchData = matchData;
  window._lastNameA = nameA;
  window._lastNameB = nameB;
}

async function runMatch() {
  const status = document.getElementById('run_status');
  status.textContent = '計算中...';
  try {
    const [chartA, chartB] = await Promise.all([fetchChart('a'), fetchChart('b')]);
    const nameA = document.getElementById('a_name').value || 'A';
    const nameB = document.getElementById('b_name').value || 'B';

    const userA = { ...chartA, ...getRpv('a') };
    const userB = { ...chartB, ...getRpv('b') };

    const r = await fetch(`${BASE}/compute-match`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ user_a: userA, user_b: userB })
    });
    if (!r.ok) throw new Error(`/compute-match failed: ${await r.text()}`);
    const matchData = await r.json();

    const gt = document.getElementById('ground_truth').value;
    const testId = genTestId();
    const match = computeIsMatch(gt, matchData.lust_score, matchData.soul_score, matchData.primary_track);

    renderResults(testId, gt, match, matchData, chartA, chartB, nameA, nameB);
    status.textContent = '';
  } catch (e) {
    status.textContent = '';
    document.getElementById('results-a').className = 'results show';
    document.getElementById('results-a').innerHTML = `<div class="error-msg">Error: ${e.message}</div>`;
  }
}

async function generateArchetype(matchData, nameA, nameB) {
  const btn = document.getElementById('archetype-btn');
  const out = document.getElementById('archetype-output');
  btn.disabled = true;
  out.innerHTML = '<div class="loading">呼叫 Claude API...</div>';

  try {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    const headers = {'Content-Type':'application/json'};
    // apiKey is passed as a note; actual key used by server env
    const r = await fetch(`${BASE}/generate-archetype`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        match_data: matchData,
        person_a_name: nameA,
        person_b_name: nameB,
      })
    });
    if (!r.ok) {
      const err = await r.json();
      throw new Error(err.detail || r.statusText);
    }
    const data = await r.json();
    const tagsHtml = (data.archetype_tags || []).map(t => `<span class="archetype-tag">${t}</span>`).join('');
    out.innerHTML = `
      <div class="archetype-tags">${tagsHtml}</div>
      <div class="report-text">${data.report || ''}</div>
    `;
  } catch (e) {
    out.innerHTML = `<div class="error-msg">Error: ${e.message}</div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── Mechanism B — Rectification Simulation ────────────────────
const VIA_NEGATIVA_QUESTIONS = [
  "你不是那種喜歡在人群中成為焦點的人",
  "你不是早起型的人，比起早晨更喜歡夜晚的能量",
  "你不是天生的計劃型，傾向即興而非按表操課",
  "你面對衝突時，不會選擇沉默迴避，傾向直接說出來",
  "你不是天生的領袖型，更享受輔助與配合他人的角色",
];

// Time slot center (minutes from midnight)
function slotCenter(h) {
  if (h >= 4  && h < 12) return { name: 'morning',   center: 8 * 60 };
  if (h >= 12 && h < 18) return { name: 'afternoon',  center: 15 * 60 };
  if (h >= 18 || h < 4)  return { name: 'evening',    center: 21 * 60 };
  return { name: 'unknown', center: 12 * 60 };
}

function minutesToHHMM(mins) {
  let h = Math.floor(((mins % 1440) + 1440) % 1440 / 60);
  let m = Math.floor(((mins % 1440) + 1440) % 1440 % 60);
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
}

let rectState = null;

function startRectSim() {
  const preciseTime = document.getElementById('b2_precise').value; // "HH:MM"
  if (!preciseTime) { alert('請輸入精確出生時間'); return; }

  const [hh, mm] = preciseTime.split(':').map(Number);
  const preciseMinutes = hh * 60 + mm;
  const { name: slotName, center } = slotCenter(hh);
  const initialWindowMin = slotName === 'unknown' ? 1440 : 360;

  rectState = {
    preciseMinutes,
    center,
    windowMin: initialWindowMin,
    confidence: 0.15,
    questionIdx: 0,
    halfWindow: initialWindowMin / 2,
  };

  const logEl = document.getElementById('rect-log');
  logEl.innerHTML = `
    <div style="margin-bottom:10px;font-size:11px;color:#9ca3af">
      精確時間: <b style="color:#e0dff8">${preciseTime}</b> →
      時段: <b style="color:#c084fc">${slotName}</b> →
      初始視窗: <b style="color:#e0dff8">${minutesToHHMM(center - rectState.halfWindow)} ～ ${minutesToHHMM(center + rectState.halfWindow)}</b>
      （${initialWindowMin} 分鐘）
    </div>
    <div class="conf-bar-wrap">
      <span class="conf-label">Confidence: 0.15</span>
      <div class="conf-bar"><div class="conf-bar-fill" id="conf-fill" style="width:15%"></div></div>
    </div>
    <div id="rect-questions" style="margin-top:12px"></div>
    <div id="rect-final"></div>
  `;

  showNextQuestion();
}

function showNextQuestion() {
  if (!rectState) return;
  if (rectState.questionIdx >= VIA_NEGATIVA_QUESTIONS.length) {
    showRectResult();
    return;
  }
  const q = VIA_NEGATIVA_QUESTIONS[rectState.questionIdx];
  const qContainer = document.getElementById('rect-questions');
  const stepEl = document.createElement('div');
  stepEl.className = 'rect-step';
  stepEl.id = `q-step-${rectState.questionIdx}`;
  stepEl.innerHTML = `
    <div class="rect-q">
      <div class="q-text">Q${rectState.questionIdx + 1}: ${q}</div>
      <div class="answer-btns">
        <button class="answer-btn yes" onclick="answerQ(true, ${rectState.questionIdx})">✓ 是的，我不是</button>
        <button class="answer-btn no"  onclick="answerQ(false, ${rectState.questionIdx})">✗ 不對，我是</button>
      </div>
    </div>
  `;
  qContainer.appendChild(stepEl);
}

function answerQ(isVN, qIdx) {
  if (!rectState || rectState.questionIdx !== qIdx) return;

  // Disable buttons for this question
  const stepEl = document.getElementById(`q-step-${qIdx}`);
  stepEl.querySelectorAll('.answer-btn').forEach(b => b.disabled = true);

  // Narrow window: each answer reduces window by ~60 min (from one side)
  const reduction = 60;
  rectState.halfWindow = Math.max(30, rectState.halfWindow - reduction / 2);
  if (isVN) {
    rectState.center = rectState.center + 15; // shift center slightly forward
  } else {
    rectState.center = rectState.center - 15; // shift center slightly backward
  }
  rectState.confidence = Math.min(0.95, rectState.confidence + 0.10);
  rectState.questionIdx++;

  // Update display in step
  const windowStart = minutesToHHMM(rectState.center - rectState.halfWindow);
  const windowEnd   = minutesToHHMM(rectState.center + rectState.halfWindow);
  const qDiv = stepEl.querySelector('.rect-q');
  qDiv.innerHTML = `
    <div class="q-text">Q${qIdx + 1}: ${VIA_NEGATIVA_QUESTIONS[qIdx]}
      <span style="color:${isVN?'#6ee7b7':'#fca5a5'}">${isVN ? '✓ 是的，我不是' : '✗ 不對，我是'}</span>
    </div>
    <div class="q-window">視窗縮小至: ${windowStart} ～ ${windowEnd}（${Math.round(rectState.halfWindow * 2)} 分鐘）</div>
    <div class="q-conf">Confidence: ${rectState.confidence.toFixed(2)}</div>
  `;

  // Update confidence bar
  const confFill = document.getElementById('conf-fill');
  if (confFill) confFill.style.width = `${rectState.confidence * 100}%`;
  const confLabel = confFill?.parentElement?.previousElementSibling;
  if (confLabel) confLabel.textContent = `Confidence: ${rectState.confidence.toFixed(2)}`;

  showNextQuestion();
}

function showRectResult() {
  if (!rectState) return;
  const { preciseMinutes, center, halfWindow, confidence } = rectState;
  const winStart = center - halfWindow;
  const winEnd   = center + halfWindow;
  const isWithin = preciseMinutes >= winStart && preciseMinutes <= winEnd;

  const finalEl = document.getElementById('rect-final');
  finalEl.innerHTML = `
    <div class="rect-result ${isWithin ? 'pass' : 'fail'}" style="margin-top:16px">
      <div style="font-weight:bold;margin-bottom:6px">${isWithin ? '✅ PASS — 校時模擬成功' : '❌ FAIL — 真實時間落在視窗外'}</div>
      <div>最終視窗: ${minutesToHHMM(winStart)} ～ ${minutesToHHMM(winEnd)}（${Math.round(halfWindow * 2)} 分鐘）</div>
      <div>Ground Truth: ${minutesToHHMM(preciseMinutes)}</div>
      <div>最終 Confidence: ${confidence.toFixed(2)}</div>
      ${isWithin ? `<div style="margin-top:4px;font-size:10px">精確時間在視窗內，置信度 ${confidence >= 0.80 ? '≥ 0.80 → 可鎖定' : '< 0.80 → 需更多問題'}。</div>` : `<div style="margin-top:4px;font-size:10px">建議：檢查問題設計或調整視窗縮小策略。</div>`}
    </div>
  `;
}
</script>
</body>
</html>
```

**Step 2: Manual verification**

1. Start astro-service: `cd astro-service && uvicorn main:app --port 8001`
2. Open `astro-service/sandbox.html` directly in Chrome/Edge (file://)
3. Check browser console for errors (F12)
4. Fill in default values and click **▶ Run Match**
5. Verify results panel appears with VibeScore, ChemistryScore, tracks, MATCH/MISMATCH badge

**Step 3: Commit**

```bash
git add astro-service/sandbox.html
git commit -m "feat: add sandbox.html Mechanism A (partner validation) + Mechanism B (rectification sim)"
```

---

## Task 4: Set ANTHROPIC_API_KEY and Validate End-to-End

**Files:**
- Check: `astro-service/.gitignore` (ensure `.env` is excluded)

**Step 1: Verify .gitignore excludes .env**

Check `astro-service/.gitignore`. If it doesn't exist or doesn't have `.env`:
```bash
# Add .env to astro-service gitignore
echo ".env" >> astro-service/.gitignore
```

**Step 2: Set ANTHROPIC_API_KEY in environment before starting service**

The user running the sandbox sets the key in their shell. Do NOT commit any key to the repo.
```bash
# Option A: set in shell before uvicorn
export ANTHROPIC_API_KEY=sk-ant-...
cd astro-service
uvicorn main:app --port 8001

# Option B: create a local .env (not committed)
# echo "ANTHROPIC_API_KEY=sk-ant-..." > astro-service/.env
# Then load it: source astro-service/.env && uvicorn main:app --port 8001
```

**Step 3: Test /generate-archetype endpoint directly**

```bash
curl -s -X POST http://localhost:8001/generate-archetype \
  -H "Content-Type: application/json" \
  -d '{
    "match_data": {
      "lust_score": 82, "soul_score": 71,
      "primary_track": "passion", "quadrant": "lover",
      "labels": ["✦ 激情型連結"],
      "tracks": {"friend": 45, "passion": 78, "partner": 62, "soul": 55},
      "power": {"rpv": 25, "frame_break": false, "viewer_role": "Dom", "target_role": "Sub"}
    },
    "person_a_name": "Alice",
    "person_b_name": "Bob"
  }' | python -m json.tool
```
Expected: JSON with `archetype_tags` (3 items) and `report` (non-empty string)

**Step 4: Full end-to-end in browser**

1. Open sandbox.html, fill in two people's birth data
2. Click ▶ Run Match → verify scores appear
3. Click ✦ Generate → verify archetype tags + report appear
4. Switch to Tab B → enter birth time → simulate rectification → verify PASS/FAIL

**Step 5: Run all tests one final time**

```bash
cd astro-service
pytest test_chart.py test_matching.py test_sandbox.py -v
```
Expected: 73 tests PASS

**Step 6: Update MVP-PROGRESS.md**

Add to `docs/MVP-PROGRESS.md` under completed items:
```
✅ Algorithm Validation Sandbox — astro-service/sandbox.html
   - Mechanism A: partner validation (positive control)
   - Mechanism B: birth time rectification simulation
   - /generate-archetype endpoint (Claude API proxy)
```

**Step 7: Final commit**

```bash
git add astro-service/.gitignore docs/MVP-PROGRESS.md
git commit -m "chore: add sandbox validation tooling — .gitignore + progress update"
```

---

## Task 5: Add /generate-profile-card Endpoint

**Purpose:** Generate a dating-app-style personal profile card from a single user's astrological + RPV data. Plain language, no hard astrology jargon.

**Files:**
- Modify: `astro-service/main.py` (append model + endpoint)
- Modify: `astro-service/test_sandbox.py` (add test)
- Modify: `astro-service/sandbox.html` (add Tab C with single-person form + output)

**Step 1: Write the failing test**

Add to `astro-service/test_sandbox.py`:
```python
def test_generate_profile_card_returns_card():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='{"headline": "探索者型", "tags": ["直覺敏銳","情感深度","喜歡安靜的驚喜"], "bio": "你是那種...", "vibe_keywords": ["神秘","溫柔","獨立"]}')]

    with patch("main.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_msg

        resp = client.post("/generate-profile-card", json={
            "chart_data": {
                "sun_sign": "gemini", "moon_sign": "pisces", "bazi_element": "wood",
                "data_tier": 1
            },
            "rpv_data": {"rpv_conflict": "cold_war", "rpv_power": "control", "rpv_energy": "home"},
            "attachment_style": "anxious",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "headline" in data
    assert "tags" in data
    assert "bio" in data
    assert "vibe_keywords" in data
    assert len(data["tags"]) >= 3
```

**Step 2: Run test to verify it fails**

```bash
cd astro-service
pytest test_sandbox.py::test_generate_profile_card_returns_card -v
```
Expected: FAIL

**Step 3: Add to main.py**

Append after `/generate-archetype` endpoint:

```python
PROFILE_CARD_PROMPT = """\
你是一個精通心理學與占星八字的現代交友顧問。請根據以下使用者的命理特徵參數，生成一份適合在交友軟體上展示的個人名片。
文案需要生活化、有吸引力，絕對不要使用生硬的算命術語（如：食神、七殺、刑沖剋害），請轉化為白話的性格描述。

使用者特徵：
- 太陽星座: {sun_sign}
- 月亮星座: {moon_sign}
- 上升星座: {ascendant_sign}
- 八字日主五行: {bazi_element}
- 依戀風格: {attachment_style}
- 衝突處理: {rpv_conflict}
- 權力偏好: {rpv_power}
- 能量模式: {rpv_energy}

請只回傳以下 JSON 格式，不要包含任何其他文字：
{{
  "headline": "3-6字的人格標題（例如：靈魂探索者、溫柔颶風）",
  "tags": ["標籤1", "標籤2", "標籤3", "標籤4"],
  "bio": "約80字的交友自介，第一人稱，生活化，有個性",
  "vibe_keywords": ["氛圍詞1", "氛圍詞2", "氛圍詞3"]
}}
"""

class ProfileCardRequest(BaseModel):
    chart_data: dict
    rpv_data: dict
    attachment_style: str = "secure"
    person_name: str = "User"

@app.post("/generate-profile-card")
def generate_profile_card(req: ProfileCardRequest):
    """Generate a dating-app profile card via Claude API."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")

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
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Add Tab C to sandbox.html**

Find the closing `</div><!-- end tab-b -->` line and add after it:

```html
<!-- ═══ TAB C ═══ -->
<div id="tab-c" class="tab-content">
  <div class="mech-b-card" style="max-width:480px">
    <h3>個人名片生成器</h3>
    <p style="color:#6b7280;font-size:11px;margin-bottom:12px">
      輸入單人星盤資料，生成交友軟體風格的個人名片。
    </p>
    <div class="field"><label>出生日期</label><input type="date" id="pc_date" value="1990-03-15"></div>
    <div class="field"><label>出生時間（可留空）</label><input type="time" id="pc_time" value="14:30"></div>
    <div class="field lat-lng">
      <div><label>緯度</label><input type="number" id="pc_lat" value="25.033" step="0.001"></div>
      <div><label>經度</label><input type="number" id="pc_lng" value="121.565" step="0.001"></div>
    </div>
    <div class="field"><label>RPV 衝突</label>
      <select id="pc_conflict"><option value="cold_war">冷戰</option><option value="argue">開吵</option></select>
    </div>
    <div class="field"><label>RPV 權力</label>
      <select id="pc_power"><option value="control">主導</option><option value="follow">跟隨</option></select>
    </div>
    <div class="field"><label>RPV 能量</label>
      <select id="pc_energy"><option value="home">宅</option><option value="out">外出</option></select>
    </div>
    <div class="field"><label>依戀風格</label>
      <select id="pc_attach">
        <option value="secure">安全型</option>
        <option value="anxious">焦慮型</option>
        <option value="avoidant">迴避型</option>
      </select>
    </div>
    <div style="margin-top:12px">
      <button class="btn" onclick="generateProfileCard()">✦ 生成個人名片</button>
      <span id="pc_status" class="loading" style="margin-left:8px"></span>
    </div>
    <div id="pc_output" style="margin-top:16px"></div>
  </div>
</div><!-- end tab-c -->
```

Also update the tab bar HTML to add Tab C button:
```html
<!-- Replace the two-button tab bar with: -->
<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('a')">Mechanism A — 伴侶驗證</button>
  <button class="tab-btn" onclick="switchTab('b')">Mechanism B — 校時模擬</button>
  <button class="tab-btn" onclick="switchTab('c')">個人名片生成</button>
  <button class="tab-btn" onclick="switchTab('d')">雙人合盤報告</button>
</div>
```

Also update `switchTab()` JS function to handle 4 tabs:
```javascript
function switchTab(id) {
  const ids = ['a','b','c','d'];
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', ids[i] === id));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
}
```

Add `generateProfileCard()` JS function:
```javascript
async function generateProfileCard() {
  const status = document.getElementById('pc_status');
  const out = document.getElementById('pc_output');
  status.textContent = '計算星盤中...';
  out.innerHTML = '';

  try {
    const date = document.getElementById('pc_date').value;
    const time = document.getElementById('pc_time').value;
    const lat  = parseFloat(document.getElementById('pc_lat').value);
    const lng  = parseFloat(document.getElementById('pc_lng').value);

    const chartBody = { birth_date: date, lat, lng, data_tier: time ? 1 : 3 };
    if (time) { chartBody.birth_time_exact = time; chartBody.birth_time = 'precise'; }

    const cr = await fetch(`${BASE}/calculate-chart`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(chartBody)
    });
    if (!cr.ok) throw new Error(await cr.text());
    const chart = await cr.json();

    status.textContent = '生成名片中...';
    const r = await fetch(`${BASE}/generate-profile-card`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        chart_data: chart,
        rpv_data: {
          rpv_conflict: document.getElementById('pc_conflict').value,
          rpv_power:    document.getElementById('pc_power').value,
          rpv_energy:   document.getElementById('pc_energy').value,
        },
        attachment_style: document.getElementById('pc_attach').value,
      })
    });
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || r.statusText); }
    const data = await r.json();

    const tagsHtml = (data.tags || []).map(t => `<span class="label-tag">${t}</span>`).join('');
    const vibeHtml = (data.vibe_keywords || []).map(t => `<span class="archetype-tag">${t}</span>`).join('');
    out.innerHTML = `
      <div style="background:#0f172a;border:1px solid #7c3aed;border-radius:10px;padding:16px">
        <div style="color:#c084fc;font-size:16px;font-weight:bold;margin-bottom:8px">${data.headline || ''}</div>
        <div class="labels-row" style="margin-bottom:8px">${tagsHtml}</div>
        <div class="report-text" style="margin-bottom:10px">${data.bio || ''}</div>
        <div style="color:#6b7280;font-size:10px;margin-bottom:4px">氛圍關鍵字</div>
        <div class="archetype-tags">${vibeHtml}</div>
      </div>
    `;
    status.textContent = '';
  } catch(e) {
    out.innerHTML = `<div class="error-msg">Error: ${e.message}</div>`;
    status.textContent = '';
  }
}
```

**Step 5: Run tests**

```bash
cd astro-service
pytest test_sandbox.py -v
```
Expected: 3 tests PASS

**Step 6: Commit**

```bash
git add astro-service/main.py astro-service/test_sandbox.py astro-service/sandbox.html
git commit -m "feat: add /generate-profile-card endpoint + Tab C in sandbox"
```

---

## Task 6: Add /generate-match-report Endpoint

**Purpose:** Full synastry relationship report — 閃光點 (high-score items), 潛在雷區 (low-score items), 相處建議 (advice). Uses match + chart data from both people.

**Files:**
- Modify: `astro-service/main.py` (append model + endpoint)
- Modify: `astro-service/test_sandbox.py` (add test)
- Modify: `astro-service/sandbox.html` (add Tab D + button in Mechanism A results)

**Step 1: Write the failing test**

Add to `astro-service/test_sandbox.py`:
```python
def test_generate_match_report_returns_report():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='{"title": "激情型連結", "sparks": ["靈魂共鳴深度", "互補的能量流動"], "landmines": ["控制慾張力"], "advice": "保持各自空間，定期深度對話。", "one_liner": "你們是彼此的鏡子，也是彼此的火焰。"}')]

    with patch("main.anthropic_client") as mock_client:
        mock_client.messages.create.return_value = mock_msg

        resp = client.post("/generate-match-report", json={
            "match_data": SAMPLE_MATCH_DATA,
            "person_a_name": "Alice",
            "person_b_name": "Bob",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "title" in data
    assert "sparks" in data
    assert "landmines" in data
    assert "advice" in data
    assert "one_liner" in data
    assert len(data["sparks"]) >= 1
```

**Step 2: Run test to verify it fails**

```bash
cd astro-service
pytest test_sandbox.py::test_generate_match_report_returns_report -v
```
Expected: FAIL

**Step 3: Add to main.py**

Append after `/generate-profile-card` endpoint:

```python
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

@app.post("/generate-match-report")
def generate_match_report(req: MatchReportRequest):
    """Generate a full synastry relationship report via Claude API."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")

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
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {raw[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Add Tab D to sandbox.html**

Add after `</div><!-- end tab-c -->`:

```html
<!-- ═══ TAB D ═══ -->
<div id="tab-d" class="tab-content">
  <div class="mech-b-card" style="max-width:560px">
    <h3>雙人合盤報告生成器</h3>
    <p style="color:#6b7280;font-size:11px;margin-bottom:12px">
      先在 Mechanism A 跑完合盤，再回到此頁生成完整關係報告。<br>
      或直接填入分數手動觸發。
    </p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
      <div class="field"><label>Person A 名字</label><input type="text" id="mr_name_a" value="Person A"></div>
      <div class="field"><label>Person B 名字</label><input type="text" id="mr_name_b" value="Person B"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
      <div class="field"><label>VibeScore (lust)</label><input type="number" id="mr_lust" value="75" min="0" max="100"></div>
      <div class="field"><label>ChemistryScore (soul)</label><input type="number" id="mr_soul" value="68" min="0" max="100"></div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px">
      <div class="field"><label>friend</label><input type="number" id="mr_friend" value="45" min="0" max="100"></div>
      <div class="field"><label>passion</label><input type="number" id="mr_passion" value="72" min="0" max="100"></div>
      <div class="field"><label>partner</label><input type="number" id="mr_partner" value="60" min="0" max="100"></div>
      <div class="field"><label>soul</label><input type="number" id="mr_soul_t" value="55" min="0" max="100"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px">
      <div class="field"><label>primary_track</label>
        <select id="mr_primary"><option>passion</option><option>partner</option><option>friend</option><option>soul</option></select>
      </div>
      <div class="field"><label>quadrant</label>
        <select id="mr_quad"><option>lover</option><option>soulmate</option><option>partner</option><option>colleague</option></select>
      </div>
      <div class="field"><label>RPV</label><input type="number" id="mr_rpv" value="25"></div>
    </div>
    <div>
      <button class="btn" onclick="fillFromLastMatch()">← 從上次合盤填入</button>
      <button class="btn" style="margin-left:8px" onclick="generateMatchReport()">✦ 生成合盤報告</button>
      <span id="mr_status" class="loading" style="margin-left:8px"></span>
    </div>
    <div id="mr_output" style="margin-top:16px"></div>
  </div>
</div><!-- end tab-d -->
```

Add corresponding JS functions:
```javascript
function fillFromLastMatch() {
  if (!window._lastMatchData) { alert('請先在 Mechanism A 跑完合盤'); return; }
  const md = window._lastMatchData;
  document.getElementById('mr_lust').value    = md.lust_score.toFixed(0);
  document.getElementById('mr_soul').value    = md.soul_score.toFixed(0);
  document.getElementById('mr_friend').value  = md.tracks.friend.toFixed(0);
  document.getElementById('mr_passion').value = md.tracks.passion.toFixed(0);
  document.getElementById('mr_partner').value = md.tracks.partner.toFixed(0);
  document.getElementById('mr_soul_t').value  = md.tracks.soul.toFixed(0);
  document.getElementById('mr_rpv').value     = md.power.rpv;
  document.getElementById('mr_primary').value = md.primary_track;
  document.getElementById('mr_quad').value    = md.quadrant;
  document.getElementById('mr_name_a').value  = window._lastNameA || 'A';
  document.getElementById('mr_name_b').value  = window._lastNameB || 'B';
}

async function generateMatchReport() {
  const status = document.getElementById('mr_status');
  const out    = document.getElementById('mr_output');
  status.textContent = '生成報告中...';
  out.innerHTML = '';

  const matchData = {
    lust_score:    parseFloat(document.getElementById('mr_lust').value),
    soul_score:    parseFloat(document.getElementById('mr_soul').value),
    primary_track: document.getElementById('mr_primary').value,
    quadrant:      document.getElementById('mr_quad').value,
    labels:        [],
    tracks: {
      friend:  parseFloat(document.getElementById('mr_friend').value),
      passion: parseFloat(document.getElementById('mr_passion').value),
      partner: parseFloat(document.getElementById('mr_partner').value),
      soul:    parseFloat(document.getElementById('mr_soul_t').value),
    },
    power: {
      rpv: parseFloat(document.getElementById('mr_rpv').value),
      frame_break: false,
      viewer_role: 'Equal', target_role: 'Equal',
    },
  };
  if (window._lastMatchData) {
    matchData.labels = window._lastMatchData.labels || [];
    matchData.power  = window._lastMatchData.power  || matchData.power;
  }

  try {
    const r = await fetch(`${BASE}/generate-match-report`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        match_data: matchData,
        person_a_name: document.getElementById('mr_name_a').value,
        person_b_name: document.getElementById('mr_name_b').value,
      })
    });
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || r.statusText); }
    const data = await r.json();

    const sparksHtml    = (data.sparks    || []).map(s => `<li style="color:#6ee7b7">✦ ${s}</li>`).join('');
    const landminesHtml = (data.landmines || []).map(s => `<li style="color:#fca5a5">⚡ ${s}</li>`).join('');

    out.innerHTML = `
      <div style="background:#0f172a;border:1px solid #7c3aed;border-radius:10px;padding:16px">
        <div style="color:#c084fc;font-size:15px;font-weight:bold;margin-bottom:12px">${data.title || ''}</div>
        <div style="font-style:italic;color:#a78bfa;font-size:12px;margin-bottom:14px;padding:8px;background:#1e1b4b;border-radius:6px">"${data.one_liner || ''}"</div>
        <div style="margin-bottom:10px">
          <div style="color:#34d399;font-size:11px;margin-bottom:4px">✦ 閃光點</div>
          <ul style="list-style:none;font-size:12px;line-height:2">${sparksHtml}</ul>
        </div>
        <div style="margin-bottom:10px">
          <div style="color:#f87171;font-size:11px;margin-bottom:4px">⚡ 成長課題</div>
          <ul style="list-style:none;font-size:12px;line-height:2">${landminesHtml}</ul>
        </div>
        <div>
          <div style="color:#6b7280;font-size:11px;margin-bottom:4px">相處建議</div>
          <div class="report-text">${data.advice || ''}</div>
        </div>
      </div>
    `;
    status.textContent = '';
  } catch(e) {
    out.innerHTML = `<div class="error-msg">Error: ${e.message}</div>`;
    status.textContent = '';
  }
}
```

**Step 5: Run all tests**

```bash
cd astro-service
pytest test_sandbox.py -v
```
Expected: 4 tests PASS

**Step 6: Run full test suite**

```bash
cd astro-service
pytest test_chart.py test_matching.py test_sandbox.py -v
```
Expected: 75 tests PASS (71 + 4 new)

**Step 7: Commit**

```bash
git add astro-service/main.py astro-service/test_sandbox.py astro-service/sandbox.html
git commit -m "feat: add /generate-match-report endpoint + Tab D in sandbox"
```

---

## Quick Reference: Running the Sandbox

```bash
# Terminal 1: start astro-service
export ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
cd astro-service
uvicorn main:app --port 8001

# Then: open astro-service/sandbox.html in browser
```

That's it. No Next.js needed.

---

## Validation Test Cases to Run Manually

After building, test these cases to validate the algorithm:

| Test | Person A | Person B | ground_truth | Expected |
|---|---|---|---|---|
| T01 | Any stable couple | same | 已婚（穩定）| MATCH (soul ≥ 65, partner/soul track) |
| T02 | Known bad breakup | same | 已分手（慘烈）| MATCH (avg ≤ 55) |
| T03 | Lifelong friends | same | 萬年好友 | MATCH (friend track primary, lust ≤ 60) |
| T04 | Rectification sim | time=14:30 | — | PASS (time within final window) |
