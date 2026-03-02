# Profile Avatar Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add astrology-themed emoji icon picker to soul card creation and editing, with a 2-step wizard (icon → name) in `/lounge` and icon display/edit on `/me`.

**Architecture:** DB gets `avatar_icon` + `avatar_url` (future) columns. A shared `ProfileIconPicker` component renders the 36-icon grid. A `SaveCardModal` wraps it in a 2-step wizard. `/lounge` triggers the modal instead of its current inline save form. `/me` shows each card's icon and opens the same modal for editing.

**Tech Stack:** Next.js 15 App Router, TypeScript, Supabase PostgreSQL, inline CSS (no Tailwind — this project uses inline styles consistently)

**Working directory:** `E:\下班自學用\destiny\destiny-mvp`

---

## Task 1: DB migration 016 — add avatar columns

**Files:**
- Create: `supabase/migrations/016_avatar.sql`

**Step 1: Create the migration file**

```sql
-- Migration 016: add avatar_icon and avatar_url to soul_cards
ALTER TABLE public.soul_cards
  ADD COLUMN IF NOT EXISTS avatar_icon TEXT NOT NULL DEFAULT '✦',
  ADD COLUMN IF NOT EXISTS avatar_url  TEXT;

COMMENT ON COLUMN public.soul_cards.avatar_icon IS 'Emoji icon for soul card display. Default ✦.';
COMMENT ON COLUMN public.soul_cards.avatar_url  IS 'Custom uploaded image URL (Phase 2). Overrides avatar_icon when set.';
```

**Step 2: Apply the migration**

```bash
cd "E:\下班自學用\destiny\destiny-mvp"
npx supabase db push
```

Expected output: Migration 016 applied successfully.

If `supabase` CLI is not linked, apply via Supabase dashboard SQL editor instead (copy the SQL above).

**Step 3: Verify the columns exist**

In Supabase dashboard → Table Editor → `soul_cards` → confirm `avatar_icon` (text, not null, default `✦`) and `avatar_url` (text, nullable) columns are present.

**Step 4: Commit**

```bash
git add supabase/migrations/016_avatar.sql
git commit -m "feat(db): add avatar_icon + avatar_url to soul_cards (migration 016)"
```

---

## Task 2: `ProfileIconPicker` component

**Files:**
- Create: `components/ProfileIconPicker.tsx`

**Step 1: Create the component**

```tsx
"use client";

import React from "react";

export const ICON_SET = [
  // 黃道十二宮
  "♈", "♉", "♊", "♋", "♌", "♍",
  "♎", "♏", "♐", "♑", "♒", "♓",
  // 行星符號
  "☽", "☀", "✦", "☿", "♀", "♂",
  "♃", "♄", "♅", "♆", "⚸", "⚷",
  // 神秘主題
  "⭐", "🌙", "💫", "✨", "🔮", "🌸",
  "🌊", "🌀", "⚡", "🪐", "🌌", "🌟",
] as const;

interface Props {
  value: string;
  onChange: (icon: string) => void;
  disabled?: boolean;
}

export function ProfileIconPicker({ value, onChange, disabled }: Props) {
  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 8,
          marginBottom: 16,
        }}
      >
        {ICON_SET.map((icon) => (
          <button
            key={icon}
            type="button"
            disabled={disabled}
            onClick={() => onChange(icon)}
            style={{
              width: 44,
              height: 44,
              borderRadius: 10,
              border: icon === value
                ? "2px solid #d98695"
                : "2px solid rgba(255,255,255,0.4)",
              background: icon === value
                ? "rgba(217,134,149,0.15)"
                : "rgba(255,255,255,0.25)",
              fontSize: 20,
              cursor: disabled ? "not-allowed" : "pointer",
              transition: "border 0.15s, background 0.15s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              lineHeight: 1,
            }}
          >
            {icon}
          </button>
        ))}
      </div>

      {/* Phase 2 placeholder */}
      <button
        type="button"
        disabled
        style={{
          width: "100%",
          padding: "9px 0",
          borderRadius: 10,
          border: "1px dashed rgba(140,112,137,0.35)",
          background: "transparent",
          color: "#a08a9d",
          fontSize: 12,
          cursor: "not-allowed",
          letterSpacing: "0.03em",
        }}
      >
        📷 上傳自訂圖片 · 即將推出
      </button>
    </div>
  );
}
```

**Step 2: Verify it builds**

```bash
cd "E:\下班自學用\destiny\destiny-mvp"
npx tsc --noEmit
```

Expected: No errors.

**Step 3: Commit**

```bash
git add components/ProfileIconPicker.tsx
git commit -m "feat(ui): add ProfileIconPicker component (36-icon astro grid)"
```

---

## Task 3: `SaveCardModal` component — 2-step wizard

**Files:**
- Create: `components/SaveCardModal.tsx`

**Step 1: Create the component**

```tsx
"use client";

import React, { useState } from "react";
import { ProfileIconPicker } from "./ProfileIconPicker";

interface Props {
  person: "A" | "B";
  defaultName?: string;
  onConfirm: (label: string, avatarIcon: string) => Promise<void>;
  onClose: () => void;
}

const overlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(30,10,35,0.55)",
  backdropFilter: "blur(4px)",
  zIndex: 1000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px",
};

const modal: React.CSSProperties = {
  background: "rgba(255,255,255,0.92)",
  backdropFilter: "blur(16px)",
  borderRadius: 24,
  padding: "28px 24px",
  width: "100%",
  maxWidth: 400,
  boxShadow: "0 20px 60px rgba(92,64,89,0.25)",
};

export function SaveCardModal({ person, defaultName = "", onConfirm, onClose }: Props) {
  const [step, setStep] = useState<1 | 2>(1);
  const [icon, setIcon] = useState("✦");
  const [label, setLabel] = useState(defaultName);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleConfirm() {
    if (!label.trim()) { setError("請輸入命盤名稱"); return; }
    setSaving(true);
    setError("");
    try {
      await onConfirm(label.trim(), icon);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "儲存失敗，請再試一次");
      setSaving(false);
    }
  }

  return (
    <div style={overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={modal}>
        {/* Step indicator */}
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 20 }}>
          {([1, 2] as const).map((s) => (
            <div
              key={s}
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: step === s ? "#d98695" : "rgba(140,112,137,0.3)",
                transition: "background 0.2s",
              }}
            />
          ))}
        </div>

        {step === 1 ? (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#5c4059", marginBottom: 4 }}>
              選擇命盤圖示
            </h2>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 16 }}>
              為「{person === "A" ? "命盤 A" : "命盤 B"}」挑選一個象徵符號
            </p>
            <ProfileIconPicker value={icon} onChange={setIcon} />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setStep(2)}
                style={{
                  padding: "10px 24px",
                  borderRadius: 999,
                  background: "linear-gradient(135deg, #d98695, #b86e7d)",
                  color: "#fff",
                  border: "none",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                下一步 →
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#5c4059", marginBottom: 4 }}>
              為命盤命名
            </h2>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 20 }}>
              取一個你記得住的名字
            </p>

            {/* Selected icon preview */}
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 56,
                  height: 56,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, rgba(217,134,149,0.2), rgba(124,92,138,0.2))",
                  fontSize: 28,
                  border: "2px solid rgba(217,134,149,0.4)",
                }}
              >
                {icon}
              </div>
            </div>

            <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 6 }}>
              命盤名稱
            </label>
            <input
              value={label}
              onChange={(e) => { setLabel(e.target.value); setError(""); }}
              placeholder="例：小羊的星盤"
              maxLength={50}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 12,
                border: error ? "1px solid #c0392b" : "1px solid rgba(140,112,137,0.3)",
                background: "rgba(255,255,255,0.6)",
                fontSize: 14,
                color: "#5c4059",
                outline: "none",
                boxSizing: "border-box",
              }}
              onKeyDown={(e) => { if (e.key === "Enter") handleConfirm(); }}
            />
            {error && (
              <p style={{ color: "#c0392b", fontSize: 12, marginTop: 4 }}>{error}</p>
            )}

            <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={saving}
                style={{
                  flex: 1,
                  padding: "10px 0",
                  borderRadius: 999,
                  background: "transparent",
                  border: "1px solid rgba(140,112,137,0.35)",
                  color: "#8c7089",
                  fontSize: 13,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                ← 上一步
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={saving}
                style={{
                  flex: 2,
                  padding: "10px 0",
                  borderRadius: 999,
                  background: saving ? "rgba(217,134,149,0.4)" : "linear-gradient(135deg, #d98695, #b86e7d)",
                  color: "#fff",
                  border: "none",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                {saving ? "儲存中..." : "建立命盤 ✓"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Verify it builds**

```bash
npx tsc --noEmit
```

Expected: No errors.

**Step 3: Commit**

```bash
git add components/SaveCardModal.tsx
git commit -m "feat(ui): add SaveCardModal 2-step wizard (icon → name)"
```

---

## Task 4: Update `/api/profiles/route.ts` — accept `avatar_icon`

**Files:**
- Modify: `app/api/profiles/route.ts`

The current POST handler ignores `avatar_icon`. Add it to the body type, validate it, and persist it.

**Step 1: Update the body type and validation**

In `app/api/profiles/route.ts`, find the `body` type declaration (around line 27) and the insert call (around line 107). Make these changes:

```typescript
// Change the body type from:
let body: {
  label: string;
  birth_date: string;
  birth_time?: string;
  lat: number;
  lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang?: "yin" | "yang";
};

// To:
let body: {
  label: string;
  birth_date: string;
  birth_time?: string;
  lat: number;
  lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang?: "yin" | "yang";
  avatar_icon?: string;
};
```

Add validation after the existing `data_tier` check (around line 53), before the `try` block for chart calculation:

```typescript
if (body.avatar_icon !== undefined && (typeof body.avatar_icon !== "string" || body.avatar_icon.length > 8)) {
  return NextResponse.json({ error: "avatar_icon must be a string ≤8 chars" }, { status: 400 });
}
```

**Step 2: Add `avatar_icon` to the DB insert**

Find the `supabase.from("soul_cards").insert({...})` call and add:

```typescript
avatar_icon: body.avatar_icon ?? "✦",
```

So the insert object becomes:

```typescript
.insert({
  owner_id: user.id,
  display_name: body.label,
  birth_date: body.birth_date,
  birth_time: body.birth_time || null,
  lat: body.lat,
  lng: body.lng,
  data_tier: body.data_tier,
  gender: body.gender,
  yin_yang: body.yin_yang ?? "yang",
  avatar_icon: body.avatar_icon ?? "✦",   // ← add this line
  natal_cache,
})
```

**Step 3: Add `avatar_icon` to GET select and POST select**

In the GET handler, update the select string:
```typescript
.select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, profile_card_data, ideal_match_data, avatar_icon, avatar_url, created_at")
```

In the POST insert's `.select(...)` at the end:
```typescript
.select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, avatar_icon")
```

**Step 4: Verify it builds**

```bash
npx tsc --noEmit
```

Expected: No errors.

**Step 5: Commit**

```bash
git add app/api/profiles/route.ts
git commit -m "feat(api): accept and persist avatar_icon in POST /api/profiles"
```

---

## Task 5: Update `/api/profiles/[id]/route.ts` — PATCH supports `avatar_icon` + `display_name`

**Files:**
- Modify: `app/api/profiles/[id]/route.ts`

The current PATCH only accepts `yin_yang`. Extend it to also accept `avatar_icon` and `display_name`.

**Step 1: Replace the PATCH body type and validation**

Find the current body type declaration (line 14) and validation:

```typescript
// Replace current body type:
let body: { yin_yang?: "yin" | "yang" };

// With:
let body: {
  yin_yang?: "yin" | "yang";
  avatar_icon?: string;
  display_name?: string;
};
```

Replace the current validation block (lines 21–27) that rejects if no `yin_yang`:

```typescript
// Replace:
if (body.yin_yang !== undefined && !["yin", "yang"].includes(body.yin_yang)) {
  return NextResponse.json({ error: "yin_yang must be 'yin' or 'yang'" }, { status: 400 });
}

if (body.yin_yang === undefined) {
  return NextResponse.json({ error: "At least one field (yin_yang) is required" }, { status: 400 });
}

// With:
if (body.yin_yang !== undefined && !["yin", "yang"].includes(body.yin_yang)) {
  return NextResponse.json({ error: "yin_yang must be 'yin' or 'yang'" }, { status: 400 });
}
if (body.avatar_icon !== undefined && (typeof body.avatar_icon !== "string" || body.avatar_icon.length > 8)) {
  return NextResponse.json({ error: "avatar_icon must be a string ≤8 chars" }, { status: 400 });
}
if (body.display_name !== undefined && (typeof body.display_name !== "string" || body.display_name.length < 1 || body.display_name.length > 50)) {
  return NextResponse.json({ error: "display_name must be 1–50 chars" }, { status: 400 });
}
if (body.yin_yang === undefined && body.avatar_icon === undefined && body.display_name === undefined) {
  return NextResponse.json({ error: "At least one field required" }, { status: 400 });
}
```

**Step 2: Add new fields to the updates object**

Find the `updates` object build (line 28) and extend it:

```typescript
const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
if (body.yin_yang !== undefined)    updates.yin_yang = body.yin_yang;
if (body.avatar_icon !== undefined) updates.avatar_icon = body.avatar_icon;
if (body.display_name !== undefined) updates.display_name = body.display_name;
```

**Step 3: Update the select string to return `avatar_icon`**

```typescript
.select("id, yin_yang, avatar_icon, display_name")
```

**Step 4: Verify build**

```bash
npx tsc --noEmit
```

**Step 5: Commit**

```bash
git add "app/api/profiles/[id]/route.ts"
git commit -m "feat(api): PATCH /api/profiles/[id] now accepts avatar_icon + display_name"
```

---

## Task 6: Update `/lounge/page.tsx` — replace inline save form with `SaveCardModal`

**Files:**
- Modify: `app/lounge/page.tsx`

The current save form is an inline `<div>` with a text input and confirm/cancel buttons. Replace it with the `SaveCardModal`.

**Step 1: Add import at the top of the file**

After the existing imports (around line 7), add:

```typescript
import { SaveCardModal } from "@/components/SaveCardModal";
```

**Step 2: Update the `SavedProfile` interface**

Add `avatar_icon` to it:

```typescript
interface SavedProfile {
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
  lat: number;
  lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang: string;
  natal_cache: Record<string, unknown> | null;
  avatar_icon: string;   // ← add
}
```

**Step 3: Update state — remove `saveLabel`, keep `saving` as `null | "A" | "B"`**

The current state already has `saving` and `saveLabel`. Keep `saving`, remove `saveLabel` usage (the label is now collected inside the modal). `saveStatus` stays for showing the success/error toast.

**Step 4: Replace the inline save form for Person A**

Find the `{saving === "A" ? (...) : (...)}` block for Person A (lines 234–281) and replace the entire block with:

```tsx
{saving === "A" && (
  <SaveCardModal
    person="A"
    defaultName={a.name !== "Person A" ? a.name : ""}
    onConfirm={async (label, avatarIcon) => {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label,
          avatar_icon: avatarIcon,
          birth_date: a.birth_date,
          birth_time: a.birth_time || undefined,
          lat: a.lat, lng: a.lng,
          data_tier: a.data_tier, gender: a.gender,
        }),
      });
      if (res.status === 403) { setSaveStatus("❌ 免費方案限 1 張，升級解鎖更多"); setSaving(null); return; }
      if (!res.ok) throw new Error("儲存失敗");
      const saved = await res.json() as SavedProfile;
      setProfiles((prev) => [saved, ...prev]);
      setSaving(null);
      setSaveStatus("✓ 已儲存");
      setTimeout(() => setSaveStatus(""), 3000);
    }}
    onClose={() => setSaving(null)}
  />
)}
{saving !== "A" && (
  <button
    onClick={() => setSaving("A")}
    style={{ fontSize: 11, color: "#8c7089", background: "transparent", border: "none", cursor: "pointer", padding: "4px 0" }}
  >💾 儲存此命盤</button>
)}
```

**Step 5: Do the same for Person B**

Replace the `{saving === "B" ? (...) : (...)}` block (lines 306–353) with the identical pattern but `person="B"` and using `b.*` values:

```tsx
{saving === "B" && (
  <SaveCardModal
    person="B"
    defaultName={b.name !== "Person B" ? b.name : ""}
    onConfirm={async (label, avatarIcon) => {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label,
          avatar_icon: avatarIcon,
          birth_date: b.birth_date,
          birth_time: b.birth_time || undefined,
          lat: b.lat, lng: b.lng,
          data_tier: b.data_tier, gender: b.gender,
        }),
      });
      if (res.status === 403) { setSaveStatus("❌ 免費方案限 1 張，升級解鎖更多"); setSaving(null); return; }
      if (!res.ok) throw new Error("儲存失敗");
      const saved = await res.json() as SavedProfile;
      setProfiles((prev) => [saved, ...prev]);
      setSaving(null);
      setSaveStatus("✓ 已儲存");
      setTimeout(() => setSaveStatus(""), 3000);
    }}
    onClose={() => setSaving(null)}
  />
)}
{saving !== "B" && (
  <button
    onClick={() => setSaving("B")}
    style={{ fontSize: 11, color: "#8c7089", background: "transparent", border: "none", cursor: "pointer", padding: "4px 0" }}
  >💾 儲存此命盤</button>
)}
```

**Step 6: Update `ProfilePicker` to show avatar icon**

Find the `ProfilePicker` component (lines 48–78) and update each `<option>` to include the icon:

```tsx
{profiles.map((p) => (
  <option key={p.id} value={p.id}>
    {p.avatar_icon ?? "✦"} {p.display_name}
  </option>
))}
```

**Step 7: Remove unused `saveLabel` state** (if still present):

```typescript
// Delete this line if it exists:
const [saveLabel, setSaveLabel] = useState("");
```

**Step 8: Verify build**

```bash
npx tsc --noEmit
npm run build
```

Expected: No errors.

**Step 9: Commit**

```bash
git add app/lounge/page.tsx
git commit -m "feat(lounge): replace inline save form with SaveCardModal 2-step wizard"
```

---

## Task 7: Update `/me/page.tsx` and `MeClient.tsx` — show + edit avatar icon

**Files:**
- Modify: `app/me/page.tsx`
- Modify: `app/me/MeClient.tsx`

### Part A: `page.tsx` — add `avatar_icon` to Supabase select

In `app/me/page.tsx`, find the `.select(...)` string (line 12) and add `avatar_icon`:

```typescript
.select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, avatar_icon, created_at")
```

### Part B: `MeClient.tsx` — add icon to profile interface

At the top of `MeClient.tsx`, find the `ProfileData` or equivalent interface (if it exists, else find where `profile` prop type is defined). Search for the `MeClient` function signature and update the profile type to include `avatar_icon`:

Add to the profile prop type:
```typescript
avatar_icon?: string;
```

### Part C: `MeClient.tsx` — display icon in card header

Find the section in `MeClient.tsx` that renders the profile card header. It currently shows `display_name` and other info. Add the icon display before the name.

Search for the first `{profile.display_name}` rendering in a heading/title context. Before it, add:

```tsx
{/* Avatar icon */}
<div
  style={{
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 56,
    height: 56,
    borderRadius: "50%",
    background: "linear-gradient(135deg, rgba(217,134,149,0.25), rgba(124,92,138,0.25))",
    border: "2px solid rgba(217,134,149,0.4)",
    fontSize: 26,
    marginBottom: 8,
    cursor: "pointer",
  }}
  onClick={() => setEditingAvatar(true)}
  title="點擊更換圖示"
>
  {profile.avatar_icon ?? "✦"}
</div>
```

### Part D: `MeClient.tsx` — add edit state and `SaveCardModal`

1. Add import at top of file:
```typescript
import { SaveCardModal } from "@/components/SaveCardModal";
```

2. Add state inside the `MeClient` component (near other `useState` calls):
```typescript
const [editingAvatar, setEditingAvatar] = useState(false);
```

3. After the existing modal/overlay rendering (or before the closing `</div>` of the component's return), add:

```tsx
{editingAvatar && profile && (
  <SaveCardModal
    person="A"
    defaultName={profile.display_name}
    onConfirm={async (label, avatarIcon) => {
      const res = await fetch(`/api/profiles/${profile.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ avatar_icon: avatarIcon, display_name: label }),
      });
      if (!res.ok) throw new Error("更新失敗");
      // Update local state to reflect change without full page reload
      profile.avatar_icon = avatarIcon;
      profile.display_name = label;
      setEditingAvatar(false);
    }}
    onClose={() => setEditingAvatar(false)}
  />
)}
```

> **Note:** `MeClient.tsx` is a large file (~600+ lines). When reading it to find where to insert, look for the profile card rendering section — it will have a large `display_name` heading and `yin_yang` mode toggle. Insert the avatar circle just above the `display_name` heading.

**Step: Verify build**

```bash
npx tsc --noEmit
npm run build
```

Expected: No errors, build succeeds.

**Step: Commit**

```bash
git add app/me/page.tsx app/me/MeClient.tsx
git commit -m "feat(me): show and edit avatar_icon on soul card"
```

---

## Manual Testing Checklist

After all tasks complete, verify in browser (`npm run dev`):

1. **Migration**: Go to Supabase dashboard → `soul_cards` → confirm `avatar_icon` and `avatar_url` columns.
2. **Lounge save**: Click "💾 儲存此命盤" → 2-step modal opens → Step 1 shows 36 icons → "✦" pre-selected → click another icon → click "下一步" → Step 2 shows selected icon preview → enter name → click "建立命盤 ✓" → modal closes → profile appears in dropdown with icon.
3. **Lounge dropdown**: Saved profiles show `{icon} {name}` in the dropdown.
4. **/me page**: Open `/me` → profile card header shows `avatar_icon` circle → click it → 2-step modal opens → change icon + name → confirm → circle updates immediately.
5. **Phase 2 placeholder**: In Step 1 of modal, "📷 上傳自訂圖片 · 即將推出" button is visible but disabled/unclickable.
