# Synastry Prompt v2 — Profile Injection + 4-Bug Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Inject per-person psychological profiles into the synastry LLM prompt so `reality_check` can produce specific "A's need collides with B's fear" content instead of generic Barnum-effect filler.

**Architecture:** Four coordinated changes — (1) fix the `_MATCH_ARCHETYPE_SCHEMA` constant and `get_match_report_prompt` in `prompt_manager.py` to accept optional profile dicts and remove four known defects; (2) add `get_or_compute_psychology_profile()` to `db_client.py` (cache-first, compute-on-miss); (3) thread profiles through the `/api/matches/compute` pipeline in `main.py`; (4) add `--synastry` mode to `run_ideal_match_prompt.py` so CLI test output automatically includes profiles.

**Tech Stack:** Python 3.9+, FastAPI, `ideal_avatar.extract_ideal_partner_profile()`, Supabase `user_psychology_profiles` table (migration 014 already applied), `pytest`.

---

## Context for the implementer

### The four bugs in the current `get_match_report_prompt`

| # | Bug | Location | Fix |
|---|-----|----------|-----|
| 1 | **Duplicate task block** | `prompt_manager.py:352-354` hardcodes a `【本次任務：雙人宿命深度破防解析 (塔羅牌模式)】` block that conflicts with the `instruction` variable already injected from `_SOUL_INSTRUCTION` | Delete the hardcoded block |
| 2 | **No anti-Barnum formula for `reality_check`** | `_MATCH_ARCHETYPE_SCHEMA` line 308 | Replace with forced formula: "A的具體需求 撞上 B的具體恐懼" |
| 3 | **RPV not explained** | Prompt shows `RPV=0.0` with no definition | Add Python-side translation: if `rpv > 20` → "某方處於明顯高位"; else → "勢均力敵" |
| 4 | **UI markup in JSON values** | `_MATCH_ARCHETYPE_SCHEMA` has `"一、初見面..."`, `"二、權力..."`, `"❌"`, `"👉"` | Remove all emoji/numbering from JSON schema string |

### Key files

- `astro-service/prompt_manager.py` — All prompt logic, `_MATCH_ARCHETYPE_SCHEMA` at line 302, `get_match_report_prompt` at line 314
- `astro-service/db_client.py` — Supabase wrappers; `get_psychology_profile(user_id)` at line 89, `upsert_psychology_profile(user_id, profile)` at line 70
- `astro-service/main.py` — FastAPI app; `/api/matches/compute` endpoint at line 500, `build_synastry_report_prompt` called at line 572
- `astro-service/run_ideal_match_prompt.py` — CLI test runner, `build_natal_report()` at line 61
- `astro-service/ideal_avatar.py` — `extract_ideal_partner_profile(western_chart, bazi_chart, zwds_chart, psychology_data=None)` at line 524; returns dict with keys: `psychological_needs` (List[str]), `relationship_dynamic` (str), `favorable_elements` (List[str]), etc.
- `astro-service/test_prompt_manager.py` — Existing tests for `get_ideal_match_prompt` only

### DB note

`user_psychology_profiles` table (migration 014) already exists with columns: `user_id`, `relationship_dynamic`, `psychological_needs`, `favorable_elements`, `dominant_elements`, `karmic_boss`, `llm_natal_report`. The `get_psychology_profile` / `upsert_psychology_profile` functions in `db_client.py` are already written and working — you just need to add a `get_or_compute_psychology_profile` wrapper.

---

## Task 1: Fix `_MATCH_ARCHETYPE_SCHEMA` — remove UI markup, add anti-Barnum

**Files:**
- Modify: `astro-service/prompt_manager.py:302-311`
- Test: `astro-service/test_prompt_manager.py`

**Step 1: Write the failing test**

Add to `test_prompt_manager.py`:

```python
from prompt_manager import get_match_report_prompt, _MATCH_ARCHETYPE_SCHEMA

def test_schema_has_no_ui_markup():
    """JSON schema must not contain emoji or numbered list prefixes."""
    assert "❌" not in _MATCH_ARCHETYPE_SCHEMA
    assert "👉" not in _MATCH_ARCHETYPE_SCHEMA
    assert "一、" not in _MATCH_ARCHETYPE_SCHEMA
    assert "二、" not in _MATCH_ARCHETYPE_SCHEMA
    assert "五、" not in _MATCH_ARCHETYPE_SCHEMA

def test_schema_has_anti_barnum_formula():
    """reality_check description must include the A撞B formula."""
    assert "A的" in _MATCH_ARCHETYPE_SCHEMA or "User A" in _MATCH_ARCHETYPE_SCHEMA
    assert "B的" in _MATCH_ARCHETYPE_SCHEMA or "User B" in _MATCH_ARCHETYPE_SCHEMA
```

**Step 2: Run test to verify it fails**

```bash
cd astro-service && pytest test_prompt_manager.py::test_schema_has_no_ui_markup test_prompt_manager.py::test_schema_has_anti_barnum_formula -v
```

Expected: FAIL — `AssertionError` because `❌` and `一、` currently exist in the schema.

**Step 3: Replace `_MATCH_ARCHETYPE_SCHEMA` at line 302**

Find and replace the entire constant (lines 302–311):

```python
_MATCH_ARCHETYPE_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "archetype_tags": ["兩個英文單字代表關係原型(如: Fatal_Attraction)", "第二個tag"],
  "resonance": "用2到3句話(約60字)，點出兩人初見面的致命引力。具體描繪是肉體費洛蒙的衝擊，還是靈魂深處的熟悉感。",
  "shadow": "用2到3句話(約60字)，解析他們在關係中的權力動態與失控深淵。根據 RPV 值判斷誰掌握絕對話語權，或是誰的愛會讓另一方感到窒息。",
  "reality_check": [
    "第一道會痛的關卡（約20字，嚴格套用『User A 的具體需求，撞上 User B 的具體恐懼/雷區』之公式，禁止寫通用廢話如溝通不良、脾氣差）",
    "第二道會痛的關卡（約20字，描述具體的日常摩擦或價值觀死穴）",
    "第三道會痛的關卡（約20字）"
  ],
  "evolution": [
    "第一帖專屬解藥（約15字，給予突破業力或現實摩擦的具體行動建議）",
    "第二帖專屬解藥（約15字）",
    "第三帖專屬解藥（約15字）"
  ],
  "core": "用一句話（約40字）總結這段緣分的終極意義，作為極具震撼力與宿命感的命運箴言。"
}"""
```

**Step 4: Run tests to verify they pass**

```bash
cd astro-service && pytest test_prompt_manager.py::test_schema_has_no_ui_markup test_prompt_manager.py::test_schema_has_anti_barnum_formula -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add astro-service/prompt_manager.py astro-service/test_prompt_manager.py
git commit -m "fix(prompt): remove UI markup from _MATCH_ARCHETYPE_SCHEMA, add anti-Barnum formula"
```

---

## Task 2: Fix `get_match_report_prompt` — remove duplicate task block + add RPV explanation + profile params

**Files:**
- Modify: `astro-service/prompt_manager.py:314-373`
- Test: `astro-service/test_prompt_manager.py`

**Step 1: Write the failing tests**

Add to `test_prompt_manager.py`:

```python
def _match_data():
    return {
        "lust_score": 30,
        "soul_score": 80,
        "tracks": {"friend": 40, "passion": 30, "partner": 50, "soul": 80},
        "primary_track": "soul",
        "quadrant": "partner",
        "power": {"viewer_role": "Equal", "target_role": "Equal", "rpv": 0.0, "frame_break": False},
        "high_voltage": False,
        "psychological_tags": [],
        "zwds": {},
    }

def test_no_duplicate_task_block():
    """Only one 【本次任務】 block should appear in the final prompt."""
    prompt, _ = get_match_report_prompt(_match_data())
    assert prompt.count("【本次任務") == 1

def test_rpv_explained_in_prompt():
    """Prompt should translate RPV value into human-readable power description."""
    prompt, _ = get_match_report_prompt(_match_data())
    # For rpv=0.0 should show equal balance text
    assert "勢均力敵" in prompt or "Equal" in prompt

def test_rpv_high_value_explained():
    """RPV > 20 should translate to high-position description."""
    data = _match_data()
    data["power"]["rpv"] = 35.0
    prompt, _ = get_match_report_prompt(data)
    assert "高位" in prompt or "35" in prompt

def test_profile_injection_when_provided():
    """When profiles are provided, they appear in the prompt."""
    prof_a = {"psychological_needs": ["極度需要秩序", "無法忍受計畫被打破"], "relationship_dynamic": "stable"}
    prof_b = {"psychological_needs": ["需要思想自由", "討厭被框架綁死"], "relationship_dynamic": "high_voltage"}
    prompt, _ = get_match_report_prompt(_match_data(), user_a_profile=prof_a, user_b_profile=prof_b)
    assert "極度需要秩序" in prompt
    assert "需要思想自由" in prompt

def test_no_profile_injection_when_absent():
    """When profiles are absent, prompt is still valid (backward compat)."""
    prompt, _ = get_match_report_prompt(_match_data())
    assert "雙方心理結構" not in prompt
```

**Step 2: Run tests to verify they fail**

```bash
cd astro-service && pytest test_prompt_manager.py::test_no_duplicate_task_block test_prompt_manager.py::test_rpv_explained_in_prompt test_prompt_manager.py::test_rpv_high_value_explained test_prompt_manager.py::test_profile_injection_when_provided test_prompt_manager.py::test_no_profile_injection_when_absent -v
```

Expected: multiple FAIL (duplicate task block exists, RPV not translated, profile params don't exist yet).

**Step 3: Rewrite `get_match_report_prompt` (lines 314–373)**

Replace the entire function with:

```python
def get_match_report_prompt(
    match_data: dict,
    mode: str = "auto",
    person_a: str = "User A",
    person_b: str = "User B",
    user_a_profile: dict = None,
    user_b_profile: dict = None,
) -> tuple[str, str]:
    """
    Build a DESTINY-worldview-enriched prompt for pairwise AI analysis (Tab A).

    Parameters
    ----------
    match_data        : output of compute_match_v2()
    mode              : "auto" | "abyss" | "hunt" | "nest" | "friend"
    person_a / person_b : display labels (default "User A" / "User B")
    user_a_profile    : dict from extract_ideal_partner_profile() for person A.
                        Keys used: psychological_needs (List[str]), relationship_dynamic (str)
    user_b_profile    : same for person B.
                        When either is None the profile injection block is skipped.

    Returns
    -------
    (prompt, effective_mode)
    """
    effective_mode = _pick_mode(match_data, mode)
    instruction = _INSTRUCTION_MAP.get(effective_mode, _SOUL_INSTRUCTION)

    tracks = match_data.get("tracks", {})
    power  = match_data.get("power", {})
    zwds   = match_data.get("zwds") or {}
    psych_tags   = match_data.get("psychological_tags", [])
    high_voltage = match_data.get("high_voltage", False)
    ep_a = match_data.get("element_profile_a")
    ep_b = match_data.get("element_profile_b")

    # RPV human-readable translation (Bug #3 fix)
    rpv_val = float(power.get("rpv", 0.0))
    if rpv_val > 20:
        power_desc = (
            f"{person_a}={power.get('viewer_role', 'Equal')}，"
            f"{person_b}={power.get('target_role', 'Equal')}，"
            f"RPV={rpv_val}（差距顯著，某方在這段關係中處於明顯高位或被極度偏愛）"
        )
    else:
        power_desc = (
            f"{person_a}={power.get('viewer_role', 'Equal')}，"
            f"{person_b}={power.get('target_role', 'Equal')}，"
            f"RPV={rpv_val}（勢均力敵的博弈，雙方話語權接近）"
        )

    elem_context = ""
    if ep_a or ep_b:
        elem_context = (
            f"\n[八字與五行能量場]"
            f"\n{person_a} 能量: {_element_summary(ep_a)}"
            f"\n{person_b} 能量: {_element_summary(ep_b)}"
        )

    # Individual psychology profile injection (new)
    profile_block = ""
    if user_a_profile and user_b_profile:
        a_needs = "、".join(user_a_profile.get("psychological_needs", [])) or "（未提供）"
        a_dyn   = user_a_profile.get("relationship_dynamic", "unknown")
        b_needs = "、".join(user_b_profile.get("psychological_needs", [])) or "（未提供）"
        b_dyn   = user_b_profile.get("relationship_dynamic", "unknown")
        profile_block = f"""
【雙方心理結構（Reality Check 必須使用此素材）】
[{person_a}]
- 核心需求與恐懼：{a_needs}
- 關係動態傾向：{a_dyn}

[{person_b}]
- 核心需求與恐懼：{b_needs}
- 關係動態傾向：{b_dyn}
"""

    prompt = f"""{DESTINY_WORLDVIEW}

{instruction}

【輸入數據 — {person_a} × {person_b}】
VibeScore（肉體費洛蒙張力）: {round(match_data.get('lust_score', 0), 1)}/100
ChemistryScore（靈魂共鳴深度）: {round(match_data.get('soul_score', 0), 1)}/100
四軌: 朋友={round(tracks.get('friend', 0), 1)} 激情={round(tracks.get('passion', 0), 1)} 伴侶(正緣)={round(tracks.get('partner', 0), 1)} 靈魂(業力)={round(tracks.get('soul', 0), 1)}
主要連結類型: {match_data.get('primary_track', 'unknown')}
四象限落點: {match_data.get('quadrant', 'unknown')}
權力動態: {power_desc}
框架崩潰 (理智斷線): {power.get('frame_break', False)}
高壓警告 (修羅場/禁忌感): {high_voltage}
紫微斗數烈度: {zwds.get('spiciness_level', 'N/A')}

【心理與業力分析結果（請將以下標籤轉譯為白話情境，禁止直接輸出原始英文標籤）】
{_translate_psych_tags(psych_tags)}{elem_context}
{profile_block}
【寫作嚴格規範】
- reality_check 中的每一條，必須基於上方【雙方心理結構】，套用「{person_a}的某項具體需求，撞上{person_b}的某項具體恐懼或雷區」的公式。
- 嚴禁寫「溝通不良、脾氣差、缺乏信任」等通用廢話——每個人都適用的句子等於沒寫。

{_MATCH_ARCHETYPE_SCHEMA}"""

    return prompt, effective_mode
```

**Step 4: Run tests to verify they pass**

```bash
cd astro-service && pytest test_prompt_manager.py -v
```

Expected: All 5 new tests + all prior tests PASS.

**Step 5: Commit**

```bash
git add astro-service/prompt_manager.py astro-service/test_prompt_manager.py
git commit -m "feat(prompt): add profile injection + RPV translation + remove duplicate task block"
```

---

## Task 3: Add `get_or_compute_psychology_profile()` to `db_client.py`

**Files:**
- Modify: `astro-service/db_client.py` (append after line 97)
- Test: `astro-service/test_prompt_manager.py` (or a new `test_db_client.py`)

**Context:** `get_psychology_profile(user_id)` already exists at line 89. `upsert_psychology_profile(user_id, profile)` already exists at line 70. `extract_ideal_partner_profile(western_chart, bazi_chart, zwds_chart)` is in `ideal_avatar.py`. The new function wraps them with cache-first logic.

**Step 1: Write the failing test**

Create `astro-service/test_db_client.py`:

```python
# -*- coding: utf-8 -*-
"""Tests for db_client.py helper functions that do NOT require Supabase."""
import pytest
from unittest.mock import patch, MagicMock


def test_get_or_compute_returns_cached_when_available():
    """If Supabase returns a profile, return it without calling extract_ideal_partner_profile."""
    cached = {"psychological_needs": ["安全感"], "relationship_dynamic": "stable"}
    with patch("db_client.get_psychology_profile", return_value=cached) as mock_get, \
         patch("db_client.upsert_psychology_profile") as mock_upsert:
        from db_client import get_or_compute_psychology_profile
        result = get_or_compute_psychology_profile("user-123", {})
        mock_get.assert_called_once_with("user-123")
        mock_upsert.assert_not_called()
        assert result == cached


def test_get_or_compute_computes_and_saves_on_miss():
    """If cache miss, call extract_ideal_partner_profile and save to DB."""
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
        mock_extract.assert_called_once()
        mock_upsert.assert_called_once_with("user-456", fake_profile)
        assert result == fake_profile


def test_get_or_compute_returns_empty_dict_on_exception():
    """Never crash even if Supabase is down; return {} gracefully."""
    with patch("db_client.get_psychology_profile", side_effect=RuntimeError("no supabase")):
        from db_client import get_or_compute_psychology_profile
        result = get_or_compute_psychology_profile("user-789", {})
        assert result == {}
```

**Step 2: Run test to verify it fails**

```bash
cd astro-service && pytest test_db_client.py -v
```

Expected: FAIL — `ImportError: cannot import name 'get_or_compute_psychology_profile'`.

**Step 3: Add the function to `db_client.py`** (after line 97, before the `# ── Match Results` section)

```python
def get_or_compute_psychology_profile(user_id: str, natal_data: dict) -> dict:
    """Return cached psychology profile from DB, or compute + cache it on miss.

    Parameters
    ----------
    user_id    : Supabase user UUID
    natal_data : dict with keys western_chart, bazi_chart, zwds_chart
                 (same shape as returned by db_client.get_natal_data)

    Returns
    -------
    dict — same shape as extract_ideal_partner_profile() output.
           Returns {} on any error so callers can safely fallback.
    """
    try:
        cached = get_psychology_profile(user_id)
        if cached:
            return cached

        from ideal_avatar import extract_ideal_partner_profile
        profile = extract_ideal_partner_profile(
            natal_data.get("western_chart", {}),
            natal_data.get("bazi_chart", {}),
            natal_data.get("zwds_chart", {}),
        )
        upsert_psychology_profile(user_id, profile)
        return profile
    except Exception:
        return {}
```

**Step 4: Run tests to verify they pass**

```bash
cd astro-service && pytest test_db_client.py -v
```

Expected: All 3 tests PASS.

**Step 5: Commit**

```bash
git add astro-service/db_client.py astro-service/test_db_client.py
git commit -m "feat(db): add get_or_compute_psychology_profile with cache-first pattern"
```

---

## Task 4: Thread profiles through `/api/matches/compute` in `main.py`

**Files:**
- Modify: `astro-service/main.py:500-595` (the `compute_match_cached` function)
- Also modify: `astro-service/prompt_manager.py` — update `build_synastry_report_prompt` signature

**Context:** The endpoint at line 500 (`/api/matches/compute`) currently:
1. Checks cache
2. Loads natal data
3. Flattens it
4. Calls `compute_match_v2`
5. Calls `build_synastry_report_prompt(raw_result)` (no profiles)
6. Sanitizes + caches result

You need to insert step 3.5 (load profiles) and update step 5 to pass them.

**Step 1: Update `build_synastry_report_prompt` signature in `prompt_manager.py`**

Find `def build_synastry_report_prompt(raw_match_data: dict) -> str:` at line 693. Add profile params and inject them before the `【寫作指南】` block:

```python
def build_synastry_report_prompt(
    raw_match_data: dict,
    user_a_profile: dict = None,
    user_b_profile: dict = None,
) -> str:
    """Build a safe LLM prompt for pairwise synastry report generation.
    ...
    """
    tension = raw_match_data.get("karmic_tension", 0)
    badges = raw_match_data.get("resonance_badges", [])
    tracks = raw_match_data.get("tracks", {})
    soul_score = tracks.get("soul", 0)
    partner_score = tracks.get("partner", 0)
    passion_score = tracks.get("passion", 0)
    friend_score = tracks.get("friend", 0)
    high_voltage = raw_match_data.get("high_voltage", False)
    quadrant = raw_match_data.get("quadrant", "unknown")
    psych_tags = raw_match_data.get("psychological_tags", [])

    psych_section = _translate_psych_tags(psych_tags)

    # Profile injection (same pattern as get_match_report_prompt)
    profile_block = ""
    if user_a_profile and user_b_profile:
        a_needs = "、".join(user_a_profile.get("psychological_needs", [])) or "（未提供）"
        a_dyn   = user_a_profile.get("relationship_dynamic", "unknown")
        b_needs = "、".join(user_b_profile.get("psychological_needs", [])) or "（未提供）"
        b_dyn   = user_b_profile.get("relationship_dynamic", "unknown")
        profile_block = f"""
【雙方心理結構（請據此寫出具體的現實碰撞，禁止使用通用廢話）】
[User A] 核心需求：{a_needs}｜關係傾向：{a_dyn}
[User B] 核心需求：{b_needs}｜關係傾向：{b_dyn}
"""

    prompt = f"""{DESTINY_WORLDVIEW}

【本次任務：雙人關係洞察報告生成】
你是一位榮格深度心理占星師。請根據以下演算法算出的「關係標籤」，為這對潛在伴侶寫一段 150 字的【關係洞察報告】。

【核心配對數據】：
- 靈魂共鳴度：{round(soul_score)} / 100（代表天生頻率契合度）
- 現實相處穩定度：{round(partner_score)} / 100（代表日常柴米油鹽的摩擦程度）
- 費洛蒙張力：{round(passion_score)} / 100（代表肉體與慾望的吸引力）
- 友誼默契度：{round(friend_score)} / 100（代表思維共振與溝通品質）
- 業力與張力指數：{round(tension)} / 100（分數越高，代表致命吸引力越強，但也越容易相愛相殺）
- 關係四象限落點：{quadrant}
- 高壓警告：{high_voltage}
- 關係特殊徽章：{', '.join(badges) if badges else '無'}

【心理動力學標籤（請轉譯為白話情境，禁止直接輸出原始標籤）】
{psych_section}
{profile_block}
【寫作指南】：
1. 如果「靈魂」高但「相處」低，請點出這是一段「深刻但需要磨合」的關係。
2. 如果「張力指數」大於 60，請務必警告他們這段關係帶有強烈的業力或致命吸引力，不要用平淡的語氣。
3. 如果有特殊徽章（如：完美互補、金火互溶），請用浪漫但深刻的語氣解釋這個徽章的意義。
4. 不要出現任何占星或八字專有名詞，請轉化為心理學與感情視角的白話文。
5. 控制在 150 字以內，語氣像一個極度懂他們的知己。
6. 直接回傳純文字，不要用 JSON 或 markdown 格式。"""

    return prompt
```

**Step 2: Update `/api/matches/compute` in `main.py`**

In the `compute_match_cached` function, after step 3 (`user_a = _flatten_natal(natal_a)`, line ~563), insert step 3.5:

```python
        # 3.5 Load or compute psychology profiles (non-blocking, cache-first)
        prof_a: dict = {}
        prof_b: dict = {}
        try:
            prof_a = db_client.get_or_compute_psychology_profile(req.user_a_id, natal_a)
            prof_b = db_client.get_or_compute_psychology_profile(req.user_b_id, natal_b)
        except Exception:
            pass  # Profile enrichment is non-critical; matching still works without it
```

Then update step 5 (line ~572, the `prompt = build_synastry_report_prompt(raw_result)` call):

```python
        # 5. Optional LLM report (with profiles)
        llm_report = ""
        if req.generate_report:
            try:
                prompt = build_synastry_report_prompt(raw_result, prof_a, prof_b)
                llm_report = call_llm(
                    prompt, provider=req.provider, max_tokens=400,
                    api_key=req.api_key, gemini_model=req.gemini_model,
                )
            except Exception:
                llm_report = ""
```

**Step 3: No test required for API endpoint** (integration test via manual curl is sufficient). Run the existing test suite to confirm nothing is broken:

```bash
cd astro-service && pytest test_prompt_manager.py test_db_client.py -v
```

Expected: All tests PASS.

**Step 4: Commit**

```bash
git add astro-service/prompt_manager.py astro-service/main.py
git commit -m "feat(api): thread psychology profiles through /api/matches/compute pipeline"
```

---

## Task 5: Add `--synastry` mode to `run_ideal_match_prompt.py`

**Files:**
- Modify: `astro-service/run_ideal_match_prompt.py`

**Context:** The script currently only does single-person natal reports. We need a `--synastry` flag that:
1. Takes a second person's birth data via `--date2`, `--time2`, `--gender2`
2. Calls the API for both persons
3. Computes profiles locally using `extract_ideal_partner_profile()` (no DB needed for CLI testing)
4. Calls `/compute-match` endpoint with both flattened profiles
5. Calls `get_match_report_prompt(match_data, user_a_profile=prof_a, user_b_profile=prof_b)`
6. Outputs the enriched synastry prompt to `synastry_output.txt`

**Step 1: Add imports and default constants** at the top of the file (after existing imports):

```python
from prompt_manager import get_ideal_match_prompt, get_match_report_prompt
try:
    from ideal_avatar import extract_ideal_partner_profile
    _HAS_IDEAL_AVATAR = True
except ImportError:
    _HAS_IDEAL_AVATAR = False
```

Also add defaults near the top:

```python
DEFAULT_DATE2   = "1995-03-26"
DEFAULT_TIME2   = "14:30"
DEFAULT_GENDER2 = "F"
```

**Step 2: Add a `build_synastry_prompt` function** (add before `main()`):

```python
def build_synastry_prompt(
    full_report_a: dict, chart_a: dict,
    full_report_b: dict, chart_b: dict,
) -> str:
    """Build enriched synastry prompt for two persons.

    Uses /compute-match endpoint for match scores, then injects
    individual psychology profiles from ideal_avatar.
    """
    # Flatten both charts for /compute-match
    flat_a = flatten_to_chart_data(full_report_a, chart_a)
    flat_b = flatten_to_chart_data(full_report_b, chart_b)

    # /compute-match expects flat dicts with sign keys at top level
    match_resp = call_api("/compute-match", {"user_a": flat_a, "user_b": flat_b})

    # Compute individual profiles locally (no DB required for CLI)
    prof_a: dict = {}
    prof_b: dict = {}
    if _HAS_IDEAL_AVATAR:
        try:
            prof_a = extract_ideal_partner_profile(
                full_report_a.get("western_astrology", {}).get("planets", {}),
                full_report_a.get("bazi", {}),
                full_report_a.get("zwds", {}),
            )
        except Exception:
            pass
        try:
            prof_b = extract_ideal_partner_profile(
                full_report_b.get("western_astrology", {}).get("planets", {}),
                full_report_b.get("bazi", {}),
                full_report_b.get("zwds", {}),
            )
        except Exception:
            pass

    # Build enriched prompt
    ident_a = full_report_a["ident"]
    ident_b = full_report_b["ident"]
    label_a = f"{ident_a['gender']}({ident_a['birth_date'][5:]})"   # e.g. "M(03-07)"
    label_b = f"{ident_b['gender']}({ident_b['birth_date'][5:]})"

    prompt, mode = get_match_report_prompt(
        match_resp,
        person_a=label_a,
        person_b=label_b,
        user_a_profile=prof_a,
        user_b_profile=prof_b,
    )
    return prompt
```

**Step 3: Add CLI args and synastry branch in `main()`**

Add to the `argparse` section:

```python
    parser.add_argument("--synastry",  action="store_true", help="合盤模式：輸出合盤 Prompt 到 synastry_output.txt")
    parser.add_argument("--date2",     default=DEFAULT_DATE2,  help="第二人出生日期 YYYY-MM-DD")
    parser.add_argument("--time2",     default=DEFAULT_TIME2,  help="第二人出生時間 HH:MM")
    parser.add_argument("--gender2",   default=DEFAULT_GENDER2, help="第二人性別 M / F")
```

Add synastry branch at the end of `main()`, after the existing single-person prompt section:

```python
    # ── Step 3 (optional): 合盤模式 ──────────────────────────────
    if args.synastry:
        if not args.copy_prompt:
            print(f"\n{SEP}")
            print(f"  合盤模式：排第二人 {args.date2} {args.time2} {'女' if args.gender2=='F' else '男'}")
            print(SEP)

        full_report_b, chart_b = build_natal_report(
            args.date2, args.time2, args.gender2, args.lat, args.lng
        )

        synastry_prompt = build_synastry_prompt(
            full_report, chart,
            full_report_b, chart_b,
        )

        # Write to file (avoids Windows encoding issues with emoji in terminal)
        out_path = os.path.join(os.path.dirname(__file__), "synastry_output.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(synastry_prompt)

        if args.copy_prompt:
            print(synastry_prompt)
        else:
            print(f"\n合盤 Prompt 已寫入 {out_path}")
            print(f"💡 只輸出 Prompt 文字：py -3.12 run_ideal_match_prompt.py --synastry --copy-prompt")
        return
```

**Step 4: Manual smoke test**

With `astro-service` running on port 8001:

```bash
cd astro-service
python run_ideal_match_prompt.py --synastry --date 1997-03-07 --time 10:59 --gender M --date2 1995-03-26 --time2 14:30 --gender2 F
```

Expected output:
```
合盤 Prompt 已寫入 .../astro-service/synastry_output.txt
```

Open `synastry_output.txt` and verify:
- Only **one** `【本次任務` block
- Power section says `勢均力敵` or `高位` (not raw `RPV=0.0`)
- Profile block `【雙方心理結構】` is present with `psychological_needs` content
- JSON schema has no `❌`, `👉`, `一、`, `二、`

**Step 5: Commit**

```bash
git add astro-service/run_ideal_match_prompt.py
git commit -m "feat(cli): add --synastry mode to run_ideal_match_prompt with profile injection"
```

---

## Final verification

Run the full astro-service test suite to confirm no regressions:

```bash
cd astro-service && pytest -v --tb=short 2>&1 | tail -20
```

Expected: All tests pass (387+ tests, 0 failures).

---

## Summary of changed files

| File | Change |
|------|--------|
| `astro-service/prompt_manager.py` | Replace `_MATCH_ARCHETYPE_SCHEMA`; rewrite `get_match_report_prompt`; update `build_synastry_report_prompt` signature |
| `astro-service/db_client.py` | Add `get_or_compute_psychology_profile()` |
| `astro-service/main.py` | Insert profile loading step 3.5; pass profiles to `build_synastry_report_prompt` |
| `astro-service/run_ideal_match_prompt.py` | Add `--synastry` flag + `build_synastry_prompt()` function |
| `astro-service/test_prompt_manager.py` | Add 7 new tests for schema + prompt fixes |
| `astro-service/test_db_client.py` | New file: 3 tests for `get_or_compute_psychology_profile` |
