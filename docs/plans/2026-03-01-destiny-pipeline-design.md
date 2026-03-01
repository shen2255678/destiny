# DESTINY Pipeline 設計文件

**日期：** 2026-03-01
**狀態：** Approved
**目標：** 將排盤 → 匹配 → 心理萃取 → prompt 組裝封裝為 `DestinyPipeline` class，提供一條龍的 enriched 輸出，取代現有的手動膠水腳本。

---

## 1. 動機

### 現狀痛點

1. `/compute-match` 只回傳原始分數（lust/soul/tracks），不含中文標籤和 prompt
2. `prompt_manager.py` 的標籤翻譯（`_translate_psych_tags`）和 `ideal_avatar.py` 的心理需求萃取只在本地腳本 `run_ideal_match_prompt.py` 裡呼叫，API 層拿不到
3. `run_ideal_match_prompt.py` 有 300+ 行膠水代碼（`build_natal_report`、`flatten_to_chart_data`、`build_synastry_prompt`），手動串接 API call
4. Windows cp950 編碼問題：中文/emoji print 到 terminal 會爆

### 目標

- **後端一條龍：** 一個 API call → 分數 + 中文標籤 + 組好的 prompt
- **DTO 安全：** 不洩漏原始度數、natal aspects 等敏感天文資料
- **預留 LLM：** 未來加 `.call_llm()` step 即可完成全流程
- **CLI 精簡：** `run_ideal_match_prompt.py` 從 300 行降到 ~30 行

---

## 2. 架構

### 2.1 核心類別

```python
# destiny_pipeline.py (新檔案)

@dataclass
class BirthInput:
    birth_date: str        # "1996-11-05"
    birth_time: str | None # "02:00" (Tier 1) | None (Tier 3)
    gender: str            # "M" | "F"
    lat: float = 25.033
    lng: float = 121.565
    # data_tier 由 Pipeline 自動推斷

class DestinyPipeline:
    """從出生資料到 prompt-ready 輸出的一條龍流水線。"""

    def __init__(self, person_a: BirthInput, person_b: BirthInput | None = None):
        # person_b = None → 單人模式 (profile / ideal match)
        # person_b 有值 → 雙人模式 (synastry)

    def compute_charts(self) -> "DestinyPipeline":
        # 呼叫 chart.py::calculate_chart + zwds.py::compute_zwds_chart
        # 結果存 self._chart_a, self._full_report_a 等

    def compute_match(self) -> "DestinyPipeline":
        # 雙人模式：呼叫 matching.py::compute_match_v2
        # 單人模式：skip（no-op）

    def extract_profiles(self) -> "DestinyPipeline":
        # 呼叫 ideal_avatar.py::extract_ideal_partner_profile

    def build_prompts(self) -> "DestinyPipeline":
        # 呼叫 prompt_manager.py 的各函數組裝 prompt

    def to_enriched_dto(self) -> dict:
        # 安全 DTO — 前端用

    def to_raw(self) -> dict:
        # 完整資料 — CLI / debug 用

    def to_json_file(self, path: str) -> None:
        # 寫 enriched DTO 到 UTF-8 JSON 檔案

    def to_prompt_file(self, prompt_key: str, path: str) -> None:
        # 寫指定 prompt 到 UTF-8 純文字檔
```

### 2.2 資料流

```
BirthInput(date, time, gender, lat, lng)
    │
    ▼
compute_charts()  ←── chart.py + zwds.py
    │
    ├── 單人 → extract_profiles() → build_prompts(profile, ideal_match)
    │
    └── 雙人 → compute_match() → extract_profiles()
                → build_prompts(synastry, profile×2, ideal×2)
    │
    ▼
to_enriched_dto()  →  前端安全 DTO
to_raw()           →  CLI / debug
```

### 2.3 Tier 自動推斷

```python
def _infer_tier(birth_time: str | None) -> int:
    if birth_time and ":" in birth_time:
        return 1   # "14:30" → Tier 1
    if birth_time in ("morning", "afternoon", "evening"):
        return 2   # 模糊時段 → Tier 2
    return 3       # None / "unknown" → Tier 3
```

---

## 3. Enriched DTO 結構

```python
{
  # ── 基本資訊 ──
  "mode": "synastry" | "single",
  "data_quality": {
    "person_a": { "tier": 1, "missing": [] },
    "person_b": { "tier": 3, "missing": ["moon", "ascendant", "houses", "zwds", "hour_pillar"] }
  },

  # ── 分數 (雙人模式才有) ──
  "scores": {
    "harmony": 85.4,
    "lust": 35.2,
    "soul": 85.4,
    "karmic_tension": 10.0,
    "tracks": { "friend": 8.0, "passion": 15.3, "partner": 35.8, "soul": 87.26 },
    "primary_track": "soul",
    "quadrant": "partner",
    "spiciness_level": "STABLE",
    "high_voltage": false
  },

  # ── 中文標籤 (前端可直接顯示) ──
  "tags_zh": {
    "resonance_badges": ["專屬幸運星"],
    "labels": ["✦ 靈魂型連結"],
    "psychological": ["你的愛意引領對方走向靈魂想去的地方..."],
    "element_a": "四元素均衡",
    "element_b": "靈魂黑洞: 風（思維/溝通）",
    "power_dynamic": "勢均力敵的博弈，雙方話語權接近"
  },

  # ── 個人摘要 (不含原始度數) ──
  "person_a_summary": {
    "sun": "scorpio", "moon": "leo", "ascendant": "virgo",
    "venus": "libra", "mars": "virgo", "juno": "aries",
    "descendant": "pisces",
    "day_master": "丙火 (陽)",
    "pillars": "丙子 戊戌 丙午 己丑",
    "zwds_ming": "武曲七殺",
    "zwds_spouse": "天相",
    "sm_tags_zh": ["享受施壓的快感", "在關係中容易焦慮"],
    "karmic_tags_zh": ["白羊↔天秤軸線：學習獨立與合作的平衡"],
    "element_profile": { "dominant": ["Earth"], "deficiency": [] },
    "ideal_partner_profile": {
      "target_signs": ["Pisces", "Aries"],
      "psychological_needs": ["極度需要情緒承接與溫柔的安全感"],
      "relationship_dynamic": "high_voltage",
      "venus_mars_tags": ["金星天秤：追求美感與和諧的對等關係"]
    }
  },
  "person_b_summary": { ... },

  # ── Prompts (完整文字，可直接丟 LLM) ──
  "prompts": {
    "synastry": "【系統角色與核心哲學】...",
    "ideal_a": "【系統角色與核心哲學】...",
    "ideal_b": "【系統角色與核心哲學】...",
    "profile_a": "【系統角色與核心哲學】...",
    "profile_b": "【系統角色與核心哲學】..."
  }
}
```

### DTO 安全規則

- **不含：** `*_degree`、`natal_aspects`、`planet_degrees`、raw chart dict
- **不含：** `_PSYCH_TAG_ZH` 的 key（英文原始標籤），只含翻譯後的中文
- **包含：** 星座名（`sun: "scorpio"`）— 這是公開資訊，不敏感

---

## 4. API Endpoint

### POST /compute-enriched

**Request：**
```json
{
  "person_a": {
    "birth_date": "1996-11-05",
    "birth_time": "02:00",
    "gender": "F",
    "lat": 25.033,
    "lng": 121.565
  },
  "person_b": {
    "birth_date": "1996-12-10",
    "birth_time": null,
    "gender": "M"
  }
}
```

- `person_b` 省略 → 單人模式
- `birth_time: null` → Tier 3 自動推斷
- `lat/lng` 省略 → 預設台北

**Response：** Enriched DTO（見 Section 3）

### 向後相容

現有 endpoint 全部保留不動：
- `/compute-match` — 原始分數
- `/calculate-chart` — 原始星盤
- `/preview-prompt` — simple report prompt
- `/generate-match-report` — LLM 報告
- `/generate-ideal-match` — LLM 理想伴侶
- `/extract-ideal-profile` — ideal avatar

---

## 5. 編碼策略

| 層級 | 策略 |
|------|------|
| Pipeline 內部 | 全部 UTF-8 str，不涉及編碼轉換 |
| JSON 序列化 | `ensure_ascii=False` + `encoding="utf-8"` |
| API 回傳 | FastAPI 預設 UTF-8 JSON，無需處理 |
| CLI 輸出 | 永遠寫檔（UTF-8），不 print 中文到 terminal |
| `to_json_file()` | `open(path, "w", encoding="utf-8")` |
| `to_prompt_file()` | `open(path, "w", encoding="utf-8")` |
| CLI stdout | 只 print ASCII 狀態訊息（DONE, ERROR）；加 `--stdout` flag 時 `sys.stdout.reconfigure(encoding="utf-8")` |

---

## 6. 檔案變更清單

| 檔案 | 動作 | 說明 |
|------|------|------|
| `destiny_pipeline.py` | **新增** | 核心 Pipeline class + BirthInput |
| `main.py` | **修改** | 新增 `POST /compute-enriched` endpoint |
| `run_ideal_match_prompt.py` | **修改** | 改用 Pipeline，300行→~30行 |
| `test_pipeline.py` | **新增** | Pipeline 單元測試 |
| `docs/PIPELINE-GUIDE.md` | **新增** | Pipeline 使用手冊 |
| `chart.py` | 不動 | |
| `matching.py` | 不動 | |
| `shadow_engine.py` | 不動 | |
| `psychology.py` | 不動 | |
| `ideal_avatar.py` | 不動 | |
| `prompt_manager.py` | 不動 | |
| `zwds.py` | 不動 | |

---

## 7. 測試計畫

```
test_pipeline.py
├── test_single_person_tier1          # Tier 1 單人完整輸出
├── test_single_person_tier3          # Tier 3 缺失欄位標記
├── test_synastry_both_tier1          # 雙 Tier 1 完整分數 + 5 prompts
├── test_synastry_mixed_tier          # Tier 1 + Tier 3 混合
├── test_dto_no_raw_degrees           # DTO 不含 *_degree
├── test_dto_no_aspects_leaked        # DTO 不含 natal_aspects
├── test_tags_zh_all_translated       # 心理標籤全中文
├── test_data_quality_missing         # Tier 3 missing 欄位正確
├── test_tier_auto_inference          # "14:30"→T1, "morning"→T2, None→T3
├── test_encoding_utf8_output         # 檔案輸出合法 UTF-8
├── test_chained_api                  # Pipeline chain state 正確
└── test_endpoint_compute_enriched    # HTTP endpoint 回傳結構符合 schema
```

---

## 8. 未來擴充

### 接 LLM（下一階段）

```python
# Pipeline 新增一步
pipeline.call_llm(provider="anthropic")
# prompt 送 LLM → 回傳 JSON → 存入 self._llm_results

# DTO 新增欄位
"llm_results": {
    "synastry": { "archetype_tags": [...], "resonance": "...", ... },
    "ideal_a": { "ideal_partner": "...", "toxic_trap": [...], ... },
    ...
}
```

### 新增 Prompt 類型

在 `build_prompts()` 裡新增 prompt_manager 的函數呼叫即可，DTO 自動帶出。
