# DESTINY — Photo Pipeline 技術文件

**Last Updated:** 2026-02-15

---

## 概觀

DESTINY 的照片系統採用 **漸進式揭露 (Progressive Reveal)** 設計：用戶上傳的照片會自動進行高斯模糊處理，隨著互動深入逐步解鎖清晰度。

---

## 上傳流程

```
┌────────────────┐
│  前端 (Browser) │
│  File Input ×2  │
└───────┬────────┘
        │ FormData (multipart/form-data, 二進制傳輸)
        ▼
┌────────────────────────────────────┐
│  POST /api/onboarding/photos       │
│  (Next.js API Route, server-side)  │
├────────────────────────────────────┤
│  1. Auth 驗證 (supabase.auth)      │
│  2. 基本驗證 (type/size)           │
│  3. file.arrayBuffer() → Buffer    │
│  4. sharp(buffer).blur(30).jpeg()  │
│  5. Upload to Supabase Storage     │
│  6. Insert DB record (photos 表)   │
│  7. Update onboarding_step         │
└────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│  Supabase Storage (photos bucket)  │
│                                    │
│  {user_id}/                        │
│  ├── original_1.jpg  ← 原圖       │
│  ├── original_2.jpg  ← 原圖       │
│  ├── blurred_1.jpg   ← 模糊版     │
│  └── blurred_2.jpg   ← 模糊版     │
└────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│  DB: photos 表                     │
│  ┌──────────┬────┬──────────────┐  │
│  │ user_id  │slot│ original_path│  │
│  │          │    │ blurred_path │  │
│  └──────────┴────┴──────────────┘  │
└────────────────────────────────────┘
```

---

## Storage 結構

```
photos/                          ← Supabase Storage bucket
└── {user_id}/                   ← 每個用戶一個資料夾
    ├── original_1.jpg           ← 照片 1 原圖 (JPEG)
    ├── original_2.jpg           ← 照片 2 原圖 (JPEG)
    ├── blurred_1.jpg            ← 照片 1 模糊版 (blur=30, quality=60%)
    └── blurred_2.jpg            ← 照片 2 模糊版 (blur=30, quality=60%)
```

**每位用戶 = 4 個檔案**（2 張照片 × 2 版本）

---

## 圖片處理 (sharp)

| 參數 | 值 | 說明 |
|------|---|------|
| blur sigma | `30` | 高斯模糊強度，30 = 重度模糊，只剩色調和輪廓 |
| jpeg quality | `60%` | 模糊版壓縮率較高，減少儲存空間 |
| format | JPEG | 統一輸出格式，即使輸入為 PNG/WebP |

```typescript
// 模糊處理程式碼
const blurredBuffer = await sharp(buffer)
  .blur(30)
  .jpeg({ quality: 60 })
  .toBuffer()
```

---

## 伺服器端驗證規則

| 規則 | 條件 | 錯誤訊息 |
|------|------|---------|
| MIME Type | `image/jpeg`, `image/png`, `image/webp` | `Invalid file type. Only JPEG, PNG, and WebP are accepted.` |
| 檔案大小 | 最大 10MB per file | `File too large. Maximum size is 10MB.` |
| 必要性 | photo1 和 photo2 都必須上傳 | `Both photo1 and photo2 are required` |

### 前端驗證 (page.tsx)

- File input 設定 `accept="image/*"` 限制選擇器
- 兩張照片都選完後才能點 Continue

### 目前未驗證項目

- 圖片是否包含人臉 (Phase 2)
- NSFW/不當內容過濾 (Phase 2)
- 圖片尺寸/解析度 (可透過 sharp metadata 實作)
- 重複照片偵測

---

## Progressive Unlock（漸進式揭露）

照片清晰度隨互動深度提升：

| Level | 觸發條件 | 顯示路徑 | 清晰度 |
|-------|---------|---------|--------|
| **Lv.1** | 0–10 則訊息 | `blurred_*.jpg` | 高斯模糊 (只見色調輪廓) |
| **Lv.2** | 10–50 則訊息 | `half_blurred_*.jpg` (待實作) | 50% 清晰度 |
| **Lv.3** | 50+ 則訊息 或 3+ 分鐘通話 | `original_*.jpg` | 完整高清 |

> **Note:** 目前只生成 `blurred` 和 `original` 兩個版本。Lv.2 的 `half_blurred` 需在 Phase C 實作半模糊版本（`sharp.blur(10)`）。

### 解鎖邏輯（待實作）

```typescript
// connections 表的 sync_level 決定照片路徑
function getPhotoPath(photo: Photo, syncLevel: number): string {
  if (syncLevel >= 3) return photo.original_path   // Lv.3: 原圖
  if (syncLevel >= 2) return photo.half_blur_path   // Lv.2: 半模糊
  return photo.blurred_path                         // Lv.1: 全模糊
}
```

---

## DB Schema (photos 表)

```sql
CREATE TABLE photos (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  slot        INT NOT NULL CHECK (slot IN (1, 2)),
  original_path TEXT NOT NULL,    -- Storage 路徑: {user_id}/original_{slot}.jpg
  blurred_path  TEXT NOT NULL,    -- Storage 路徑: {user_id}/blurred_{slot}.jpg
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, slot)
);
```

---

## RLS Policies

| Policy | 規則 |
|--------|------|
| Upload | `auth.uid() = user_id` (只能上傳自己的照片) |
| View | 自己 + 配對對象 (透過 daily_matches / connections join) |
| Delete | `auth.uid() = user_id` |

---

## 相關檔案

| 檔案 | 用途 |
|------|------|
| `src/app/api/onboarding/photos/route.ts` | 上傳 API (驗證 + sharp + Storage) |
| `src/app/onboarding/photos/page.tsx` | 上傳 UI (File input + FormData) |
| `src/__tests__/api/onboarding-photos.test.ts` | 5 個測試 (upload, auth, missing, type, size) |
| `supabase/migrations/001_initial_schema.sql` | photos 表 + RLS + Storage bucket |

---

## Future Roadmap: 照片驗證升級計畫

| Phase | Feature | 技術方案 | 狀態 | 說明 |
|-------|---------|---------|------|------|
| **MVP** | 基本驗證 | MIME type + file size + sharp integrity | **Done** ✅ | 防止非圖片檔案和超大檔案 |
| **Phase 2** | AI 人臉偵測 | Claude Vision API | 規劃中 | 上傳時送圖片到 Claude，問「此圖片是否包含清晰的人臉？」，拒絕食物照、風景照等 |
| **Phase 2** | NSFW 過濾 | Claude Vision API | 規劃中 | 與人臉偵測同一 API call，一石二鳥。Prompt: 「此圖片是否包含不當內容？」 |
| **Phase 2** | 半模糊版本 | `sharp.blur(10).jpeg({quality:75})` | 規劃中 | 為 Lv.2 生成 `half_blurred_*.jpg`，上傳時一次生成 3 個版本 |
| **Phase 3** | 人臉品質分析 | Claude Vision API | 規劃中 | 偵測遮擋、模糊、極度側臉 → 建議用戶重新拍攝 |
| **Phase 3** | 前端預檢 | TensorFlow.js (face-detection) | 規劃中 | 上傳前在瀏覽器端初步偵測是否有人臉，減少無效上傳 |
| **Phase 3** | 圖片壓縮 | sharp resize + 前端壓縮 | 規劃中 | 大圖自動縮小到 2000px 長邊，減少 Storage 用量 |

### Phase 2 Claude Vision 偵測範例（參考用）

```typescript
// 未來實作參考 — src/lib/ai/photo-validator.ts
import Anthropic from '@anthropic-ai/sdk'

const client = new Anthropic()

export async function validatePhotoContent(imageBuffer: Buffer): Promise<{
  hasFace: boolean
  isNSFW: boolean
  reason?: string
}> {
  const base64 = imageBuffer.toString('base64')

  const response = await client.messages.create({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 200,
    messages: [{
      role: 'user',
      content: [
        {
          type: 'image',
          source: { type: 'base64', media_type: 'image/jpeg', data: base64 },
        },
        {
          type: 'text',
          text: 'Analyze this photo for a dating app. Answer in JSON: {"has_face": bool, "is_nsfw": bool, "reason": "..."}. has_face = contains a clearly visible human face. is_nsfw = contains nudity or inappropriate content.',
        },
      ],
    }],
  })

  const json = JSON.parse(response.content[0].text)
  return { hasFace: json.has_face, isNSFW: json.is_nsfw, reason: json.reason }
}
```

---

## 效能考量

| 項目 | 現況 | 優化方向 |
|------|------|---------|
| 上傳時間 | 2 張照片序列處理 | 可改為 `Promise.all` 並行處理 |
| Storage 用量 | 4 files × ~500KB = ~2MB/user | 未來加壓縮可降到 ~800KB/user |
| sharp 記憶體 | 每次處理約 20-50MB | Serverless 環境注意 memory limit |
| 重複上傳 | `upsert: true` 覆蓋舊檔 | 正確行為，不會產生孤立檔案 |
