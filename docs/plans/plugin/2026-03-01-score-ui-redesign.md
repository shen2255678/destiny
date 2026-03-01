# Plan B: Score UI Redesign — Quadrant Visualization

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current 6 raw numbers (lust/soul/harmony + four tracks) with a visual dual-axis quadrant plot and four-track bar chart in the MVP report view, matching the product philosophy from 產品企劃書: "不要給絕對分數，給潛力區間".

**Architecture:** All changes are UI-only in `destiny-mvp`. The API response shape does not change. New inline SVG quadrant component + track bars in `ReportClient.tsx` (or the equivalent lounge/report display component).

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS v4, inline SVG (no new deps)

---

## Background

Current display (6 raw numbers):
```
VibeScore: 29 / ChemistryScore: 72 / 綜合: 54
朋友=29.6 激情=15.8 伴侶=36.4 靈魂=100.0
```

Product spec vision:
- 不要給「絕對分數」，改給「潛力區間 + 關係象限落點」
- 雙軸 (X=肉體費洛蒙, Y=靈魂共鳴) 視覺化
- 四軌道 (friend/passion/partner/soul) 能量條

---

## Data Contract (API fields used)

From `POST /api/compute-enriched` (or lounge report endpoint):
```typescript
lust: number        // X axis (0-100)
soul: number        // Y axis (0-100)
harmony: number     // blended score — shown as subtitle only
tracks: {
  friend:   number  // 0-100
  passion:  number  // 0-100
  partner:  number  // 0-100
  soul:     number  // 0-100
}
quadrant: string    // "soulmate" | "lover" | "partner" | "colleague"
primary_track: string
```

---

### Task 1: Build QuadrantPlot inline component

**Files:**
- Modify: `destiny-mvp/app/lounge/ReportClient.tsx` (or the equivalent report display file — search for where `lust_score`/`soul_score` are displayed)

**Step 1: Locate the score display section**

```bash
grep -rn "lust\|soul\|harmony\|ChemistryScore\|VibeScore" destiny-mvp/app/lounge/
```

**Step 2: Add QuadrantPlot as an inline function at the top of the file**

```tsx
/** Dual-axis quadrant plot — inline SVG, no deps */
function QuadrantPlot({ lust, soul }: { lust: number; soul: number }) {
  const W = 200, H = 200, PAD = 28;
  const inner = W - PAD * 2;

  // Map score (0-100) → SVG pixel position
  const toX = (v: number) => PAD + (v / 100) * inner;
  const toY = (v: number) => PAD + ((100 - v) / 100) * inner; // Y is inverted in SVG

  const dotX = toX(lust);
  const dotY = toY(soul);

  // Quadrant labels (center of each quadrant)
  const labels = [
    { x: PAD + inner * 0.25, y: PAD + inner * 0.25, text: "靈魂伴侶", color: "#9b59b6" },
    { x: PAD + inner * 0.75, y: PAD + inner * 0.25, text: "命定雙生", color: "#e74c3c" },
    { x: PAD + inner * 0.25, y: PAD + inner * 0.75, text: "知心好友", color: "#3498db" },
    { x: PAD + inner * 0.75, y: PAD + inner * 0.75, text: "激情愛人", color: "#e67e22" },
  ];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: 220 }}>
      {/* Background */}
      <rect x={PAD} y={PAD} width={inner} height={inner} fill="#1a0f1e" rx={4} />

      {/* Quadrant dividers */}
      <line x1={W / 2} y1={PAD} x2={W / 2} y2={W - PAD} stroke="#5c4059" strokeWidth={1} strokeDasharray="3,3" />
      <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="#5c4059" strokeWidth={1} strokeDasharray="3,3" />

      {/* Quadrant labels */}
      {labels.map((l) => (
        <text key={l.text} x={l.x} y={l.y} textAnchor="middle" dominantBaseline="middle"
          fontSize={8} fill={l.color} opacity={0.6} fontFamily="sans-serif">
          {l.text}
        </text>
      ))}

      {/* Axes */}
      <line x1={PAD} y1={W - PAD} x2={W - PAD} y2={W - PAD} stroke="#8c7089" strokeWidth={1} />
      <line x1={PAD} y1={PAD} x2={PAD} y2={W - PAD} stroke="#8c7089" strokeWidth={1} />

      {/* Axis labels */}
      <text x={W / 2} y={W - 6} textAnchor="middle" fontSize={8} fill="#8c7089" fontFamily="sans-serif">肉體費洛蒙</text>
      <text x={8} y={H / 2} textAnchor="middle" fontSize={8} fill="#8c7089" fontFamily="sans-serif"
        transform={`rotate(-90, 8, ${H / 2})`}>靈魂共鳴</text>

      {/* Dot: user pair position */}
      <circle cx={dotX} cy={dotY} r={7} fill="#c084fc" opacity={0.9} />
      <circle cx={dotX} cy={dotY} r={7} fill="none" stroke="#e9d5ff" strokeWidth={1.5} />
    </svg>
  );
}
```

**Step 3: Add TrackBars inline component**

```tsx
/** Horizontal track bars replacing raw track numbers */
function TrackBars({ tracks }: { tracks: Record<string, number> }) {
  const items = [
    { key: "friend",  label: "朋友緣",    color: "#60a5fa" },
    { key: "passion", label: "激情張力",   color: "#f87171" },
    { key: "partner", label: "正緣伴侶",   color: "#a78bfa" },
    { key: "soul",    label: "業力靈魂",   color: "#34d399" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, width: "100%" }}>
      {items.map(({ key, label, color }) => {
        const val = Math.round(tracks[key] ?? 0);
        return (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "#8c7089", width: 52, flexShrink: 0 }}>{label}</span>
            <div style={{ flex: 1, height: 6, background: "#2d1f35", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: 3,
                transition: "width 0.6s ease" }} />
            </div>
            <span style={{ fontSize: 10, color: "#c084fc", width: 24, textAlign: "right" }}>{val}</span>
          </div>
        );
      })}
    </div>
  );
}
```

**Step 4: Replace raw number display in JSX**

Find where the current score numbers are rendered (likely a grid with lust/soul/harmony labels). Replace with:

```tsx
{/* Quadrant section */}
<div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
  <QuadrantPlot lust={report.lust} soul={report.soul} />
  <div style={{ fontSize: 11, color: "#8c7089", textAlign: "center" }}>
    綜合契合指數 <span style={{ color: "#c084fc", fontWeight: 700 }}>{report.harmony}</span>
    {" · "}
    <span style={{ color: "#e9d5ff" }}>{QUADRANT_LABEL[report.quadrant] ?? report.quadrant}</span>
  </div>
</div>

{/* Track bars section */}
<TrackBars tracks={report.tracks} />
```

Where `QUADRANT_LABEL` is:
```typescript
const QUADRANT_LABEL: Record<string, string> = {
  soulmate:  "靈魂伴侶象限",
  lover:     "命定雙生象限",
  partner:   "正緣伴侶象限",
  colleague: "知心好友象限",
};
```

**Step 5: Remove old score number display**

Delete the previous `lust / soul / harmony` number grid. Keep any sections that show psychological tags or power dynamics — only the score numbers change.

**Step 6: Test in browser**

```bash
cd destiny-mvp && npm run dev
```

Navigate to the lounge/report page and verify:
- Quadrant plot renders with a purple dot positioned correctly
- Track bars animate on load
- No raw "29 / 72 / 54" numbers visible

**Step 7: Commit**

```bash
git add destiny-mvp/app/lounge/ReportClient.tsx
git commit -m "feat(ui): replace raw score numbers with quadrant plot + track bars"
```

---

### Task 2: Add quadrant label to soul_card display in /me page (optional polish)

**Files:**
- Modify: `destiny-mvp/app/me/MeClient.tsx`

If the `/me` page shows any compatibility scores for saved profiles, ensure it also uses the new quadrant label rather than raw numbers. If `/me` doesn't show scores, skip this task.

```bash
grep -n "lust\|soul\|harmony\|score" destiny-mvp/app/me/MeClient.tsx
```

If nothing found → skip. If found → apply same QUADRANT_LABEL mapping.

**Commit (if needed):**

```bash
git add destiny-mvp/app/me/MeClient.tsx
git commit -m "feat(me): show quadrant label instead of raw score numbers"
```

---

## Expected Outcome

**Before:**
```
VibeScore: 29 / ChemistryScore: 72 / 綜合: 54
朋友=29.6 激情=15.8 伴侶=36.4 靈魂=100.0
```

**After:**
- SVG quadrant plot with the couple's dot in the relevant quadrant
- Label below: "綜合契合指數 54 · 靈魂伴侶象限"
- Four horizontal track bars with smooth fill animation
- No raw decimal numbers except the single harmony score subtitle
