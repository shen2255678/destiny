# Profile Avatar Feature Design

## Goal

Let users personalize each soul card with an astrology-themed emoji icon.
The save-card flow in `/lounge` becomes a 2-step wizard (choose icon → name).
The `/me` page shows each card's icon and lets the user edit it.

## DB Schema (migration 016)

```sql
ALTER TABLE public.soul_cards
  ADD COLUMN IF NOT EXISTS avatar_icon TEXT NOT NULL DEFAULT '✦',
  ADD COLUMN IF NOT EXISTS avatar_url  TEXT;
```

**Display priority:** `avatar_url` (custom upload, Phase 2) → `avatar_icon` (emoji).
Both columns are added now so Phase 2 (custom image upload) needs no migration.

## Icon Set (36 icons, 6 groups)

```
♈ ♉ ♊ ♋ ♌ ♍   ← 黃道十二宮
♎ ♏ ♐ ♑ ♒ ♓
☽ ☀ ✦ ☿ ♀ ♂   ← 行星符號
♃ ♄ ♅ ♆ ⚸ ⚷
⭐ 🌙 💫 ✨ 🔮 🌸  ← 神秘主題
🌊 🌀 ⚡ 🪐 🌌 🌟
```

Default icon: `✦`

## Component: `ProfileIconPicker`

Path: `destiny-mvp/components/ProfileIconPicker.tsx`

Props:
```ts
interface Props {
  value: string;
  onChange: (icon: string) => void;
  disabled?: boolean;
}
```

- 6×6 grid of icon buttons
- Selected icon has highlighted border (`#d98695` ring)
- Bottom row: "📷 上傳自訂圖片" button — `disabled`, label "即將推出"

## Component: `SaveCardModal`

Path: `destiny-mvp/components/SaveCardModal.tsx`

A 2-step modal overlay used in `/lounge` for saving a new card.

**Step 1: 選擇命盤圖示**
- Step indicator: `● Step 1  ○ Step 2`
- `ProfileIconPicker` (full 36-icon grid)
- [下一步 →] button (disabled until icon selected, but default `✦` pre-selected)

**Step 2: 為命盤命名**
- Step indicator: `○ Step 1  ● Step 2`
- Preview: large selected icon (40px)
- Text input: "命盤名稱" placeholder "例：小羊的星盤"
- [← 上一步] / [建立命盤 ✓] buttons

**Props:**
```ts
interface Props {
  person: "A" | "B";
  onConfirm: (label: string, avatarIcon: string) => Promise<void>;
  onClose: () => void;
}
```

## Changes to `/lounge/page.tsx`

- Remove current inline save form (input + 確認/取消 buttons)
- "💾 儲存此命盤" button → opens `SaveCardModal`
- `SaveCardModal.onConfirm` calls `POST /api/profiles` with `avatar_icon` included
- On success: add card to `profiles` state, close modal

## Changes to `/api/profiles/route.ts`

**POST body** — add `avatar_icon?: string`:
```ts
body: {
  label: string;
  birth_date: string;
  birth_time?: string;
  lat: number; lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang?: "yin" | "yang";
  avatar_icon?: string;  // ← new
}
```

**Validation:** `avatar_icon` max 8 chars (emoji safe), defaults to `'✦'`.

**DB insert** — add `avatar_icon: body.avatar_icon ?? '✦'`.

**GET select** — add `avatar_icon, avatar_url` to select string.

## Changes to `/api/profiles/[id]/route.ts`

**PATCH** — allow updating `avatar_icon` (and `display_name`):
```ts
body: { avatar_icon?: string; display_name?: string }
```

## Changes to `/me/MeClient.tsx`

Each soul card shows its `avatar_icon` in the card header (48px circle, gradient bg).

- Click the icon → opens an inline 2-step edit flow (same steps as SaveCardModal but in edit mode)
- On confirm → `PATCH /api/profiles/[id]` with `{ avatar_icon, display_name }`
- `/me/page.tsx` must also include `avatar_icon` in the Supabase `.select()`

## Affected Files Summary

| File | Change |
|------|--------|
| `supabase/migrations/016_avatar.sql` | ADD COLUMN avatar_icon + avatar_url |
| `components/ProfileIconPicker.tsx` | NEW — 36-icon grid picker |
| `components/SaveCardModal.tsx` | NEW — 2-step wizard modal |
| `app/lounge/page.tsx` | Replace inline save form with SaveCardModal |
| `app/api/profiles/route.ts` | Accept + persist avatar_icon |
| `app/api/profiles/[id]/route.ts` | PATCH endpoint for avatar_icon |
| `app/me/MeClient.tsx` | Display + edit avatar_icon per card |
| `app/me/page.tsx` | Add avatar_icon to Supabase select |

## Out of Scope (Phase 2)

- Custom image upload (Supabase Storage `avatars/` bucket)
- Supabase Storage RLS policy for avatars
- PATCH `avatar_url` endpoint
