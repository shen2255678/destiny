# Bonus Algorithm Upgrade — 榮格哲學 + 邊際遞減 + 維度拆分 + 理想型萃取

根據 `2026-02-24-bonus-plan.md` 的需求，對 `astro-service/` 進行 4 個 Sprint 的演算法升級。

> **執行順序：Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4（可獨立）**
> Sprint 3 的 `karmic_tension` 依賴 Sprint 1 的 `partner_mod` 值，必須依序執行。

---

## Sprint 1：Batch 1 — 陰影引擎哲學重構 (Jungian Shift)

**修改範圍：** `astro-service/shadow_engine.py` → `compute_shadow_and_wound`

**目標：** 業力觸發器不再只是加分，須同時扣除「世俗伴侶分數（`partner_mod`）」，如實反映高張力關係的日常摩擦代價。

| 觸發條件 | soul_mod | lust_mod | partner_mod | high_voltage |
|----------|----------|----------|-------------|--------------|
| Chiron 合相/沖（非 Mars） | +15 | 0 | **-10**（新增） | ✓ |
| Chiron 合相/沖（Mars） | +15 | +10 | **-15**（新增） | ✓ |
| South Node 合相 | +20 | 0 | **-15**（新增） | ✓ |
| 12th House Overlay | +20 | 0 | **-10**（新增） | ✓ |
| Mutual Shadow Integration | +40 | 0 | **-20**（新增） | — |
| Lilith 合相 | 0 | +25 | **-10**（新增） | ✓ |
| Vertex 觸發器 | +25 | 0 | 不變（0） | — |
| North Node 合相 | +20 | 0 | 不變（0） | — |

```diff
 # Chiron conjunction/opposition (non-Mars)
 result["soul_mod"] += 15.0
+result["partner_mod"] -= 10.0
 result["high_voltage"] = True

 # Chiron conjunction/opposition (Mars)
 result["soul_mod"] += 15.0
 result["lust_mod"] += 10.0
+result["partner_mod"] -= 15.0
 result["high_voltage"] = True

 # South Node conjunction
 result["soul_mod"] += 20.0
+result["partner_mod"] -= 15.0
 result["high_voltage"] = True

 # 12th House Overlay (single direction)
 result["soul_mod"] += 20.0
+result["partner_mod"] -= 10.0

 # Mutual Shadow Integration
 result["soul_mod"] += 40.0
+result["partner_mod"] -= 20.0

 # Lilith conjunction
 result["lust_mod"] += 25.0
+result["partner_mod"] -= 10.0
```

**邏輯閉環確認：** `matching.py` L1133 已有 `partner_adj += _shadow.get("partner_mod", 0.0)`，L1173-1174 已有 `tracks["partner"] = _clamp(tracks["partner"] + partner_adj)`。Sprint 1 只需改 `shadow_engine.py` 回傳值，下游 wiring 已存在。

**新增測試：** `test_shadow_engine.py`，+6 個測試，驗證各觸發器的 `partner_mod` 扣分值。

---

## Sprint 2：Batch 2 — 邊際遞減公式 (Diminishing Returns)

**修改範圍：** `astro-service/matching.py` → `compute_soul_score`、`compute_lust_score`

**目標：** 用邊際遞減公式取代線性乘法，確保分數不爆表、保留鑑別度。

### `compute_soul_score`（L752-758）

```diff
 if rel["relation"] in ("a_generates_b", "b_generates_a"):
-    base_score *= WEIGHTS["soul_generation_mult"]   # 原本 ×1.2
+    # 邊際遞減：給予剩餘空間的 30% 加成
+    base_score += (1.0 - base_score) * 0.30
+elif rel["relation"] == "same":
+    # 比和：給予剩餘空間的 15% 加成
+    base_score += (1.0 - base_score) * 0.15
```

### `compute_lust_score`（L672-678）

```diff
 if rel["relation"] in ("a_restricts_b", "b_restricts_a"):
-    base_score *= WEIGHTS["lust_bazi_restrict_mult"]   # 原本 ×1.25
+    # 邊際遞減：給予剩餘空間的 25% 加成
+    base_score += (1.0 - base_score) * 0.25
```

**新增測試：** `test_matching.py`，+2 個測試，驗證遞減後分數 ≤ 100 且高於無加成基線。

---

## Sprint 3：Batch 3 — 維度拆分與徽章系統 (Dimensional Split)

**修改範圍：** `astro-service/matching.py` → `compute_match_v2`

**目標：** 新增 `karmic_tension` 張力指數與 `resonance_badges` 共振徽章至回傳結構。

### `karmic_tension` 計算（Apply modifiers 之後）

```python
# ── Karmic Tension Index (0-100) ──────────────────────────────────────────
# 痛感（partner_mod）佔最大視覺比重；情慾執念次之；靈魂羈絆為隱性張力
raw_tension = (
    abs(_shadow.get("partner_mod", 0.0)) * 1.5 +
    abs(_shadow.get("lust_mod",    0.0)) * 1.0 +
    abs(_shadow.get("soul_mod",    0.0)) * 0.5
)
karmic_tension = _clamp(raw_tension)
```

### `resonance_badges` 計算

```python
# ── Resonance Badges ──────────────────────────────────────────────────────
resonance_badges: List[str] = []

# Badge A: 命理雙重認證 — soul ≥ 80 且八字相生/比和
if soul >= 80 and bazi_relation in ("a_generates_b", "b_generates_a", "same"):
    resonance_badges.append("命理雙重認證")

# Badge B: 三界共振：宿命伴侶 — Badge A + ZWDS SOULMATE
if "命理雙重認證" in resonance_badges \
        and zwds_result and zwds_result.get("spiciness_level") == "SOULMATE":
    resonance_badges.append("三界共振：宿命伴侶")

# Badge C: 進化型靈魂伴侶 — karmic_tension ≥ 30 且 soul ≥ 75
if karmic_tension >= 30 and soul >= 75:
    resonance_badges.append("進化型靈魂伴侶：虐戀與升級")
```

### Return dict 新增欄位

```diff
 return {
     "lust_score":   round(lust, 1),
     "soul_score":   round(soul, 1),
+    "harmony_score":     round(soul, 1),       # alias for frontend
+    "karmic_tension":    round(karmic_tension, 1),
+    "resonance_badges":  resonance_badges,
     "power":  power,
     "tracks": tracks,
     ...
 }
```

**新增測試：** `test_matching.py`，+5 個測試，驗證 karmic_tension 加權計算與三種 badge 觸發條件。

---

## Sprint 4：Batch 4 — 理想型萃取引擎 (Target Avatar Profiling)

**修改範圍：** 新建 `astro-service/ideal_avatar.py` + `test_ideal_avatar.py`；修改 `main.py` 新增 endpoint。

**目標：** 將單人星盤逆向工程為「理想對象特徵標籤」，供推薦系統做第一層 DB filter，替換 LLM 直接通靈。

### 函式簽名

```python
def extract_ideal_partner_profile(
    western_chart: dict,
    bazi_chart: dict,
    zwds_chart: dict,
) -> dict:
    """
    回傳範例：
    {
        "target_western_signs":  ["Scorpio", "Taurus"],
        "target_bazi_elements":  ["水", "木"],
        "relationship_dynamic":  "high_voltage",     # "stable" | "high_voltage"
        "psychological_needs":   ["渴望被強勢帶領", "需要深度靈魂連結"],
        "zwds_partner_tags":     ["氣場強", "直接不扭捏"],
        "karmic_match_required": False
    }
    """
```

### 三層萃取邏輯

#### Rule 1：西方占星萃取

| 來源 | 萃取邏輯 | 輸出欄位 |
|------|---------|---------|
| DSC（第 7 宮宮頭） | 最高權重；填入對面星座 | `target_western_signs` |
| Venus 落入星座 | 「美學偏好」 | `target_western_signs` |
| Mars 落入星座 | 「情慾激發特質」 | `target_western_signs` |
| Venus/Moon 與 Pluto/Uranus/Chiron 形成 hard aspect（合/刑/沖） | 潛意識高波動偏好 | `relationship_dynamic = "high_voltage"` |

> **⚠️ Tier 3 降級（必須實作）**：若 `western_chart` 缺少 `descendant_sign` / `houses`（無精確出生時間），靜默略過 DSC，權重 100% 轉移至 Venus 與 Mars。所有欄位使用 `.get("key", None)` 存取，缺失直接跳過，絕不引發 Exception。

#### Rule 2：東方八字萃取

| 來源 | 萃取邏輯 | 輸出欄位 |
|------|---------|---------|
| 日主五行（Day Master） | 根據相生相合推導互補五行（木需水滋潤、需金修剪等） | `target_bazi_elements` |
| 日支（Day Branch，Optional） | 若有偏印日支 → `psychological_needs` 追加「容易被古怪、有獨特邏輯的人吸引」 | `psychological_needs` |

#### Rule 3：紫微斗數夫妻宮萃取

**主星群組映射：**

| 夫妻宮主星 | 標籤 |
|-----------|------|
| 七殺、破軍、貪狼（殺破狼） | 「感情波動大」、「喜歡充滿魅力與挑戰性的對象」 |
| 紫微、天府、太陽 | 「喜歡氣場強大、能帶領自己的人」、「慕強心理」 |
| 天機、太陰、天同、天梁（機月同梁） | 「渴望溫柔陪伴」、「喜歡知性、情緒穩定的人」 |

**空宮借星（Empty Palace Resolution）：**
- 偵測夫妻宮無 14 主星（紫微、天機…破軍）→ 改讀官祿宮主星，標記 `is_borrowed: True`
- 在 `psychological_needs` 追加「感情觀較具彈性，容易受環境或伴侶狀態影響」

**六煞星潛意識渴望：**

| 煞星 | 注入標籤 | zwds_partner_tags | relationship_dynamic |
|------|---------|-------------------|---------------------|
| 擎羊、火星 | 潛意識容易被強勢、有野性的人吸引；需要勢均力敵的愛情對手 | 「氣場強」、「直接不扭捏」 | `high_voltage` |
| 陀羅、鈴星 | 感情中帶有強烈執念；容易吸引帶有宿命感的對象 | 「心思深沉」、「宿命感」 | `high_voltage` |
| 地空、地劫 | 不愛世俗常規的感情；追求極致靈魂交流 | 「靈魂共鳴」、「非傳統關係」 | `high_voltage` |

**負負得正（Karmic Matching Flag）：**
- 西占偵測到 high_voltage **且** 紫微夫妻宮有煞星 → `karmic_match_required: true`

> **⚠️ 防呆（必須實作）**：
> - 若 `zwds_chart` 為空或 Tier 2/3（無紫微盤），直接回傳空 `zwds_partner_tags: []`，不影響西方與八字萃取。
> - `extract_ideal_partner_profile({}, {}, {})` 全空輸入必須正常回傳空結構，不 crash。

### 新增 FastAPI endpoint（`main.py`）

```python
@app.post("/extract-ideal-profile")
async def extract_ideal_profile(req: dict):
    from ideal_avatar import extract_ideal_partner_profile
    return extract_ideal_partner_profile(
        req.get("western_chart", {}),
        req.get("bazi_chart", {}),
        req.get("zwds_chart", {}),
    )
```

**新增測試：** `test_ideal_avatar.py`，+20 個測試（含 Tier 3 降級 + 空 ZWDS 防呆）。

---

## Verification Plan

```bash
cd D:\新增資料夾\destiny\astro-service
python -m pytest test_shadow_engine.py test_matching.py test_ideal_avatar.py -v

# 全量回歸
python -m pytest -v
```

| Sprint | 新增測試數 | 重點驗證 |
|--------|-----------|---------|
| 1 | +6 | 各觸發器的 `partner_mod` 扣分值；現有 56 個 shadow 測試需更新斷言 |
| 2 | +2 | 遞減後分數 ≤ 100 且高於無加成基線 |
| 3 | +5 | karmic_tension 加權計算；三種 badge 觸發條件 |
| 4 | +20 | Rule 1/2/3 + Tier 3 降級 + 空輸入防呆 |
| **總計** | **+33** | **407 → ~440 全部通過** |
