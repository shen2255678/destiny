# Algorithm V2.0 — 十神心理學 + 身強弱 + 喜用神互補

根據 `2026-02-24-bonus-plan-1.0.md` 的 V2.0 SPEC，對 `astro-service/` 新增八字十神系統。
本計畫與 `2026-02-24-algorithm-v2-bonus-plan.md`（榮格哲學/邊際遞減/維度拆分/理想型萃取）為平行升級，可獨立執行。

> **架構鐵律**：十神只做「單人心理標籤」（寫入 `ideal_avatar.py`），絕不寫成 `matching.py` 裡的雙人扣分規則。合盤僅使用「喜用神互補」正向加成。

---

## 現有架構分析

`bazi.py` 已有的基礎設施（可直接複用）：

| 常數/函式 | 說明 |
|----------|------|
| `HEAVENLY_STEMS` | `["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]` |
| `EARTHLY_BRANCHES` | `["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]` |
| `STEM_ELEMENTS` | 天干 → 五行映射 |
| `STEM_YINYANG` | 天干 → 陰陽映射 |
| `BRANCH_ELEMENTS` | 地支 → 五行映射（本氣） |
| `calculate_bazi()` | 回傳 `four_pillars`（含 stem/branch），`hour` pillar 在 Tier 3 已設為 `None`（`hour_known=False`） |
| `bazi_day_branch` | 日支（夫妻宮）已在回傳中 |

---

## Sprint 5：十神底層引擎 (in `bazi.py`)

### 5-1：地支藏干常數字典 `HIDDEN_STEMS`

```python
# 十二地支藏干（本氣 / 中氣 / 餘氣）
HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}
```

### 5-2：十神映射函式 `get_ten_god(day_master, other_stem)`

根據日主五行/陰陽 vs 其他天干五行/陰陽，回傳十神名稱：

| 關係 | 同陰陽 | 異陰陽 |
|------|-------|-------|
| 同我（比和） | 比肩 | 劫財 |
| 我生（食傷） | 食神 | 傷官 |
| 我剋（財星） | 偏財 | 正財 |
| 剋我（官殺） | 七殺 | 正官 |
| 生我（印星） | 偏印 | 正印 |

### 5-3：`compute_ten_gods(bazi_chart: dict) -> dict`

- 讀取 `four_pillars` 的年/月/日/時天干 → 各自對照日主算出十神
- 讀取各柱地支 → 取 `HIDDEN_STEMS` 本氣藏干 → 對照日主算出地支十神
- **Tier 3 時柱屏蔽**：`hour` pillar 為 `None` 時跳過，不生成假十神
- 回傳結構：

```python
{
    "stem_gods": {
        "year": "偏財",    # 年干十神
        "month": "正官",   # 月干十神（格局核心）
        "day": "日主",     # 日干永遠是日主本身
        "hour": "食神"     # Tier 3 → None
    },
    "branch_gods": {
        "year": "正印",    # 年支本氣十神
        "month": "七殺",   # 月支本氣十神（月令）
        "day": "偏印",     # 日支本氣十神（夫妻宮，權重最高）
        "hour": "劫財"     # Tier 3 → None
    },
    "god_counts": {        # 各十神出現次數統計
        "正印": 1, "偏印": 1, "正官": 1, "七殺": 1,
        "食神": 1, ...
    },
    "spouse_palace_god": "偏印",   # 日支本氣十神（感情需求核心）
    "month_god": "正官"            # 月干十神（格局/性格核心）
}
```

### 5-4：`evaluate_day_master_strength(bazi_chart: dict) -> dict`

**簡化版身強弱判定**（權重計分）：

| 條件 | 計分 |
|------|------|
| 月支五行 = 印星（生我）或比劫（同我） | +40（得令） |
| 其他各干支為印星 | +10 each |
| 其他各干支為比劫 | +8 each |
| 各干支為官殺/食傷/財星 | -8 each |

- 總分 ≥ 50 → `is_strong = True`
- 總分 < 50 → `is_strong = False`

**喜用神推導**：

| 身強身弱 | 喜用神 | 忌神 |
|---------|--------|------|
| 身強 | 財星(我剋)、食傷(我生)、官殺(剋我) 之五行 | 印星、比劫 |
| 身弱 | 印星(生我)、比劫(同我) 之五行 | 財星、食傷、官殺 |

- **Tier 3 動態閾值**：有效干支僅 6 個（無時柱），閾值調低至 40

回傳結構追加至 `calculate_bazi` 回傳：

```python
{
    ...,  # 原有欄位
    "ten_gods": { ... },        # compute_ten_gods 結果
    "day_master_strength": {
        "score": 55,
        "is_strong": True,
        "favorable_elements": ["水", "金"],  # 喜用神五行
        "dominant_elements": ["火", "木"],    # 強勢五行
    }
}
```

---

## Sprint 6：十神心理標籤萃取 (in `ideal_avatar.py`)

### 6-1：十神心理映射字典

完整 10 神 → `psychological_needs` + `relationship_dynamic` 映射：

| 十神 | 觸發條件 | psychological_needs | relationship_dynamic |
|------|---------|---------------------|---------------------|
| 正印 | 偏旺 or 夫妻宮 | 極度需要穩定與承諾；偏好溫和、具備長輩般包容力 | stable |
| 偏印 | 偏旺 or 夫妻宮 | 極度缺乏安全感，防備心重；需要極致偏愛 | high_voltage |
| 正官 | 偏旺 or 夫妻宮 | 重視對方社會價值與人品；需要體面、情緒穩定的伴侶 | stable |
| 七殺 | 偏旺 or 夫妻宮 | 外表強勢但內在渴望被征服；需要勢均力敵的對手 | high_voltage |
| 正財 | 偏旺 or 夫妻宮 | 感情觀極度務實；偏好生活規律、願意實質付出的對象 | stable |
| 偏財 | 偏旺 or 夫妻宮 | 追求戀愛的樂趣與新鮮感；容易被幽默不黏人的人吸引 | — |
| 食神 | 偏旺 or 夫妻宮 | 追求純粹快樂、無壓力的相處；需要懂生活脾氣好的伴侶 | stable |
| 傷官 | 偏旺 or 夫妻宮 | 討厭世俗管束與愚笨；容易被才華洋溢具獨特魅力的人吸引 | high_voltage |
| 比肩 | 偏旺 or 夫妻宮 | 感情觀如兄弟般平等；需要懂得分寸感給予獨立空間 | — |
| 劫財 | 偏旺 or 夫妻宮 | 感情容易充滿戲劇性與競爭感；需要極高情緒價值 | high_voltage |

**「偏旺」判定（動態閾值）**：
- Tier 1（8 字）：`god_counts[十神] >= 3`，或 `月令 + 總數 >= 2`
- Tier 3（6 字）：`god_counts[十神] >= 2`

**夫妻宮優先權**：`spouse_palace_god` 若為 high_voltage 類型（七殺/偏印/傷官/劫財），強制觸發標籤。

### 6-2：衝突格局偵測

| 衝突組合 | Flag | 額外標籤 |
|---------|------|---------|
| 傷官 + 正官（傷官見官） | `psychological_conflict = True` | 內在充滿矛盾：理智渴望穩定，但潛意識被不穩定的人吸引 |
| 偏印 + 食神（梟神奪食） | `psychological_conflict = True` | 容易有突發性憂鬱；極度需要情緒穩定、能提供安全感的伴侶 |

### 6-3：整合進 `extract_ideal_partner_profile`

在現有 Rule 2（東方八字萃取）段落之後新增十神萃取，所有標籤合併輸出至 `psychological_needs` 和 `relationship_dynamic`。

---

## Sprint 7：喜用神合盤加成 (in `matching.py`)

### 7-1：`compute_favorable_element_resonance(user_a, user_b) -> dict`

新增函式，計算跨盤喜用神共振：

```python
def compute_favorable_element_resonance(user_a: dict, user_b: dict) -> dict:
    """
    若 B 的 dominant_elements 包含 A 的 favorable_elements → B 是 A 的貴人
    若 A 的 dominant_elements 包含 B 的 favorable_elements → A 是 B 的貴人
    雙向互補 → 完美共振
    """
```

- 單向匹配：`soul_adj += (100 - soul) * 0.20`（邊際遞減）
- 雙向匹配：`soul_adj += (100 - soul) * 0.35`

### 7-2：徽章觸發

| 條件 | 徽章 |
|------|------|
| 雙向互補（A 是 B 的喜用神 ∧ B 是 A 的喜用神） | `"完美互補：靈魂能量共振"` |
| 單向（B 是 A 的喜用神） | `"專屬幸運星"` |

### 7-3：串接 `compute_match_v2`

在 Phase II Psychology Modifiers 區塊（L1118+）新增 `compute_favorable_element_resonance` 呼叫：

```python
# 4. Favorable Element Resonance (喜用神互補)
fav_a = user_a.get("day_master_strength", {})
fav_b = user_b.get("day_master_strength", {})
if fav_a.get("favorable_elements") and fav_b.get("dominant_elements"):
    _fav = compute_favorable_element_resonance(user_a, user_b)
    soul_adj += _fav["soul_mod"]
    resonance_badges.extend(_fav.get("badges", []))
```

---

## Tier 降級策略

| 情境 | 有效字數 | 十神處理 | 身強弱處理 |
|------|---------|---------|-----------|
| Tier 1（精確時間） | 8 字 | 完整四柱十神 | 完整計分，閾值 50 |
| Tier 2（模糊時段） | 8 字（近似） | 完整但時柱精度略低 | 完整計分，閾值 50 |
| Tier 3（無時間） | 6 字 | 時柱 `None` 跳過 | 計分排除時柱，閾值 40 |
| 全部情境 | — | 日支（夫妻宮）100% 準確 | 月支（月令）100% 準確 |

---

## 驗證計畫

### 新增測試

| 檔案 | 測試數 | 涵蓋範圍 |
|------|-------|---------|
| `test_bazi.py` 新增 | +15 | `HIDDEN_STEMS` 正確性、`get_ten_god` 10 種映射、`compute_ten_gods` Tier 1/3、`evaluate_day_master_strength` 身強/弱 |
| `test_ideal_avatar.py` 新增 | +12 | 十神偏旺標籤、夫妻宮優先權、衝突格局偵測、Tier 3 降級不 crash |
| `test_matching.py` 新增 | +5 | 喜用神單向/雙向匹配、邊際遞減不超 100、徽章觸發 |

### 全量回歸

```bash
cd D:\新增資料夾\destiny\astro-service
python -m pytest -v
```

預期：407 → ~440（含 bonus-plan v1.0 升級）全部通過。

---

## Sprint 8：全維度資料融合 + LLM 提示詞工程 (Data Merge + Prompt Engineering)

> **依賴關係**：依賴 Sprint 4（`ideal_avatar.py` 基礎模組）+ Sprint 5/6（十神標籤）。執行順序：Sprint 4→5→6→**8**。Sprint 7 可平行。

### 8-1：擴充 `ideal_avatar.py` — 三系統標籤融合

修改 `extract_ideal_partner_profile` 函式簽名，加入 `psychology_data` 參數，整合西占心理學 + 紫微夫妻宮 + 八字十神的完整標籤：

```python
def extract_ideal_partner_profile(
    western_chart: dict,
    bazi_chart: dict,
    zwds_chart: dict,
    psychology_data: dict = {},   # 新增：接收 psychology.py 的輸出
) -> dict:
    """
    回傳「User Avatar JSON」（終極標籤融合結果）：
    {
        "target_western_signs":    ["Scorpio", "Taurus"],
        "target_bazi_elements":    ["水", "金"],
        "relationship_dynamic":    "high_voltage",
        "psychological_needs":     [...],
        "zwds_partner_tags":       [...],
        "karmic_match_required":   bool,
        "attachment_style":        "anxious",    # 新增：西占依附類型
        "psychological_conflict":  bool,         # 新增：衝突格局 flag
        "venus_mars_tags":         [...],        # 新增：金星/火星落星座標籤
        "favorable_elements":      ["水", "金"], # 新增：喜用神（來自 bazi）
    }
    """
```

**新增整合邏輯**（在現有三條 Rule 之後）：

| 整合來源 | 讀取欄位 | 輸出目標 |
|---------|---------|---------|
| `psychology_data.get("attachment_style")` | 焦慮/逃避/安全型 | → `attachment_style` + 注入 `psychological_needs` |
| `western_chart.get("venus_sign")` | 金星落入星座 | → `venus_mars_tags`（例：金星天蠍→「審美帶有強烈神秘色彩」）|
| `western_chart.get("mars_sign")` | 火星落入星座 | → `venus_mars_tags`（情慾激發特質）|
| `bazi_chart.get("day_master_strength", {}).get("favorable_elements")` | 喜用神 | → `favorable_elements` |

> **防呆**：所有欄位使用 `.get("key", None)` 存取，缺失靜默跳過，不引發 Exception。

---

### 8-2：擴充 `prompt_manager.py` — 注入結構化標籤加速解盤

**設計原則（擴充，不替換）**：直接修改現有 `get_ideal_match_prompt(chart_data)`，新增一個可選參數 `avatar_summary`。

```
原流程：原始星盤 ──→ LLM（自行解盤＋寫文案）
新流程：原始星盤 + Python 預算摘要 ──→ LLM（直接寫文案，省略推理）
```

LLM **仍然看得到完整星盤數據**（保留深度解讀能力），但額外獲得一段「Python 已預算好的結論摘要」，讓它不需要花費大量 token 重新推導，可以直接聚焦在文案生成：

```python
# 修改現有 get_ideal_match_prompt 函式簽名（L550）

def get_ideal_match_prompt(
    chart_data: dict,
    avatar_summary: dict | None = None,   # 新增可選參數
) -> str:
    """
    Build ideal partner profile prompt.
    若傳入 avatar_summary（extract_ideal_partner_profile 的輸出），
    會在 prompt 中注入「預算結論區塊」，讓 LLM 跳過推理直接生成文案。
    """
    # ... 原有邏輯不動 ...

    # ── 新增：若有預算標籤，注入為提示區塊 ──
    avatar_block = ""
    if avatar_summary:
        conflict_hint = (
            "\n⚠️ 衝突格局（傷官見官/梟神奪食）：此人理智渴望穩定、"
            "但潛意識被不穩定的人吸引，請在報告中直接點出此矛盾。"
            if avatar_summary.get("psychological_conflict") else ""
        )
        avatar_block = f"""
【後端預算命理摘要（直接使用，無需重新推導）】
感情動態: {avatar_summary.get("relationship_dynamic", "unknown")}
核心心理需求: {", ".join(avatar_summary.get("psychological_needs", [])[:4])}
喜用神（真正需要的能量）: {", ".join(avatar_summary.get("favorable_elements", []))}
依附風格: {avatar_summary.get("attachment_style", "unknown")}
夫妻宮標籤: {", ".join(avatar_summary.get("zwds_partner_tags", []))}
金星/火星特質: {", ".join(avatar_summary.get("venus_mars_tags", []))}
業力配對需求: {avatar_summary.get("karmic_match_required", False)}{conflict_hint}
"""

    prompt = f"""{DESTINY_WORLDVIEW}
...（原有 prompt 內容）...
{avatar_block}
{_IDEAL_MATCH_SCHEMA}"""   # avatar_block 注入在星盤數據之後、schema 之前
    return prompt
```


---

### 8-3：串接至 `main.py`

在 `/extract-ideal-profile` endpoint 中，補上 `psychology_data` 輸入支援：

```python
@app.post("/extract-ideal-profile")
async def extract_ideal_profile(req: dict):
    from ideal_avatar import extract_ideal_partner_profile
    from prompt_manager import build_ideal_avatar_prompt
    avatar = extract_ideal_partner_profile(
        req.get("western_chart", {}),
        req.get("bazi_chart", {}),
        req.get("zwds_chart", {}),
        req.get("psychology_data", {}),   # 新增
    )
    # 選擇性：若 req 包含 generate_report=True，直接呼叫 LLM 回傳報告
    if req.get("generate_report"):
        prompt = build_ideal_avatar_prompt(avatar)
        report = await call_llm(prompt)
        return {"avatar": avatar, "report": report}
    return avatar
```

---

## 驗證計畫（更新版）

### 新增測試

| 檔案 | 測試數 | 涵蓋範圍 |
|------|-------|---------|
| `test_bazi.py` 新增 | +15 | `HIDDEN_STEMS` 正確性、`get_ten_god` 10 種映射、`compute_ten_gods` Tier 1/3、`evaluate_day_master_strength` 身強/弱 |
| `test_ideal_avatar.py` 新增 | +12 | 十神偏旺標籤、夫妻宮優先權、衝突格局偵測、Tier 3 降級不 crash |
| `test_ideal_avatar.py` Sprint 8 | +8 | 三系統標籤融合、attachment_style 整合、venus_mars_tags、favorable_elements 傳遞、全空輸入不 crash |
| `test_matching.py` 新增 | +5 | 喜用神單向/雙向匹配、邊際遞減不超 100、徽章觸發 |
| `test_prompt_manager.py` 新增 | +4 | `build_ideal_avatar_prompt` 回傳非空字串、衝突格局特殊指示觸發、禁忌詞不出現 |

### 全量回歸

```bash
cd D:\新增資料夾\destiny\astro-service
python -m pytest -v
```

預期：407 → **~451** 全部通過。

---

## 與其他計畫的關係

| 計畫 | 狀態 | 依賴關係 |
|------|------|---------|
| `2026-02-24-algorithm-v2-bonus-plan.md`（Sprint 1-4） | 已規劃 | **互不衝突**：Sprint 4 的 `ideal_avatar.py` 會被本計畫 Sprint 6/8 擴充 |
| 本計畫 Sprint 5（bazi.py 十神） | — | 無前置依賴，可獨立開發 |
| 本計畫 Sprint 6（心理標籤） | — | 依賴 Sprint 5 + Sprint 4 |
| 本計畫 Sprint 7（喜用神合盤） | — | 依賴 Sprint 5；依賴 Sprint 3 |
| **本計畫 Sprint 8（LLM 融合）** | — | **依賴 Sprint 4+6**；`prompt_manager.py` `get_ideal_match_prompt` 仍保留供舊版回退 |
