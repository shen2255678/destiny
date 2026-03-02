# 命運排行榜 — 設計文件

> **Date:** 2026-03-02
> **Status:** Draft — 待 review
> **Scope:** 新增 `/ranking` 頁面，預計算配對分數排行榜

---

## 1. 需求摘要

用戶可以在排行榜頁面看到 DB 中所有參與排名的用戶，依照與自己的契合度排序。顯示資訊以原型標籤和分數為主，隱藏所有隱私資料（姓名、生辰、出生地），增添神秘感。

### 決策記錄

| 決策項目 | 結論 |
|---------|------|
| 計算方式 | 預計算 + 快取（背景 job） |
| 顯示資訊 | 原型標籤 + 分數（不顯示姓名/生辰/位置） |
| 點擊行為 | 先彈出簡介卡片 → 用戶決定是否看完整報告 |
| 基準選擇 | 用戶手動選擇自己的哪張 soul_card |
| 配對範圍 | 每人只取 `yin_yang='yin'` 的主卡參與排名 |
| Token 機制 | MVP 先不限制，日後加入付費門檻 |

---

## 2. 架構

### 2.1 核心流程

```
用戶建立/更新 yin 主卡
        ↓
觸發預計算（POST /api/ranking/recompute）
        ↓
對所有其他 yin 卡呼叫 astro-service /compute-enriched
        ↓
結果寫入 ranking_cache table
        ↓
用戶進 /ranking → GET /api/ranking → 讀 ranking_cache → 排序顯示
```

### 2.2 新增 DB Table

```sql
CREATE TABLE ranking_cache (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_a_id     UUID NOT NULL REFERENCES soul_cards(id) ON DELETE CASCADE,
  card_b_id     UUID NOT NULL REFERENCES soul_cards(id) ON DELETE CASCADE,
  harmony       SMALLINT NOT NULL,    -- 0-100
  lust          SMALLINT NOT NULL,    -- 0-100
  soul          SMALLINT NOT NULL,    -- 0-100
  primary_track TEXT NOT NULL,         -- friend / passion / partner / soul
  quadrant      TEXT,                  -- soulmate / lover / partner / colleague
  labels        JSONB DEFAULT '[]',   -- 原型標籤 string[]
  tracks        JSONB DEFAULT '{}',   -- { friend, passion, partner, soul }
  computed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(card_a_id, card_b_id)
);

-- 加速查詢：用戶進排行榜時以 card_a_id 查詢
CREATE INDEX idx_ranking_cache_card_a ON ranking_cache(card_a_id);

-- RLS：用戶只能讀取 card_a_id 屬於自己的行
ALTER TABLE ranking_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY ranking_cache_owner_select ON ranking_cache
  FOR SELECT USING (
    card_a_id IN (
      SELECT id FROM soul_cards WHERE owner_id = auth.uid()
    )
  );
```

### 2.3 預計算觸發時機

| 觸發場景 | 動作 |
|---------|------|
| 用戶建立新 yin 卡 | 對所有其他 yin 卡算分，雙向寫入 ranking_cache |
| 用戶進 /ranking 且快取過期（>24hr） | 後端重新計算該用戶的排名 |
| 手動 API 觸發 | `POST /api/ranking/recompute` 供 admin 使用 |

### 2.4 API 端點

#### `GET /api/ranking`

讀取當前用戶的排行榜資料。

**Query Params:**
- `card_id` (required) — 用戶選擇的基準 soul_card ID

**Response:**
```json
{
  "rankings": [
    {
      "cache_id": "uuid",
      "rank": 1,
      "harmony": 97,
      "lust": 85,
      "soul": 92,
      "primary_track": "soul",
      "quadrant": "soulmate",
      "labels": ["月光獸", "火焰控制者"],
      "tracks": { "friend": 70, "passion": 85, "partner": 88, "soul": 92 }
    }
  ],
  "total": 42,
  "computed_at": "2026-03-02T10:00:00Z"
}
```

**注意：** Response 中不包含 card_b 的任何個人資料（display_name、birth_date、lat/lng 等）。

#### `POST /api/ranking/recompute`

觸發預計算。在用戶建立新 yin 卡或快取過期時呼叫。

**Body:**
```json
{ "card_id": "uuid" }
```

**流程：**
1. 驗證 card_id 屬於當前用戶
2. 查詢所有其他用戶的 yin 卡（`yin_yang = 'yin'` AND `owner_id != current_user`）
3. 逐一呼叫 astro-service `/compute-enriched`
4. UPSERT 結果到 ranking_cache
5. 回傳 `{ status: "ok", computed: N }`

---

## 3. 頁面設計

### 3.1 路由：`/ranking`

**頁面結構：**

```
┌─────────────────────────────────────────────┐
│  ✦ 命運排行榜                                │
│  你的靈魂與誰共振最深？                        │
│                                             │
│  ┌────────────────────────────┐             │
│  │  選擇你的命盤: [▼ 下拉選單]  │             │
│  └────────────────────────────┘             │
│                                             │
│  ┌─ #1 ─────────────────────────────────┐   │
│  │  🔥 97 分  │  靈魂伴侶軌道              │   │
│  │  「月光獸 × 火焰控制者」                 │   │
│  │  ██████████████████░░░ lust 85       │   │
│  │  ████████████████████░ soul 92       │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌─ #2 ─────────────────────────────────┐   │
│  │  💜 89 分  │  熱情火花軌道              │   │
│  │  「暗夜治療師 × 深淵守望者」             │   │
│  │  ████████████████████░░ lust 90      │   │
│  │  ██████████████░░░░░░░ soul 72       │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌─ #3 ─────────────────────────────────┐   │
│  │  ✦ 82 分  │  穩定夥伴軌道              │   │
│  │  「星塵旅人 × 根源守護者」              │   │
│  │  █████████████░░░░░░░ lust 68        │   │
│  │  ████████████████░░░░ soul 80        │   │
│  └──────────────────────────────────────┘   │
│          ...                                │
└─────────────────────────────────────────────┘
```

### 3.2 排名卡片顯示內容

**顯示：**
- 排名序號（#1, #2, ...）
- harmony 總分（大字）
- 主軌道中文標籤（靈魂伴侶 / 熱情火花 / 穩定夥伴 / 知心好友）
- 原型標籤組合（來自 labels，最多顯示 2 個）
- lust / soul 雙軸簡易進度條

**不顯示（隱私保護）：**
- 姓名 / display_name
- 出生日期 / 時間
- 出生地經緯度
- 性別
- 任何可辨識個人身份的資訊

### 3.3 簡介卡片（Modal）

點擊排名卡片後彈出：

```
┌──────────────────────────────────┐
│         ✦ 命運共振分析             │
│                                  │
│      ◆ 97 分 — 靈魂伴侶          │
│                                  │
│   ┌──── 四軌雷達圖 ────┐         │
│   │   friend: 70       │         │
│   │   passion: 85      │         │
│   │   partner: 88      │         │
│   │   soul: 92         │         │
│   └────────────────────┘         │
│                                  │
│   標籤：月光獸 × 火焰控制者        │
│   象限：soulmate                  │
│                                  │
│   [ 查看完整報告 →  ]             │
│                                  │
└──────────────────────────────────┘
```

**「查看完整報告」按鈕：**
- 點擊後觸發合盤計算（如果 ranking_cache 有完整 report_json 則直接用）
- 播放陰陽碰撞動畫 → 跳轉 `/report/[id]`

### 3.4 導航更新

NavBar `NAV_ITEMS` 新增：

| Label | Path | Icon (Material Symbols) |
|-------|------|------------------------|
| 命運排行 | `/ranking` | `leaderboard` |

---

## 4. 隱私保護機制

| 層級 | 措施 |
|------|------|
| DB RLS | ranking_cache 只能讀取自己為 card_a 的行 |
| API Response | 只回傳分數/標籤/軌道，不回傳 card_b 的任何個資 |
| 前端 | 不請求也不渲染任何對方的 birth_date/name/location |
| 排名匿名化 | 對方只以原型標籤呈現（如「月光獸」），無法反推身份 |

---

## 5. Token 門檻機制（⚠️ 日後實作）

> **重要備註：** 以下 token 門檻機制在 MVP 階段暫不實作，但架構設計需預留擴展空間。

### 5.1 規劃

- **上架排行榜門檻：** 用戶需付費或消耗 token 才能將自己的 yin 卡放上排行榜供他人配對。
  - 未付費用戶的 yin 卡不會出現在其他人的排行榜中。
  - 付費/消耗 token 後，卡片進入「公開配對池」。
- **查看完整報告門檻：** 點擊「查看完整報告」時消耗 1 token。
  - 排行榜瀏覽和簡介卡片免費。
  - 完整報告需付費解鎖。

### 5.2 預留設計

- `soul_cards` table 日後新增 `is_public BOOLEAN DEFAULT false` 欄位
  - 用戶付費後設為 `true`，該卡進入排行榜配對池
  - MVP 階段：所有 yin 卡預設參與排名（等同 `is_public = true`）
- `ranking_cache` 查詢日後加 `WHERE card_b.is_public = true` 過濾
- API 日後加 token 餘額檢查中間件
- 前端「查看完整報告」按鈕日後加 token 餘額確認彈窗

### 5.3 MVP 階段行為

- 所有 yin 卡自動參與排名，不需付費
- 查看完整報告不消耗 token
- `users.tokens` 欄位已存在（DEFAULT 3），日後直接啟用

---

## 6. 新增檔案清單

| 檔案 | 用途 |
|------|------|
| `supabase/migrations/015_ranking_cache.sql` | ranking_cache table + RLS + index |
| `app/ranking/page.tsx` | 排行榜頁面（選擇命盤 + 排名列表 + infinite scroll） |
| `app/api/ranking/route.ts` | GET: 讀取排名（支援 offset/limit 分頁） |
| `app/api/ranking/recompute/route.ts` | POST: 觸發增量預計算 |
| `components/RankingCard.tsx` | 排名卡片元件 |
| `components/RankingDetailModal.tsx` | 簡介卡片彈窗（四軌 + 標籤 + 查看報告按鈕） |
| `components/NavBar.tsx` | 新增「命運排行」nav item |
| `astro-service/main.py` | 新增 `POST /quick-score` 輕量評分端點 |
| `astro-service/matching.py` | 新增 `compute_quick_score()` 函數 |

---

## 7. 效能策略

原始 O(N²) 問題：N 個 yin 卡需要 N×(N-1) 次計算，100 人 = ~10,000 次，1000 人 = ~1,000,000 次。
以下三層策略組合解決：

### 7.1 輕量快速評分 API（核心）

在 astro-service 新增 `POST /quick-score` 端點：

- **只算：** harmony / lust / soul 三分 + primary_track + quadrant + labels
- **跳過：** ZWDS 紫微斗數、shadow engine 完整分析、detailed report_json
- **效能目標：** 每次呼叫 ~50ms（現有 /compute-enriched 約 ~500ms）
- **用途：** 排行榜排序和卡片顯示專用

```
排行榜瀏覽 → /quick-score（輕量）
查看完整報告 → /compute-enriched（完整）
```

### 7.2 增量計算

- **新用戶加入時：** 只算「新卡 vs 所有現有卡」= 2×(N-1) 次（雙向），不重算舊卡之間的結果
- **現有用戶更新卡片時：** 只重算「該卡 vs 所有其他卡」，刪除舊快取
- **永不全量重算：** ranking_cache 只做 UPSERT，已存在的配對不重複計算

```
N=100 時新加 1 人 → 只算 198 次（而非 10,000 次）
N=1000 時新加 1 人 → 只算 1,998 次（而非 1,000,000 次）
```

### 7.3 懶加載 + 分頁

- 用戶進 /ranking 時先載入 **top 20**
- 滾動到底部時 infinite scroll 載入下一批 20 筆
- 後端 `GET /api/ranking?card_id=xxx&offset=0&limit=20`
- **首次進頁面若無快取：** 即時對所有其他 yin 卡跑 /quick-score，結果存入 ranking_cache，前端顯示 loading 動畫
- **後續進入：** 直接讀 ranking_cache，毫秒級回應

### 7.4 快取過期策略

| 場景 | 行為 |
|------|------|
| 快取存在且 < 24hr | 直接讀取，不重算 |
| 快取存在但 > 24hr | 先顯示舊資料，背景靜默重算，完成後前端刷新 |
| 快取不存在（新配對） | 即時計算 + 寫入快取 |
| astro-service 不可用 | 顯示最近快取，標註「資料更新於 XX 前」 |

### 7.5 計算流程圖

```
用戶進 /ranking，選擇 card_id
        ↓
GET /api/ranking?card_id=xxx&offset=0&limit=20
        ↓
查 ranking_cache WHERE card_a_id = xxx
        ↓
  ┌─ 有快取且未過期 ─→ 直接回傳排序結果
  │
  └─ 無快取 / 過期 ─→ 查所有其他 yin 卡
                         ↓
                    過濾已有快取的（增量）
                         ↓
                    批次呼叫 /quick-score
                         ↓
                    UPSERT ranking_cache
                         ↓
                    回傳排序結果
```

---

## 8. Token 付費進階排行（⚠️ 日後實作）

> **備註：** 付費用戶日後可解鎖完整版排行榜，使用 `/compute-enriched` 計算，包含 ZWDS 紫微斗數、shadow engine、完整 report_json 的分數。

### 8.1 兩層排行榜

| 層級 | 計算端點 | 包含內容 | 門檻 |
|------|---------|---------|------|
| 免費版（MVP） | `/quick-score` | harmony/lust/soul + 軌道 + 標籤 | 無 |
| 付費版（日後） | `/compute-enriched` | 以上 + ZWDS 宮位分數 + shadow 觸發 + 完整報告 | 消耗 token / 訂閱 |

### 8.2 付費版額外顯示

- ZWDS 12 宮位契合度分數
- Shadow engine 觸發標籤（凱龍傷口、Vertex 靈魂觸發等）
- 更精確的分數（含 shadow modifier 調整）
- 排名卡片上標示「✦ 完整分析」徽章

---

## 9. 技術注意事項

- **雙向快取：** A→B 和 B→A 的分數可能不同（交叉相位不對稱），需分別計算和儲存。
- **astro-service /quick-score：** 需新增此端點，只跑 matching.py 的核心公式，跳過 ZWDS bridge 和 shadow_engine 完整分析。
- **並發控制：** 批次呼叫 /quick-score 時使用 Promise.allSettled + concurrency limit（建議 5 並發），避免打爆 astro-service。
- **soul_cards RLS 繞行：** ranking API 需要讀取其他用戶的 yin 卡來計算配對，需使用 service_role key（server-side only），前端永遠不會接觸到其他用戶的原始資料。
