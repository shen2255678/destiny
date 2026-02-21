# Algorithm Validation Sandbox — 使用指南

`astro-service/sandbox.html` 是一個獨立的內部開發工具，用於在 Phase E 上線前手動驗
證 Phase G 配對演算法（`compute_match_v2`）的輸出是否符合真實世界的配對結果。它不需
要啟動 Next.js，直接用瀏覽器開啟即可使用。

> **Note:** 這是內部開發者工具，不對外開放，不需要身份驗證。

---

## 前置作業

### 1. 啟動 astro-service

直接啟動即可，不需要預先設定環境變數：

```bash
cd astro-service
uvicorn main:app --port 8001
```

服務就緒後，終端機會顯示：

```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

> **Note:** API key 直接在 sandbox 頁面填入（見下方步驟 3），不需要設定在 server
> 環境變數中。若環境變數已設定，頁面留空時 server 會自動使用環境變數作為 fallback。

### 2. 開啟 sandbox

astro-service 啟動後，直接在瀏覽器開啟：

```
http://localhost:8001/sandbox
```

> **Note:** 請用 `http://localhost:8001/sandbox` 開啟，**不要**直接雙擊 `sandbox.html`
> 檔案。從 `file://` 協議呼叫 localhost API 會觸發瀏覽器的 CORS 限制，導致所有請求
> 失敗。從 `http://localhost:8001/sandbox` 開啟是同源請求，完全不受 CORS 影響。

### 3. 填入 API Key 並選擇 Provider

頁面頂端有一列全局設定，套用於所有 AI 生成功能（Tab A、C、D）：

1. 在 **LLM Provider** 下拉選單選擇目標 AI 服務。
2. 在 **API Key** 欄位貼上對應的金鑰（以 `password` 輸入框顯示，不會明文顯示）。
3. 若選擇 **Google Gemini**，還可在 **Model** 欄位自訂模型版本（預設
   `gemini-1.5-flash`，可改為 `gemini-1.5-pro`、`gemini-2.0-flash` 等）。

| Provider | 欄位 | 說明 |
|---|---|---|
| Anthropic (Claude Haiku) | **API Key** | `sk-ant-...` 開頭 |
| Google Gemini | **API Key** + **Model** | `AIza...` 開頭；Model 可自訂版本 |

Key 隨每次 AI 請求傳送至 astro-service（localhost only），不會傳到其他地方。若欄位
留空且 server 也未設定對應環境變數，呼叫 AI 功能時會收到 HTTP 400 錯誤。

---

## Step 0：排盤準確性驗證（建議優先執行）

在跑配對演算法之前，先確認三套排盤系統都輸出正確結果。
astro-service 已啟動後，直接用 `curl` 或瀏覽器 Console 打以下端點即可。

### 西洋占星 + 八字驗證（`/calculate-chart`）

使用一個已知真實星盤的生日做驗證，確認行星星座與四柱都正確：

```bash
curl -s -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1997-03-07",
    "birth_time": "precise",
    "birth_time_exact": "10:59",
    "lat": 25.033, "lng": 121.565,
    "data_tier": 1
  }' | python -m json.tool
```

**預期重點欄位：**

| 欄位 | 預期值 | 說明 |
|---|---|---|
| `sun_sign` | `"pisces"` | 3 月 7 日太陽在雙魚 |
| `ascendant_sign` | `"gemini"` | 台北 10:59 上升雙子（近似） |
| `bazi.four_pillars` | `丁丑 癸卯 戊申 丁巳` | 真太陽時修正後 |
| `bazi.day_master` | `"戊"` | 日干 |
| `bazi_element` | `"earth"` | 戊 → 土 |

> **Note:** 上升星座依地點和時間而異；只要太陽星座與四柱日干正確，
> 西洋占星和八字系統即確認無誤。

---

### 紫微斗數驗證（`/compute-zwds-chart`）

```bash
curl -s -X POST http://localhost:8001/compute-zwds-chart \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "birth_month": 6,
    "birth_day": 15,
    "birth_time": "11:30",
    "gender": "M"
  }' | python -m json.tool
```

**預期重點欄位：**

| 欄位 | 預期值 | 說明 |
|---|---|---|
| `five_element` | `"火六局"` | 農曆 5 月 23 日男命 |
| `four_transforms.hua_lu` | `"太陰"` | 庚年化祿在太陰 |
| `four_transforms.hua_ji` | `"天同"` | 庚年化忌在天同 |
| `palaces.ming.main_stars` | 非空陣列 | 命宮有主星（如 `["破軍"]`） |

**驗證順序建議：**

1. 確認 `five_element` 符合你的推算（可對照紫微斗數排盤工具）。
2. 確認 `four_transforms` 四化星正確（依出生年天干查表）。
3. 確認 `palaces.ming` 有主星；若命宮空宮，`main_stars` 應為 `[]`。

> **Note:** 若不確定自己的命盤，可用出生資料在網路紫微斗數工具（如
> 免費的線上排盤網站）取得 ground truth，再與 API 輸出比對。

---

### 三系統一致性驗證流程

使用同一個人的資料，分別呼叫兩個端點，確認：

1. `/calculate-chart` → 取得 `sun_sign`、`bazi_element`
2. `/compute-zwds-chart` → 取得 `five_element`、`palaces.ming.main_stars`
3. 在 Tab A 填入 Person A / B 的完整資料（含 `birth_year` 等），點擊
   **▶ Run Match** → 確認 `zwds` 區塊非 `null`，`spiciness_level` 有值

所有三步都通過後，才進入 Tab A 進行配對演算法的 MATCH/MISMATCH 驗證。

---

## Tab A — Mechanism A：伴侶驗證

這是核心驗證工具。輸入兩個真實人物的出生資料，讓演算法計算配對分數，再對照「已知
結果」（ground truth）判斷演算法的預測是否正確（MATCH / MISMATCH）。

### 輸入欄位

在 **PERSON A** 和 **PERSON B** 兩個卡片中各填入：

| 欄位 | 說明 |
|---|---|
| 顯示名稱 | 僅用於顯示（不影響計算） |
| 出生日期 | YYYY-MM-DD 格式 |
| 出生時間（精確） | HH:MM，留空則為 Tier 3（無時柱） |
| 緯度 / 經度 | 預設為台北（25.033, 121.565） |
| Data Tier | Tier 1（精確時間）/ Tier 2（模糊時段）/ Tier 3（僅日期） |

RPV 和依戀風格**不需手動填寫**，點擊 **▶ Run Match** 後系統會根據星盤自動推算並顯示於卡片
下方。推算邏輯如下：

| 參數 | 推算依據 |
|---|---|
| 依戀風格 | 月亮星座元素：水象→焦慮、土象→迴避、火象→焦慮、風象→安全 |
| RPV 衝突 | 太陽或火星在火象星座→開吵，否則冷戰 |
| RPV 權力 | 太陽在固定星座，或日主五行為木/火→主導，否則跟隨 |
| RPV 能量 | 上升（或太陽）在火/風象→外出，否則宅家 |

### MATCH/MISMATCH 閾值

在「MATCH/MISMATCH 閾值（可調整）」區塊可以即時調整四種配對情境的判斷條件：

| Ground Truth | MATCH 條件（預設） |
|---|---|
| 已婚（穩定） | `soul_score ≥ 65` 且 `primary_track` 為 `partner` 或 `soul` |
| 已分手（慘烈） | `(lust_score + soul_score) / 2 ≤ 55` |
| 已分手（和平） | `lust_score ≤ 60` 且 `soul_score < 65` |
| 萬年好友 | `primary_track == "friend"` 且 `lust_score ≤ 60` |

調整閾值後，下次點擊 **▶ Run Match** 時即套用新數值。

### 執行配對

1. 在 **Ground Truth** 下拉選單選擇該對關係的已知結果。
2. 點擊 **▶ Run Match**。
3. 沙盒依序呼叫：
   - `POST /calculate-chart`（Person A）
   - `POST /calculate-chart`（Person B）
   - `POST /compute-match`（合盤計算）
4. 結果面板顯示：
   - **MATCH ✓** / **MISMATCH ✗** 徽章（比對 ground truth）
   - VibeScore（lust_score）和 ChemistryScore（soul_score）進度條及各行星分項
   - 四軌分數（friend / passion / partner / soul）與 primary_track
   - 權力動態（viewer_role / target_role / RPV / frame_break）
   - 系統標籤（labels）
   - **Phase H ZWDS 欄位**（Tier 1 only）：`spiciness_level`（STABLE / MEDIUM / HIGH_VOLTAGE / SOULMATE）、`defense_mechanisms`（viewer/target 煞星防禦機制）、`layered_analysis`（業力羈絆 + 化権動態 + 命宮星群）

### AI Archetype 解讀報告

結果顯示後，點擊 **✦ Generate** 呼叫 `/generate-archetype`，生成：

- **Archetype Tags**：3 個英文詞組描述這段關係的本質（例如：`Mirror Twins`、
  `Power Clash`）
- **解讀報告**：約 150 字的繁體中文分析

> **Note:** 此功能使用目前在 LLM Provider 選單中選擇的 AI 服務。Gemini 和 Anthropic
> 皆支援。

---

## Tab B — Mechanism B：校時模擬

驗證出生時間校正系統（Phase B.5 Via Negativa）能否從模糊時段還原出精確時間。

### 執行方式

1. 輸入一個**已知的精確出生時間**（作為 ground truth，例如 `14:30`）。
2. 點擊 **▶ Simulate Rectification**。
3. 沙盒根據小時數判斷時段（morning / afternoon / evening），初始化 ±180 分鐘視窗。
4. 依序顯示 5 道 Via Negativa 問題，每道題有 **✓ 是的，我不是** / **✗ 不對，我是**
   兩個選項。
5. 每次回答後視窗縮小約 60 分鐘，置信度 +0.10。
6. 5 道題結束後顯示最終結果：
   - **✅ PASS**：精確時間落在最終視窗內
   - **❌ FAIL**：精確時間落在視窗外（需檢討問題設計或縮小策略）

時段判斷規則：

| 出生小時 | 時段 | 初始視窗中心 |
|---|---|---|
| 4:00 – 11:59 | morning | 08:00 |
| 12:00 – 17:59 | afternoon | 15:00 |
| 18:00 以後 / 0:00 – 3:59 | evening | 21:00 |

---

## Tab C — 個人名片生成器

根據單人的星盤與 RPV 資料，生成交友軟體風格的個人名片。

### 輸入欄位

填入出生日期、出生時間（選填）、地理位置，以及 RPV 三個維度（衝突 / 權力 / 能量）
和依戀風格。

### 輸出格式

點擊 **✦ 生成個人名片** 後，AI 返回：

```json
{
  "headline": "靈魂探索者",
  "tags": ["直覺敏銳", "情感深度", "享受安靜的驚喜", "獨立"],
  "bio": "你是那種喜歡緊跟時代但不跟濫流行的人...",
  "vibe_keywords": ["神秘", "溫柔", "獨立"]
}
```

結果渲染為卡片形式：標題、標籤列、自介文字、氛圍關鍵字。

---

## Tab D — 雙人合盤報告生成器

生成完整的關係潛力報告，包含閃光點、成長課題和相處建議。

### 兩種填入方式

**方式 A — 從 Mechanism A 自動填入（推薦）：**

1. 先在 Tab A 執行 **▶ Run Match**。
2. 切換到 Tab D，點擊 **← 從上次合盤填入**。
3. 所有分數和參數自動填入（含 labels、power 動態）。
4. 點擊 **✦ 生成合盤報告**。

**方式 B — 手動輸入：**

直接填入 VibeScore、ChemistryScore、四軌分數、primary_track、quadrant 和 RPV，
然後點擊 **✦ 生成合盤報告**。

> **Note:** 手動方式無法輸入 `viewer_role` 和 `target_role`，這兩個欄位在手動路
> 徑下預設為 `Equal`。若需要完整的權力動態分析，使用方式 A。

### 輸出格式

AI 返回並渲染：

- **標題**：8 字以內描述這段關係
- **一句話核心**：詩意但直白的關係本質
- **✦ 閃光點**：3 個高分項目的正面描述
- **⚡ 成長課題**：潛在張力（包裝為學習機會）
- **相處建議**：約 100 字的具體可操作建議

---

## Gemini API 支援

沙盒的三個 AI 端點（`/generate-archetype`、`/generate-profile-card`、
`/generate-match-report`）全部支援在 Anthropic Claude 和 Google Gemini 之間切換，
並支援自訂 Gemini 模型版本。

**Anthropic 路徑：**

```
browser → POST /generate-archetype { provider: "anthropic", api_key: "sk-ant-..." }
        → call_llm(prompt, provider="anthropic", api_key="sk-ant-...")
        → Anthropic SDK → claude-haiku-4-5-20251001
```

**Gemini 路徑（自訂 model）：**

```
browser → POST /generate-archetype { provider: "gemini",
                                     api_key: "AIza...",
                                     gemini_model: "gemini-2.0-flash" }
        → call_llm(prompt, provider="gemini", api_key="AIza...", gemini_model="gemini-2.0-flash")
        → google-generativeai SDK → gemini-2.0-flash
```

兩條路徑使用完全相同的 prompt 和輸出 JSON schema，結果格式一致。api_key 欄位可為
空字串，server 此時自動 fallback 至環境變數（`ANTHROPIC_API_KEY` 或
`GEMINI_API_KEY`）。

> **Note:** `google-generativeai` SDK 目前顯示棄用警告，將在 Phase E 開始前遷移至
> `google-genai` 新套件（issue 已記錄）。現有功能不受影響。

---

## 測試記錄

Tab A 的每次執行會自動產生測試 ID（格式：`A-YYYYMMDD-NNN`），方便追蹤驗證記錄。
瀏覽器重新整理後計數器歸零（從 001 重新開始）。

建議測試組合：

| Test | Person A | Person B | Ground Truth | 期望結果 |
|---|---|---|---|---|
| T01 | 已婚夫妻 A | 已婚夫妻 B | 已婚（穩定）| MATCH（soul ≥ 65，partner/soul track） |
| T02 | 慘烈分手 A | 慘烈分手 B | 已分手（慘烈）| MATCH（avg ≤ 55） |
| T03 | 多年好友 A | 多年好友 B | 萬年好友 | MATCH（friend track primary，lust ≤ 60） |
| T04 | 校時模擬 | 精確時間 14:30 | — | PASS（時間落在最終視窗） |

---

## 已知限制

- 沙盒無持久化存儲，重新整理後所有輸入和結果消失。
- Tab A 的 RPV / 依戀風格使用心理占星啟發式推算，非真實產品的問卷資料，僅供演算法
  驗證參考。
- Tab D 手動路徑的 `viewer_role`/`target_role`/`frame_break` 固定為預設值；若需
  完整分析請使用「從上次合盤填入」。
- Mechanism B 使用 5 道固定問題的簡化模擬，非真實的動態 Via Negativa 系統。
- Gemini provider 目前使用 `google-generativeai`（棄用中），若 Gemini 呼叫失敗
  請先確認 `GEMINI_API_KEY` 已正確設定。
