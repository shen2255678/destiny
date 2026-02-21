# Phase H: ZiWei DouShu (紫微斗數) Synastry Engine

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wrap the existing JS 紫微斗數 engine as a headless Node.js microservice (port 8002), add Python synastry scoring logic, and integrate ZWDS scores into `compute_match_v2()` as a Tier 1 VIP bonus layer.

**Architecture:** New `ziwei-service/` Node.js Express app wraps the ZWDS JS engine headlessly via Node.js `vm` module (no DOM needed). Python `astro-service/zwds_synastry.py` calls the Node service via HTTP and returns `partner_score`, `soul_score`, and `rpv_modifier`. `matching.py` applies these as additive bonuses only when both users are Tier 1.

**Tech Stack:** Node.js 18+ (Express, no-framework), Python 3.9 (requests, FastAPI), Jest (JS tests), pytest (Python tests). Existing `ZiWeiDouShu/js/` source files are copied into `ziwei-service/vendor/` — no modification to originals.

---

## Background: How the ZWDS Engine Works

The JS source in `ZiWeiDouShu/js/` has three layers:
- `lunar.js` — solar→lunar calendar conversion; `Lunar(0, y, m, d)` sets global `lunar` object
- `ziweistar.js` — all lookup tables (`Star_S04`, `Star_A14`, `FiveEleTable`, etc.) + palace/star name constants
- `ziweicore.js` — `ziwei.computeZiWei(y, m, d, h_branch, gender)` → returns `Place12` (12-palace array)
- `ziweiui.js` — DOM rendering; the only call we need to mock is `ziweiUI.clearPalce()` in `setZiwei()`

`Place12[i]` structure:
```javascript
{
  MangA: "甲\n子",                  // heavenly stem + earthly branch for this position
  MangB: "【命宮】",                // palace label (命宮/夫妻宮/福德宮/…)
  MangC: "【身】",                  // body palace marker (or "")
  StarA: ["紫微化祿", "天機"],      // main stars (14-star system, with 化 suffix when applicable)
  StarB: ["擎羊"],                  // 6 inauspicious stars
  StarC: ["天馬"],                  // other stars
  Star6: ["文昌", "祿存"]           // 6 auspicious stars
}
```

**Synastry logic (飛星四化):**

`Star_S04[transform_idx][y1Pos]` → star name for each of A's 4 transformations, where:
- `y1Pos` = A's year heavenly stem index (甲=0, 乙=1, … 癸=9)
- Row 0 = 化祿 star, Row 1 = 化權 star, Row 2 = 化科 star, Row 3 = 化忌 star

Then search B's `Place12` to find which palace contains that star. Key palaces:
- 命宮 (Life Palace) = `Place12[lPos].MangB`
- 夫妻宮 (Spouse Palace) = Palace index 10 → position `(lPos+10)%12`
- 福德宮 (Spirit Palace) = Palace index 2 → position `(lPos+2)%12`

**Hour-to-branch conversion** (needed to call `computeZiWei`):
```
子時 23:00-00:59, 丑時 01:00-02:59, 寅時 03:00-04:59, 卯時 05:00-06:59,
辰時 07:00-08:59, 巳時 09:00-10:59, 午時 11:00-12:59, 未時 13:00-14:59,
申時 15:00-16:59, 酉時 17:00-18:59, 戌時 19:00-20:59, 亥時 21:00-22:59
```

---

## Task 1: ziwei-service scaffold

**Files:**
- Create: `ziwei-service/package.json`
- Create: `ziwei-service/server.js`
- Create: `ziwei-service/lib/engine.js`
- Create: `ziwei-service/vendor/` (copies of original JS files)

**Step 1: Write failing test for `/health` endpoint**

Create `ziwei-service/test/server.test.js`:
```javascript
const request = require('supertest');
const app = require('../server');

test('GET /health returns ok', async () => {
  const res = await request(app).get('/health');
  expect(res.status).toBe(200);
  expect(res.body).toEqual({ status: 'ok', service: 'ziwei-service' });
});
```

**Step 2: Run test to verify it fails**

Run: `cd ziwei-service && npm test -- --testPathPattern=server.test.js`
Expected: FAIL with "Cannot find module '../server'"

**Step 3: Create package.json**

Create `ziwei-service/package.json`:
```json
{
  "name": "ziwei-service",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "supertest": "^6.3.0"
  }
}
```

**Step 4: Create server.js (health only)**

Create `ziwei-service/server.js`:
```javascript
const express = require('express');
const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'ziwei-service' });
});

if (require.main === module) {
  const PORT = process.env.PORT || 8002;
  app.listen(PORT, () => console.log(`ziwei-service running on port ${PORT}`));
}

module.exports = app;
```

**Step 5: Install dependencies and run test**

Run: `cd ziwei-service && npm install && npm test -- --testPathPattern=server.test.js`
Expected: PASS

**Step 6: Copy vendor files**

Run: `cp ZiWeiDouShu/js/lunar.js ziwei-service/vendor/lunar.js`
Run: `cp ZiWeiDouShu/js/ziweistar.js ziwei-service/vendor/ziweistar.js`
Run: `cp ZiWeiDouShu/js/ziweicore.js ziwei-service/vendor/ziweicore.js`

(Do NOT copy ziweiui.js — we mock it)

**Step 7: Commit**

```bash
git add ziwei-service/
git commit -m "feat: scaffold ziwei-service with health endpoint"
```

---

## Task 2: Headless ZWDS engine wrapper

**Files:**
- Create: `ziwei-service/lib/engine.js`
- Create: `ziwei-service/test/engine.test.js`

**Step 1: Write failing tests for engine**

Create `ziwei-service/test/engine.test.js`:
```javascript
const { computeZiWei, getHourBranch } = require('../lib/engine');

describe('getHourBranch', () => {
  test('23:00 → 子', () => expect(getHourBranch('23:00')).toBe('子'));
  test('01:30 → 丑', () => expect(getHourBranch('01:30')).toBe('丑'));
  test('11:00 → 午', () => expect(getHourBranch('11:00')).toBe('午'));
  test('00:30 → 子', () => expect(getHourBranch('00:30')).toBe('子'));
});

describe('computeZiWei', () => {
  test('returns Place12 array of 12 palaces', () => {
    const chart = computeZiWei(1990, 6, 15, '午', 'M');
    expect(Array.isArray(chart)).toBe(true);
    expect(chart.length).toBe(12);
  });

  test('each palace has MangB (palace label)', () => {
    const chart = computeZiWei(1990, 6, 15, '午', 'M');
    const palaceNames = chart.map(p => p.MangB);
    expect(palaceNames).toContain('【命宮】');
    expect(palaceNames).toContain('【夫妻宮】');
    expect(palaceNames).toContain('【福德宮】');
  });

  test('each palace has StarA array', () => {
    const chart = computeZiWei(1990, 6, 15, '午', 'M');
    chart.forEach(p => {
      expect(Array.isArray(p.StarA)).toBe(true);
    });
  });

  test('chart contains at least one main star across all palaces', () => {
    const chart = computeZiWei(1990, 6, 15, '午', 'M');
    const allStars = chart.flatMap(p => p.StarA);
    expect(allStars.length).toBeGreaterThan(0);
    // Should contain 紫微 somewhere
    expect(allStars.some(s => s.includes('紫微'))).toBe(true);
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd ziwei-service && npm test -- --testPathPattern=engine.test.js`
Expected: FAIL with "Cannot find module '../lib/engine'"

**Step 3: Create engine.js**

Create `ziwei-service/lib/engine.js`:
```javascript
const vm = require('vm');
const fs = require('fs');
const path = require('path');

// Build headless execution context: mock DOM-dependent ziweiUI
const context = {
  ziweiUI: { clearPalce: () => {} },
  console,
};
vm.createContext(context);

// Load vendor files in order (lunar → star tables → core engine)
const vendorDir = path.join(__dirname, '..', 'vendor');
for (const file of ['lunar.js', 'ziweistar.js', 'ziweicore.js']) {
  const code = fs.readFileSync(path.join(vendorDir, file), 'utf8');
  vm.runInContext(code, context);
}

// EarthlyBranches order: 子丑寅卯辰巳午未申酉戌亥
const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];

/**
 * Convert a time string "HH:MM" to the corresponding EarthlyBranch (時辰).
 * 子時 covers 23:00-00:59, then pairs of 2 hours each.
 */
function getHourBranch(timeStr) {
  const [h] = timeStr.split(':').map(Number);
  // 子時: 23 or 0; others: ((h+1)/2)%12
  const idx = h === 23 ? 0 : Math.floor((h + 1) / 2) % 12;
  return BRANCHES[idx];
}

/**
 * Compute the 12-palace ZWDS chart.
 * @param {number} year  - Solar year (e.g. 1990)
 * @param {number} month - Solar month (1-12)
 * @param {number} day   - Solar day (1-31)
 * @param {string} hourBranch - EarthlyBranch for birth hour (e.g. '午')
 * @param {string} gender - 'M' or 'F'
 * @returns {Array} Place12 — array of 12 palace objects
 */
function computeZiWei(year, month, day, hourBranch, gender) {
  return context.ziwei.computeZiWei(year, month, day, hourBranch, gender);
}

module.exports = { computeZiWei, getHourBranch };
```

**Step 4: Run tests**

Run: `cd ziwei-service && npm test -- --testPathPattern=engine.test.js`
Expected: PASS (4 + 4 = 8 tests)

**Step 5: Commit**

```bash
git add ziwei-service/lib/engine.js ziwei-service/test/engine.test.js
git commit -m "feat: headless ZWDS engine wrapper (vm context, no DOM)"
```

---

## Task 3: Flying star synastry logic

**Files:**
- Create: `ziwei-service/lib/synastry.js`
- Create: `ziwei-service/test/synastry.test.js`

**Background — what to compute:**

Given two ZWDS charts (Place12 arrays), the synastry engine:
1. Finds A's 4 transformation stars (化祿/化權/化科/化忌) from `Star_S04` table
2. Locates each star in B's chart → which palace does it land in?
3. Key impacts:
   - A's 化祿 hits B's 命宮 or 夫妻宮 → A naturally nurtures B (partner track boost)
   - A's 化忌 hits B's 命宮 or 夫妻宮 → karmic debt/obsession (soul track boost, 業力)
   - A's 化權 hits B's 命宮 → A naturally dominates B (RPV modifier: A frame +15, B frame -15)
4. Mutual 化祿 = peak partner score; mutual 化忌 = peak soul score (rare fated pair)
5. Spouse palace cross-match: A's 夫妻宮 stars ∩ B's 命宮 stars → "ideal type hit"

**Step 1: Write failing tests**

Create `ziwei-service/test/synastry.test.js`:
```javascript
const { computeZiWei } = require('../lib/engine');
const {
  extractSynastrySummary,
  computeZwdsSynastry,
  getPalaceStars,
  findStarPalace,
} = require('../lib/synastry');

// Fixed test charts
const chartA = computeZiWei(1990, 6, 15, '午', 'M'); // 庚午 year
const chartB = computeZiWei(1993, 3, 8, '卯', 'F');  // 癸卯 year

describe('getPalaceStars', () => {
  test('returns stars for named palace', () => {
    const stars = getPalaceStars(chartA, '命宮');
    expect(Array.isArray(stars)).toBe(true);
  });

  test('returns empty array for non-existent palace name', () => {
    const stars = getPalaceStars(chartA, '不存在');
    expect(stars).toEqual([]);
  });
});

describe('findStarPalace', () => {
  test('returns palace label when star found', () => {
    const allStars = chartA.flatMap(p => p.StarA);
    if (allStars.length > 0) {
      // Get base name (strip 化X suffix)
      const baseName = allStars[0].replace(/化[祿權科忌]$/, '');
      const result = findStarPalace(chartA, baseName);
      expect(result).toMatch(/【.+宮】|【身】/);
    }
  });

  test('returns null when star not found in chart', () => {
    expect(findStarPalace(chartA, '不存在星')).toBeNull();
  });
});

describe('extractSynastrySummary', () => {
  test('returns four_transforms object', () => {
    const summary = extractSynastrySummary(chartA, 1990);
    expect(summary).toHaveProperty('four_transforms');
    expect(summary.four_transforms).toHaveProperty('hua_lu');
    expect(summary.four_transforms).toHaveProperty('hua_quan');
    expect(summary.four_transforms).toHaveProperty('hua_ke');
    expect(summary.four_transforms).toHaveProperty('hua_ji');
  });

  test('four_transforms star names are non-empty strings', () => {
    const summary = extractSynastrySummary(chartA, 1990);
    expect(typeof summary.four_transforms.hua_lu).toBe('string');
    expect(summary.four_transforms.hua_lu.length).toBeGreaterThan(0);
  });
});

describe('computeZwdsSynastry', () => {
  test('returns partner_score, soul_score, rpv_modifier, details', () => {
    const result = computeZwdsSynastry(chartA, 1990, chartB, 1993);
    expect(result).toHaveProperty('partner_score');
    expect(result).toHaveProperty('soul_score');
    expect(result).toHaveProperty('rpv_modifier');
    expect(result).toHaveProperty('details');
  });

  test('partner_score is between 0 and 1', () => {
    const result = computeZwdsSynastry(chartA, 1990, chartB, 1993);
    expect(result.partner_score).toBeGreaterThanOrEqual(0);
    expect(result.partner_score).toBeLessThanOrEqual(1);
  });

  test('soul_score is between 0 and 1', () => {
    const result = computeZwdsSynastry(chartA, 1990, chartB, 1993);
    expect(result.soul_score).toBeGreaterThanOrEqual(0);
    expect(result.soul_score).toBeLessThanOrEqual(1);
  });

  test('rpv_modifier is -30, -15, 0, +15, or +30', () => {
    const result = computeZwdsSynastry(chartA, 1990, chartB, 1993);
    expect([-30, -15, 0, 15, 30]).toContain(result.rpv_modifier);
  });

  test('details contains directional flags', () => {
    const result = computeZwdsSynastry(chartA, 1990, chartB, 1993);
    expect(result.details).toHaveProperty('hua_lu_a_to_b');
    expect(result.details).toHaveProperty('hua_lu_b_to_a');
    expect(result.details).toHaveProperty('hua_ji_a_to_b');
    expect(result.details).toHaveProperty('hua_ji_b_to_a');
    expect(result.details).toHaveProperty('hua_quan_a_to_b');
    expect(result.details).toHaveProperty('hua_quan_b_to_a');
    expect(result.details).toHaveProperty('spouse_match_a_sees_b');
    expect(result.details).toHaveProperty('spouse_match_b_sees_a');
  });
});
```

**Step 2: Run to verify they fail**

Run: `cd ziwei-service && npm test -- --testPathPattern=synastry.test.js`
Expected: FAIL with "Cannot find module '../lib/synastry'"

**Step 3: Create synastry.js**

Create `ziwei-service/lib/synastry.js`:
```javascript
// Star_S04 rows: [化祿, 化權, 化科, 化忌] × 10 heavenly stems (甲乙丙丁戊己庚辛壬癸)
// Matches ziweistar.js Star_S04 table values (star names for each transformation)
const HEAVENLY_STEMS = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
const FOUR_TRANSFORMS = ['hua_lu','hua_quan','hua_ke','hua_ji'];
// Star_S04 from ziweistar.js (hardcoded here to avoid vm context dependency)
// StarM_A14 = ['紫微','天機','太陽','武曲','天同','廉貞','天府','太陰','貪狼','巨門','天相','天梁','七殺','破軍']
// StarM_A07 = ['文昌','文曲','左輔','右弼','天魁','天鉞','祿存']
const STAR_S04_TABLE = [
  // 化祿: 甲廉貞 乙天機 丙天同 丁太陰 戊貪狼 己武曲 庚太陽 辛巨門 壬天梁 癸破軍
  ['廉貞','天機','天同','太陰','貪狼','武曲','太陽','巨門','天梁','破軍'],
  // 化權: 甲破軍 乙天梁 丙天機 丁天同 戊太陰 己貪狼 庚武曲 辛太陽 壬紫微 癸巨門
  ['破軍','天梁','天機','天同','太陰','貪狼','武曲','太陽','紫微','巨門'],
  // 化科: 甲武曲 乙紫微 丙文昌 丁天機 戊右弼 己天梁 庚天府 辛文曲 壬左輔 癸太陰
  ['武曲','紫微','文昌','天機','右弼','天梁','天府','文曲','左輔','太陰'],
  // 化忌: 甲太陽 乙太陰 丙廉貞 丁巨門 戊天機 己文曲 庚天同 辛文昌 壬武曲 癸貪狼
  ['太陽','太陰','廉貞','巨門','天機','文曲','天同','文昌','武曲','貪狼'],
];

// Key palace labels for synastry analysis
const KEY_PALACES_PARTNER = ['【命宮】', '【夫妻宮】'];
const KEY_PALACES_DOM = ['【命宮】'];

/**
 * Get all main stars (StarA) in a named palace (e.g. '命宮').
 * Returns array of star name strings (may include 化X suffix).
 */
function getPalaceStars(chart, palaceName) {
  const label = `【${palaceName}】`;
  const palace = chart.find(p => p.MangB === label);
  return palace ? [...palace.StarA] : [];
}

/**
 * Find which palace label contains a given base star name.
 * Strips 化X suffix before comparing (e.g. '紫微化祿' matches '紫微').
 * Returns palace label string or null if not found.
 */
function findStarPalace(chart, baseStarName) {
  for (const palace of chart) {
    const found = palace.StarA.some(s => {
      const base = s.replace(/化[祿權科忌]$/, '');
      return base === baseStarName;
    });
    if (found) return palace.MangB;
  }
  return null;
}

/**
 * Extract synastry summary from a computed chart.
 * @param {Array} chart - Place12 from computeZiWei
 * @param {number} birthYear - Solar birth year (to compute year stem index)
 */
function extractSynastrySummary(chart, birthYear) {
  const y1Pos = ((birthYear - 4) % 10 + 10) % 10;  // 0=甲…9=癸
  return {
    four_transforms: {
      hua_lu:   STAR_S04_TABLE[0][y1Pos],
      hua_quan: STAR_S04_TABLE[1][y1Pos],
      hua_ke:   STAR_S04_TABLE[2][y1Pos],
      hua_ji:   STAR_S04_TABLE[3][y1Pos],
    },
  };
}

/**
 * Check if a transformation star hits one of the key palaces in the target chart.
 * @param {string} starName - base star name (no 化X suffix)
 * @param {Array} targetChart - opponent's Place12
 * @param {string[]} keyPalaces - palace labels to check (e.g. ['【命宮】','【夫妻宮】'])
 * @returns {boolean}
 */
function starHitsKeyPalace(starName, targetChart, keyPalaces) {
  const palace = findStarPalace(targetChart, starName);
  return palace !== null && keyPalaces.includes(palace);
}

/**
 * Check overlap between spouse palace stars of A and life palace stars of B.
 * Returns true if any star name (base) in A's spouse palace appears in B's life palace.
 */
function spousePalaceMatch(chartA, chartB) {
  const aSpouseStars = getPalaceStars(chartA, '夫妻宮').map(s => s.replace(/化[祿權科忌]$/, ''));
  const bLifeStars = getPalaceStars(chartB, '命宮').map(s => s.replace(/化[祿權科忌]$/, ''));
  return aSpouseStars.some(s => bLifeStars.includes(s));
}

/**
 * Compute ZWDS synastry scores between two users.
 * @param {Array} chartA   - User A's Place12
 * @param {number} yearA   - User A's solar birth year
 * @param {Array} chartB   - User B's Place12
 * @param {number} yearB   - User B's solar birth year
 * @returns {{ partner_score: number, soul_score: number, rpv_modifier: number, details: object }}
 */
function computeZwdsSynastry(chartA, yearA, chartB, yearB) {
  const summaryA = extractSynastrySummary(chartA, yearA);
  const summaryB = extractSynastrySummary(chartB, yearB);

  // Flying star hits
  const hua_lu_a_to_b   = starHitsKeyPalace(summaryA.four_transforms.hua_lu,   chartB, KEY_PALACES_PARTNER);
  const hua_lu_b_to_a   = starHitsKeyPalace(summaryB.four_transforms.hua_lu,   chartA, KEY_PALACES_PARTNER);
  const hua_ji_a_to_b   = starHitsKeyPalace(summaryA.four_transforms.hua_ji,   chartB, KEY_PALACES_PARTNER);
  const hua_ji_b_to_a   = starHitsKeyPalace(summaryB.four_transforms.hua_ji,   chartA, KEY_PALACES_PARTNER);
  const hua_quan_a_to_b = starHitsKeyPalace(summaryA.four_transforms.hua_quan, chartB, KEY_PALACES_DOM);
  const hua_quan_b_to_a = starHitsKeyPalace(summaryB.four_transforms.hua_quan, chartA, KEY_PALACES_DOM);

  // Spouse palace ideal-type matching
  const spouse_match_a_sees_b = spousePalaceMatch(chartA, chartB);
  const spouse_match_b_sees_a = spousePalaceMatch(chartB, chartA);

  // Partner score: 化祿 + spouse palace match
  // Mutual 化祿 = 0.8 base; one-way = 0.4; spouse match adds 0.1 each way; cap at 1.0
  let partner_score = 0;
  if (hua_lu_a_to_b && hua_lu_b_to_a) partner_score += 0.8;
  else if (hua_lu_a_to_b || hua_lu_b_to_a) partner_score += 0.4;
  if (spouse_match_a_sees_b) partner_score += 0.1;
  if (spouse_match_b_sees_a) partner_score += 0.1;
  partner_score = Math.min(1.0, partner_score);

  // Soul score: 化忌 = 業力債 (fated/karmic attraction — soul track)
  // Mutual 化忌 = 1.0 (最強業力); one-way = 0.6
  let soul_score = 0;
  if (hua_ji_a_to_b && hua_ji_b_to_a) soul_score = 1.0;
  else if (hua_ji_a_to_b || hua_ji_b_to_a) soul_score = 0.6;

  // RPV modifier: 化權 hitting opponent's 命宮 → natural dominance
  // A 化權 → B 命宮: A Dom +15, B -15 (net +30 from A's perspective)
  // B 化權 → A 命宮: A Dom -15, B +15 (net -30 from A's perspective)
  // Both: cancel out (0)
  let rpv_modifier = 0;
  if (hua_quan_a_to_b && !hua_quan_b_to_a) rpv_modifier = 30;
  else if (hua_quan_b_to_a && !hua_quan_a_to_b) rpv_modifier = -30;
  else if (hua_quan_a_to_b && hua_quan_b_to_a) rpv_modifier = 0;

  return {
    partner_score: Math.round(partner_score * 100) / 100,
    soul_score: Math.round(soul_score * 100) / 100,
    rpv_modifier,
    details: {
      hua_lu_a_to_b, hua_lu_b_to_a,
      hua_ji_a_to_b, hua_ji_b_to_a,
      hua_quan_a_to_b, hua_quan_b_to_a,
      spouse_match_a_sees_b, spouse_match_b_sees_a,
    },
  };
}

module.exports = {
  computeZwdsSynastry,
  extractSynastrySummary,
  getPalaceStars,
  findStarPalace,
  spousePalaceMatch,
};
```

**Step 4: Run tests**

Run: `cd ziwei-service && npm test -- --testPathPattern=synastry.test.js`
Expected: PASS (all 12 tests)

**Step 5: Commit**

```bash
git add ziwei-service/lib/synastry.js ziwei-service/test/synastry.test.js
git commit -m "feat: ZWDS flying star synastry logic (化祿/化忌/化權 + spouse palace)"
```

---

## Task 4: ziwei-service HTTP endpoints

**Files:**
- Modify: `ziwei-service/server.js`
- Modify: `ziwei-service/test/server.test.js`

**Step 1: Write failing tests for new endpoints**

Add to `ziwei-service/test/server.test.js`:
```javascript
const { computeZiWei } = require('../lib/engine');

describe('POST /calculate-zwds', () => {
  test('returns Place12 for valid input', async () => {
    const res = await request(app).post('/calculate-zwds').send({
      year: 1990, month: 6, day: 15, birth_time: '11:30', gender: 'M',
    });
    expect(res.status).toBe(200);
    expect(res.body.chart).toHaveLength(12);
    expect(res.body.chart[0]).toHaveProperty('MangB');
  });

  test('returns 400 for missing fields', async () => {
    const res = await request(app).post('/calculate-zwds').send({ year: 1990 });
    expect(res.status).toBe(400);
  });
});

describe('POST /zwds-synastry', () => {
  test('returns synastry scores', async () => {
    const res = await request(app).post('/zwds-synastry').send({
      user_a: { year: 1990, month: 6, day: 15, birth_time: '11:30', gender: 'M' },
      user_b: { year: 1993, month: 3, day: 8,  birth_time: '05:00', gender: 'F' },
    });
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('partner_score');
    expect(res.body).toHaveProperty('soul_score');
    expect(res.body).toHaveProperty('rpv_modifier');
    expect(res.body).toHaveProperty('details');
  });

  test('returns 400 for missing user_a', async () => {
    const res = await request(app).post('/zwds-synastry').send({
      user_b: { year: 1993, month: 3, day: 8, birth_time: '05:00', gender: 'F' },
    });
    expect(res.status).toBe(400);
  });
});
```

**Step 2: Run to verify they fail**

Run: `cd ziwei-service && npm test -- --testPathPattern=server.test.js`
Expected: FAIL on the new tests (404 for missing routes)

**Step 3: Add routes to server.js**

Edit `ziwei-service/server.js` — add after the health route:
```javascript
const { computeZiWei, getHourBranch } = require('./lib/engine');
const { computeZwdsSynastry } = require('./lib/synastry');

app.post('/calculate-zwds', (req, res) => {
  const { year, month, day, birth_time, gender } = req.body;
  if (!year || !month || !day || !birth_time || !gender) {
    return res.status(400).json({ error: 'Missing required fields: year, month, day, birth_time, gender' });
  }
  try {
    const hourBranch = getHourBranch(birth_time);
    const chart = computeZiWei(Number(year), Number(month), Number(day), hourBranch, gender);
    res.json({ chart, hour_branch: hourBranch });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/zwds-synastry', (req, res) => {
  const { user_a, user_b } = req.body;
  if (!user_a || !user_b) {
    return res.status(400).json({ error: 'Missing user_a or user_b' });
  }
  try {
    const hourA = getHourBranch(user_a.birth_time);
    const hourB = getHourBranch(user_b.birth_time);
    const chartA = computeZiWei(Number(user_a.year), Number(user_a.month), Number(user_a.day), hourA, user_a.gender || 'M');
    const chartB = computeZiWei(Number(user_b.year), Number(user_b.month), Number(user_b.day), hourB, user_b.gender || 'F');
    const result = computeZwdsSynastry(chartA, user_a.year, chartB, user_b.year);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

**Step 4: Run all tests**

Run: `cd ziwei-service && npm test`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add ziwei-service/server.js ziwei-service/test/server.test.js
git commit -m "feat: ziwei-service HTTP endpoints (calculate-zwds + zwds-synastry)"
```

---

## Task 5: Python ZWDS synastry bridge

**Files:**
- Create: `astro-service/zwds_synastry.py`
- Create: `astro-service/test_zwds.py`

**Step 1: Write failing tests**

Create `astro-service/test_zwds.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from zwds_synastry import compute_zwds_synastry, is_tier1_user

# Sample Tier 1 user profile
TIER1_USER_A = {
    "birth_year": 1990, "birth_month": 6, "birth_day": 15,
    "birth_time": "11:30", "gender": "M", "data_tier": 1,
}
TIER1_USER_B = {
    "birth_year": 1993, "birth_month": 3, "birth_day": 8,
    "birth_time": "05:00", "gender": "F", "data_tier": 1,
}
TIER3_USER = {
    "birth_year": 1990, "birth_month": 6, "birth_day": 15,
    "birth_time": None, "gender": "M", "data_tier": 3,
}

class TestIsTier1User:
    def test_tier1_with_birth_time_returns_true(self):
        assert is_tier1_user(TIER1_USER_A) is True

    def test_tier3_returns_false(self):
        assert is_tier1_user(TIER3_USER) is False

    def test_tier1_without_birth_time_returns_false(self):
        user = {**TIER1_USER_A, "birth_time": None}
        assert is_tier1_user(user) is False

class TestComputeZwdsSynastry:
    def test_returns_none_if_not_both_tier1(self):
        result = compute_zwds_synastry(TIER1_USER_A, TIER3_USER)
        assert result is None

    def test_returns_none_if_service_unavailable(self):
        with patch('zwds_synastry.requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            result = compute_zwds_synastry(TIER1_USER_A, TIER1_USER_B)
        assert result is None

    def test_returns_scores_dict_on_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "partner_score": 0.8,
            "soul_score": 0.6,
            "rpv_modifier": 0,
            "details": {
                "hua_lu_a_to_b": True, "hua_lu_b_to_a": True,
                "hua_ji_a_to_b": False, "hua_ji_b_to_a": False,
                "hua_quan_a_to_b": False, "hua_quan_b_to_a": False,
                "spouse_match_a_sees_b": False, "spouse_match_b_sees_a": False,
            }
        }
        with patch('zwds_synastry.requests.post', return_value=mock_response):
            result = compute_zwds_synastry(TIER1_USER_A, TIER1_USER_B)
        assert result is not None
        assert "partner_score" in result
        assert "soul_score" in result
        assert "rpv_modifier" in result
        assert result["partner_score"] == 0.8

    def test_returns_none_on_non_200_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        with patch('zwds_synastry.requests.post', return_value=mock_response):
            result = compute_zwds_synastry(TIER1_USER_A, TIER1_USER_B)
        assert result is None
```

**Step 2: Run tests to verify they fail**

Run: `cd astro-service && pytest test_zwds.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'zwds_synastry'"

**Step 3: Create zwds_synastry.py**

Create `astro-service/zwds_synastry.py`:
```python
"""
ZWDS (紫微斗數) Synastry Bridge
Calls ziwei-service (Node.js, port 8002) to compute 飛星四化 synastry scores.
Only activated for Tier 1 users (precise birth time required).
Non-blocking: returns None if ziwei-service is unavailable.
"""
import os
import requests
from typing import Optional

ZIWEI_SERVICE_URL = os.environ.get("ZIWEI_SERVICE_URL", "http://localhost:8002")
TIMEOUT_SECONDS = 5


def is_tier1_user(user: dict) -> bool:
    """Return True only if the user has Tier 1 data and a known birth time."""
    return (
        user.get("data_tier") == 1
        and user.get("birth_time") is not None
    )


def compute_zwds_synastry(user_a: dict, user_b: dict) -> Optional[dict]:
    """
    Compute ZWDS synastry scores for two users.
    Returns None if:
    - Either user is not Tier 1
    - ziwei-service is unavailable
    - Any error occurs

    Returns dict with:
        partner_score: float (0.0–1.0) — 化祿 mutual nurturing
        soul_score: float (0.0–1.0) — 化忌 karmic bond
        rpv_modifier: int (-30/0/+30) — 化權 dominance shift
        details: dict — directional flags for each transformation
    """
    if not (is_tier1_user(user_a) and is_tier1_user(user_b)):
        return None

    payload = {
        "user_a": {
            "year": user_a["birth_year"],
            "month": user_a["birth_month"],
            "day": user_a["birth_day"],
            "birth_time": user_a["birth_time"],
            "gender": user_a.get("gender", "M"),
        },
        "user_b": {
            "year": user_b["birth_year"],
            "month": user_b["birth_month"],
            "day": user_b["birth_day"],
            "birth_time": user_b["birth_time"],
            "gender": user_b.get("gender", "F"),
        },
    }

    try:
        response = requests.post(
            f"{ZIWEI_SERVICE_URL}/zwds-synastry",
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None
```

**Step 4: Run tests**

Run: `cd astro-service && pytest test_zwds.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add astro-service/zwds_synastry.py astro-service/test_zwds.py
git commit -m "feat: Python ZWDS synastry bridge (non-blocking, Tier 1 only)"
```

---

## Task 6: Integrate ZWDS into matching.py

**Files:**
- Modify: `astro-service/matching.py`
- Modify: `astro-service/test_matching.py`

**Background:** ZWDS scores are additive bonuses applied to the existing `compute_match_v2()` output. They do NOT replace existing scores — they shift partner/soul tracks by up to ±0.20.

**Score application formula:**
```python
# If zwds result is available:
partner_track += zwds["partner_score"] * 0.20  # cap at 1.0
soul_track    += zwds["soul_score"]    * 0.20  # cap at 1.0
rpv_frame_a  += zwds["rpv_modifier"]          # carry into power frame
```

**Step 1: Write failing tests**

Add to `astro-service/test_matching.py`:
```python
from unittest.mock import patch

class TestZwdsIntegration:
    USER_TIER1 = {
        "birth_year": 1990, "birth_month": 6, "birth_day": 15,
        "birth_time": "11:30", "gender": "M", "data_tier": 1,
        "sun_sign": "Gemini", "moon_sign": "Aries", "venus_sign": "Taurus",
        "ascendant_sign": "Scorpio", "mars_sign": "Leo", "saturn_sign": "Capricorn",
        "mercury_sign": "Gemini", "jupiter_sign": "Cancer", "pluto_sign": "Scorpio",
        "chiron_sign": "Cancer", "juno_sign": "Sagittarius",
        "house4_sign": "Pisces", "house8_sign": "Cancer",
        "rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "home",
        "attachment_style": "secure", "attachment_role": "dom_secure",
    }
    USER_TIER1_B = {**USER_TIER1, "birth_year": 1993, "birth_month": 3, "birth_day": 8,
                   "birth_time": "05:00", "gender": "F",
                   "rpv_power": "follow", "attachment_role": "sub_secure"}

    def test_zwds_not_called_for_tier3_users(self):
        user_t3 = {**self.USER_TIER1, "data_tier": 3, "birth_time": None}
        with patch('matching.compute_zwds_synastry') as mock_zwds:
            compute_match_v2(user_t3, self.USER_TIER1_B)
        mock_zwds.assert_not_called()

    def test_zwds_bonus_adds_to_partner_track(self):
        mock_zwds_result = {
            "partner_score": 1.0, "soul_score": 0.0, "rpv_modifier": 0,
            "details": {
                "hua_lu_a_to_b": True, "hua_lu_b_to_a": True,
                "hua_ji_a_to_b": False, "hua_ji_b_to_a": False,
                "hua_quan_a_to_b": False, "hua_quan_b_to_a": False,
                "spouse_match_a_sees_b": False, "spouse_match_b_sees_a": False,
            }
        }
        with patch('matching.compute_zwds_synastry', return_value=mock_zwds_result):
            result_with = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        with patch('matching.compute_zwds_synastry', return_value=None):
            result_without = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        # Partner track should be higher with ZWDS bonus
        assert result_with["tracks"]["partner"] >= result_without["tracks"]["partner"]

    def test_zwds_bonus_adds_to_soul_track(self):
        mock_zwds_result = {
            "partner_score": 0.0, "soul_score": 1.0, "rpv_modifier": 0,
            "details": {
                "hua_lu_a_to_b": False, "hua_lu_b_to_a": False,
                "hua_ji_a_to_b": True, "hua_ji_b_to_a": True,
                "hua_quan_a_to_b": False, "hua_quan_b_to_a": False,
                "spouse_match_a_sees_b": False, "spouse_match_b_sees_a": False,
            }
        }
        with patch('matching.compute_zwds_synastry', return_value=mock_zwds_result) as m:
            result_with = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        with patch('matching.compute_zwds_synastry', return_value=None):
            result_without = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        assert result_with["tracks"]["soul"] >= result_without["tracks"]["soul"]

    def test_zwds_result_included_in_output(self):
        mock_zwds_result = {
            "partner_score": 0.5, "soul_score": 0.3, "rpv_modifier": 15,
            "details": {}
        }
        with patch('matching.compute_zwds_synastry', return_value=mock_zwds_result):
            result = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        assert "zwds" in result
        assert result["zwds"]["partner_score"] == 0.5

    def test_zwds_none_when_service_unavailable(self):
        with patch('matching.compute_zwds_synastry', return_value=None):
            result = compute_match_v2(self.USER_TIER1, self.USER_TIER1_B)
        assert result["zwds"] is None
```

**Step 2: Run to verify they fail**

Run: `cd astro-service && pytest test_matching.py::TestZwdsIntegration -v`
Expected: FAIL (import error or assertion error)

**Step 3: Update matching.py**

Add at top of `astro-service/matching.py`:
```python
from zwds_synastry import compute_zwds_synastry
```

In `compute_match_v2()`, after computing `useful_god_complement` and before building the return dict:
```python
# ZWDS bonus (Tier 1 VIP only — non-blocking)
zwds_result = compute_zwds_synastry(user_a, user_b)
```

In `compute_tracks()` call, pass the zwds bonus:
```python
# Modify compute_tracks call signature to accept zwds_partner and zwds_soul
tracks = compute_tracks(user_a, user_b, power,
                        useful_god_complement=useful_god_complement,
                        zwds_partner=zwds_result["partner_score"] if zwds_result else 0.0,
                        zwds_soul=zwds_result["soul_score"] if zwds_result else 0.0)
```

Update `compute_tracks()` signature and body:
```python
def compute_tracks(user_a, user_b, power, useful_god_complement=0.0,
                   zwds_partner=0.0, zwds_soul=0.0) -> dict:
    ...
    # In partner track:
    partner = ... (existing calculation) ... + 0.20 * zwds_partner
    # In soul track:
    soul = ... (existing calculation) ... + 0.20 * zwds_soul
    # Cap at 1.0
    partner = min(1.0, partner)
    soul = min(1.0, soul)
```

In `compute_power_v2()` call: if `zwds_result` has `rpv_modifier`, add it to the frame calculation (pass as `zwds_rpv_modifier` parameter — default 0).

Add `zwds` to the return dict of `compute_match_v2()`:
```python
return {
    ...,
    "bazi_relation": bazi_relation,
    "useful_god_complement": round(useful_god_complement, 2),
    "zwds": zwds_result,  # None if not Tier 1 or service unavailable
}
```

**Step 4: Run all matching tests**

Run: `cd astro-service && pytest test_matching.py -v`
Expected: PASS (all existing tests + 5 new ZWDS tests)

**Step 5: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "feat: integrate ZWDS synastry scores into compute_match_v2 (Tier 1 bonus)"
```

---

## Task 7: Migration 008 — ZWDS fields in users table

**Files:**
- Create: `destiny-app/supabase/migrations/008_zwds_fields.sql`
- Modify: `destiny-app/src/lib/supabase/types.ts`

**Step 1: Write the migration**

Create `destiny-app/supabase/migrations/008_zwds_fields.sql`:
```sql
-- Migration 008: ZWDS (紫微斗數) computed fields for Tier 1 users
-- Stores pre-computed chart summary to avoid re-calling ziwei-service on every match

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS zwds_life_palace_stars  TEXT[],   -- 命宮主星 array
  ADD COLUMN IF NOT EXISTS zwds_spouse_palace_stars TEXT[],  -- 夫妻宮主星 array
  ADD COLUMN IF NOT EXISTS zwds_spirit_palace_stars TEXT[],  -- 福德宮主星 array
  ADD COLUMN IF NOT EXISTS zwds_four_transforms     JSONB,   -- {hua_lu, hua_quan, hua_ke, hua_ji}
  ADD COLUMN IF NOT EXISTS zwds_five_element        TEXT,    -- 五行局 (水二局/火六局/土五局/木三局/金四局)
  ADD COLUMN IF NOT EXISTS zwds_body_palace         TEXT;    -- 身宮宮位名稱

COMMENT ON COLUMN public.users.zwds_life_palace_stars  IS '紫微斗數命宮主星 (Tier 1 only)';
COMMENT ON COLUMN public.users.zwds_spouse_palace_stars IS '紫微斗數夫妻宮主星 (Tier 1 only)';
COMMENT ON COLUMN public.users.zwds_spirit_palace_stars IS '紫微斗數福德宮主星 (Tier 1 only)';
COMMENT ON COLUMN public.users.zwds_four_transforms    IS '四化飛星 JSON (hua_lu/hua_quan/hua_ke/hua_ji)';
COMMENT ON COLUMN public.users.zwds_five_element       IS '五行局';
COMMENT ON COLUMN public.users.zwds_body_palace        IS '身宮宮位';
```

**Step 2: Update types.ts**

In `destiny-app/src/lib/supabase/types.ts`, in the `users` table `Row` type, add:
```typescript
zwds_life_palace_stars: string[] | null
zwds_spouse_palace_stars: string[] | null
zwds_spirit_palace_stars: string[] | null
zwds_four_transforms: {
  hua_lu: string; hua_quan: string; hua_ke: string; hua_ji: string;
} | null
zwds_five_element: string | null
zwds_body_palace: string | null
```
Also add to `Insert` and `Update` types (all optional / `| undefined`).

**Step 3: Push migration**

Run: `cd destiny-app && npx supabase db push`
Expected: Migration 008 applied successfully

**Step 4: Commit**

```bash
git add destiny-app/supabase/migrations/008_zwds_fields.sql destiny-app/src/lib/supabase/types.ts
git commit -m "feat: Migration 008 — ZWDS chart fields (Tier 1 VIP)"
```

---

## Task 8: Update birth-data API to call ziwei-service

**Files:**
- Modify: `destiny-app/src/app/api/onboarding/birth-data/route.ts`
- Modify: `destiny-app/src/__tests__/api/onboarding-birth-data.test.ts`

**Background:** After calling `astro-service/calculate-chart` (existing), if `data_tier === 1`, also call `ziwei-service/calculate-zwds` and write back the ZWDS fields. Non-blocking: if ziwei-service is unavailable, onboarding continues normally.

**Step 1: Write failing test**

Add to `destiny-app/src/__tests__/api/onboarding-birth-data.test.ts`:
```typescript
test('Tier 1 user: ZWDS fields written back if ziwei-service available', async () => {
  // Mock fetch for both astro-service and ziwei-service
  ;(global.fetch as jest.Mock)
    .mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockAstroChart }) })   // astro-service
    .mockResolvedValueOnce({ ok: true, json: async () => ({                            // ziwei-service
      chart: mockZwdsChart,
      hour_branch: '午',
    }) });
  // Call with PRECISE birth time
  const res = await POST(makePreciseRequest());
  expect(res.status).toBe(200);
  // Supabase update should have been called with zwds fields
  expect(mockSupabaseUpdate).toHaveBeenCalledWith(
    expect.objectContaining({ zwds_life_palace_stars: expect.any(Array) })
  );
});

test('Tier 1 user: onboarding succeeds even if ziwei-service fails', async () => {
  ;(global.fetch as jest.Mock)
    .mockResolvedValueOnce({ ok: true, json: async () => ({ ...mockAstroChart }) })  // astro-service OK
    .mockRejectedValueOnce(new Error('Connection refused'));                           // ziwei-service fails
  const res = await POST(makePreciseRequest());
  expect(res.status).toBe(200);  // still succeeds
});
```

**Step 2: Run to verify they fail**

Run: `cd destiny-app && npx vitest run src/__tests__/api/onboarding-birth-data.test.ts`
Expected: FAIL (new tests)

**Step 3: Update birth-data route.ts**

Add after the existing astro-service call (inside the `if (data_tier === 1)` branch or after tier check):
```typescript
// Non-blocking ZWDS computation for Tier 1 users
if (data_tier === 1 && birth_time) {
  const ziweiServiceUrl = process.env.ZIWEI_SERVICE_URL ?? 'http://localhost:8002';
  try {
    const zwdsRes = await fetch(`${ziweiServiceUrl}/calculate-zwds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year: birth_year, month: birth_month, day: birth_day,
        birth_time, gender: 'M',  // TODO: collect gender in onboarding
      }),
    });
    if (zwdsRes.ok) {
      const { chart } = await zwdsRes.json();
      // Extract key palace stars
      const getStars = (palaceName: string) =>
        chart.find((p: any) => p.MangB === `【${palaceName}】`)?.StarA ?? [];
      // Compute four transforms from year stem
      const y1Pos = ((birth_year - 4) % 10 + 10) % 10;
      const STAR_S04 = [
        ['廉貞','天機','天同','太陰','貪狼','武曲','太陽','巨門','天梁','破軍'],
        ['破軍','天梁','天機','天同','太陰','貪狼','武曲','太陽','紫微','巨門'],
        ['武曲','紫微','文昌','天機','右弼','天梁','天府','文曲','左輔','太陰'],
        ['太陽','太陰','廉貞','巨門','天機','文曲','天同','文昌','武曲','貪狼'],
      ];
      await supabase.from('users').update({
        zwds_life_palace_stars:   getStars('命宮'),
        zwds_spouse_palace_stars: getStars('夫妻宮'),
        zwds_spirit_palace_stars: getStars('福德宮'),
        zwds_four_transforms: {
          hua_lu:   STAR_S04[0][y1Pos],
          hua_quan: STAR_S04[1][y1Pos],
          hua_ke:   STAR_S04[2][y1Pos],
          hua_ji:   STAR_S04[3][y1Pos],
        },
      }).eq('id', user.id);
    }
  } catch {
    // Non-blocking: ZWDS failure never blocks onboarding
  }
}
```

**Step 4: Add env var**

Add to `.env.local`:
```
ZIWEI_SERVICE_URL=http://localhost:8002
```

**Step 5: Run tests**

Run: `cd destiny-app && npx vitest run src/__tests__/api/onboarding-birth-data.test.ts`
Expected: PASS

**Step 6: Commit**

```bash
git add destiny-app/src/app/api/onboarding/birth-data/route.ts destiny-app/.env.local
git add destiny-app/src/__tests__/api/onboarding-birth-data.test.ts
git commit -m "feat: write ZWDS chart summary to DB on Tier 1 onboarding"
```

---

## Task 9: Update MVP-PROGRESS.md

**Files:**
- Modify: `docs/MVP-PROGRESS.md`

Add to the Phase Summary table:
```markdown
| **Phase H: ZWDS Synastry Engine** | ziwei-service (Node.js port 8002) + Python bridge + matching bonus layer (Tier 1 VIP) | Planned |
```

Add to Python Microservice section:
```markdown
- [ ] `POST /zwds-synastry` — **(Phase H)** 飛星四化 cross-person analysis (Tier 1 only; calls ziwei-service)
```

Add new section:
```markdown
### ziwei-service (`ziwei-service/`)

Node.js 18 Express microservice wrapping the 紫微斗數 JS engine headlessly via Node.js `vm` module.

- [ ] `GET /health` — Health check
- [ ] `POST /calculate-zwds` — Compute 12-palace chart (Place12) from birth data
- [ ] `POST /zwds-synastry` — Return 化祿/化忌/化權 cross-person scores + spouse palace match

**Running ziwei-service:**
```bash
cd ziwei-service
npm install
node server.js   # port 8002
npm test         # Jest tests
```

**Step 1: Update the file**

Edit `docs/MVP-PROGRESS.md` as described above.

**Step 2: Commit**

```bash
git add docs/MVP-PROGRESS.md
git commit -m "docs: add Phase H ZWDS integration to MVP-PROGRESS.md"
```

---

---

## Task 10: Star archetypes + empty palace borrowing

**Files:**
- Create: `ziwei-service/lib/stars-dictionary.js`
- Modify: `ziwei-service/lib/synastry.js`
- Modify: `ziwei-service/test/synastry.test.js`

**Background (from `docs/plans/2026-02-21-ziwei-1.0.md`):**

Two advanced mechanisms:
1. **空宮借對宮 (Empty Palace Borrowing):** If a key palace (命宮/夫妻宮) has no main stars (`StarA.length === 0`), borrow stars from the opposite palace at 0.8 attenuation. A user with empty 命宮 gets flagged `is_fluid: true` → RPV frame auto -15.
2. **14 Star Archetypes:** Each main star has track weights + RPV modifier. Applied to 命宮 stars to shift track scores at the individual level.

Palace opposite pairs:
- 命宮(0) ↔ 遷移宮(6), 夫妻宮(10) ↔ 事業宮(4), 福德宮(2) ↔ 財帛宮(8), 子女宮(9) ↔ 田宅宮(3)

**Step 1: Write failing tests**

Add to `ziwei-service/test/synastry.test.js`:
```javascript
const { getPalaceStarsWithBorrow, isFluidUser } = require('../lib/synastry');

describe('getPalaceStarsWithBorrow', () => {
  test('returns own stars when palace is not empty', () => {
    // Find a palace with stars in chartA
    const ownStars = getPalaceStarsWithBorrow(chartA, '命宮');
    expect(ownStars.is_borrowed).toBe(false);
    expect(ownStars.strength).toBe(1.0);
  });

  test('borrows from opposite palace at 0.8 strength when empty', () => {
    // Create a mock chart where 命宮 is empty
    const mockChart = chartA.map((p, i) => {
      if (p.MangB === '【命宮】') return { ...p, StarA: [] };
      return p;
    });
    const result = getPalaceStarsWithBorrow(mockChart, '命宮');
    expect(result.is_borrowed).toBe(true);
    expect(result.strength).toBe(0.8);
    // Should have stars from opposite palace (遷移宮)
    const oppositeStars = getPalaceStars(chartA, '遷移宮');
    if (oppositeStars.length > 0) {
      expect(result.stars.length).toBeGreaterThan(0);
    }
  });
});

describe('isFluidUser', () => {
  test('returns false when 命宮 has stars', () => {
    expect(isFluidUser(chartA)).toBe(false);
  });

  test('returns true when 命宮 is empty', () => {
    const mockChart = chartA.map(p =>
      p.MangB === '【命宮】' ? { ...p, StarA: [] } : p
    );
    expect(isFluidUser(mockChart)).toBe(true);
  });
});
```

**Step 2: Run to verify they fail**

Run: `cd ziwei-service && npm test -- --testPathPattern=synastry.test.js`
Expected: FAIL with "getPalaceStarsWithBorrow is not a function"

**Step 3: Create stars-dictionary.js**

Create `ziwei-service/lib/stars-dictionary.js`:
```javascript
// 14 main stars (StarM_A14) with track weights and RPV modifiers
// Groups:
//   殺破狼: 七殺(12)、破軍(13)、貪狼(8) → Passion-dominant, high Dom tendency
//   紫府武相: 紫微(0)、天府(6)、武曲(3)、天相(10) → Partner-dominant, Dom tendency
//   機月同梁: 天機(1)、太陰(7)、天同(4)、天梁(11) → Soul/Friend-dominant
//   Others: 太陽(2)→付出, 廉貞(5)→dark passion, 巨門(9)→communication

const STAR_PROFILES = {
  '紫微': { group: 'zi_fu_wu_xiang', track_weights: { passion: 0.1, partner: 0.5, friend: 0.1, soul: 0.3 }, rpv_modifier: 15 },
  '天機': { group: 'ji_yue_tong_liang', track_weights: { passion: 0.1, partner: 0.1, friend: 0.4, soul: 0.4 }, rpv_modifier: -5 },
  '太陽': { group: 'other', track_weights: { passion: 0.2, partner: 0.3, friend: 0.4, soul: 0.1 }, rpv_modifier: 5 },
  '武曲': { group: 'zi_fu_wu_xiang', track_weights: { passion: 0.1, partner: 0.5, friend: 0.2, soul: 0.2 }, rpv_modifier: 10 },
  '天同': { group: 'ji_yue_tong_liang', track_weights: { passion: 0.1, partner: 0.2, friend: 0.5, soul: 0.2 }, rpv_modifier: -10 },
  '廉貞': { group: 'other', track_weights: { passion: 0.4, partner: 0.1, friend: 0.1, soul: 0.4 }, rpv_modifier: 10 },
  '天府': { group: 'zi_fu_wu_xiang', track_weights: { passion: 0.0, partner: 0.6, friend: 0.2, soul: 0.2 }, rpv_modifier: 10 },
  '太陰': { group: 'ji_yue_tong_liang', track_weights: { passion: 0.2, partner: 0.1, friend: 0.3, soul: 0.4 }, rpv_modifier: -10 },
  '貪狼': { group: 'sha_po_lang', track_weights: { passion: 0.6, partner: 0.1, friend: 0.2, soul: 0.1 }, rpv_modifier: 15 },
  '巨門': { group: 'other', track_weights: { passion: 0.1, partner: 0.2, friend: 0.4, soul: 0.3 }, rpv_modifier: 0 },
  '天相': { group: 'zi_fu_wu_xiang', track_weights: { passion: 0.1, partner: 0.4, friend: 0.3, soul: 0.2 }, rpv_modifier: 5 },
  '天梁': { group: 'ji_yue_tong_liang', track_weights: { passion: 0.0, partner: 0.2, friend: 0.4, soul: 0.4 }, rpv_modifier: -5 },
  '七殺': { group: 'sha_po_lang', track_weights: { passion: 0.5, partner: 0.2, friend: 0.1, soul: 0.2 }, rpv_modifier: 20 },
  '破軍': { group: 'sha_po_lang', track_weights: { passion: 0.5, partner: -0.2, friend: 0.1, soul: 0.3 }, rpv_modifier: 15 },
};

// Opposite palaces for empty-palace borrowing
// Palace index 0-11 in Place12 (runtime position varies; use MangB label matching)
const OPPOSITE_PALACE_MAP = {
  '命宮': '遷移宮', '遷移宮': '命宮',
  '夫妻宮': '官祿宮', '官祿宮': '夫妻宮',
  '福德宮': '財帛宮', '財帛宮': '福德宮',
  '子女宮': '田宅宮', '田宅宮': '子女宮',
  '父母宮': '疾厄宮', '疾厄宮': '父母宮',
  '兄弟宮': '交友宮', '交友宮': '兄弟宮',
};

function getStarProfile(starName) {
  const baseName = starName.replace(/化[祿權科忌]$/, '');
  return STAR_PROFILES[baseName] || null;
}

module.exports = { STAR_PROFILES, OPPOSITE_PALACE_MAP, getStarProfile };
```

**Step 4: Add empty palace borrowing to synastry.js**

Add the following to `ziwei-service/lib/synastry.js`:
```javascript
const { OPPOSITE_PALACE_MAP, getStarProfile } = require('./stars-dictionary');

/**
 * Get stars from a palace, borrowing from the opposite palace at 0.8 strength if empty.
 * Returns { stars, strength, is_borrowed }
 */
function getPalaceStarsWithBorrow(chart, palaceName) {
  const label = `【${palaceName}】`;
  const palace = chart.find(p => p.MangB === label);
  if (!palace) return { stars: [], strength: 1.0, is_borrowed: false };

  if (palace.StarA.length > 0) {
    return { stars: [...palace.StarA], strength: 1.0, is_borrowed: false };
  }

  // Empty palace — borrow from opposite
  const oppositeName = OPPOSITE_PALACE_MAP[palaceName];
  const oppositeStars = oppositeName ? getPalaceStars(chart, oppositeName) : [];
  return { stars: oppositeStars, strength: 0.8, is_borrowed: true };
}

/**
 * Return true if user's 命宮 is empty (no main stars).
 * Empty 命宮 = fluid user → auto RPV frame -15.
 */
function isFluidUser(chart) {
  const { stars } = getPalaceStarsWithBorrow(chart, '命宮');
  // If result came from borrow, the original 命宮 was empty
  const label = '【命宮】';
  const palace = chart.find(p => p.MangB === label);
  return !palace || palace.StarA.length === 0;
}

/**
 * Compute individual star archetype bonus for one user's 命宮.
 * Returns { passion, partner, friend, soul, rpv_modifier } adjustments.
 */
function computeStarArchetypeBonus(chart) {
  const { stars } = getPalaceStarsWithBorrow(chart, '命宮');
  const bonus = { passion: 0, partner: 0, friend: 0, soul: 0, rpv_modifier: 0 };
  for (const starName of stars) {
    const profile = getStarProfile(starName);
    if (!profile) continue;
    bonus.passion    += profile.track_weights.passion * 0.1;
    bonus.partner    += profile.track_weights.partner * 0.1;
    bonus.friend     += profile.track_weights.friend  * 0.1;
    bonus.soul       += profile.track_weights.soul    * 0.1;
    bonus.rpv_modifier += profile.rpv_modifier;
  }
  return bonus;
}
```

In `computeZwdsSynastry()`, add these after computing `spouse_match_b_sees_a`:
```javascript
  // Empty palace fluid check → RPV modifier
  const is_fluid_a = isFluidUser(chartA);
  const is_fluid_b = isFluidUser(chartB);
  if (is_fluid_a) rpv_modifier -= 15;
  if (is_fluid_b) rpv_modifier += 15;

  // Star archetype bonus
  const archetypeA = computeStarArchetypeBonus(chartA);
  const archetypeB = computeStarArchetypeBonus(chartB);
```

Export new functions:
```javascript
module.exports = {
  computeZwdsSynastry,
  extractSynastrySummary,
  getPalaceStars,
  getPalaceStarsWithBorrow,
  findStarPalace,
  spousePalaceMatch,
  isFluidUser,
  computeStarArchetypeBonus,
};
```

**Step 5: Run all synastry tests**

Run: `cd ziwei-service && npm test -- --testPathPattern=synastry.test.js`
Expected: PASS (all tests including new empty palace tests)

**Step 6: Commit**

```bash
git add ziwei-service/lib/stars-dictionary.js ziwei-service/lib/synastry.js
git add ziwei-service/test/synastry.test.js
git commit -m "feat: empty palace borrowing + star archetype weights in ZWDS synastry"
```

---

## Final Test Count Target

| Test File | New Tests | Total After |
|-----------|-----------|-------------|
| `ziwei-service/test/engine.test.js` | 8 | +8 |
| `ziwei-service/test/synastry.test.js` | 12 | +12 |
| `ziwei-service/test/server.test.js` | 5 | +5 |
| `astro-service/test_zwds.py` | 7 | +7 |
| `astro-service/test_matching.py` | 5 | +5 |
| `destiny-app/test_birth-data.test.ts` | 2 | +2 |
| **Total new tests** | **39** | |

---

## Running the Full Stack (Phase H)

```bash
# Terminal 1: ziwei-service
cd ziwei-service && npm install && node server.js   # port 8002

# Terminal 2: astro-service (existing)
cd astro-service && uvicorn main:app --port 8001    # port 8001

# Terminal 3: Next.js app (existing)
cd destiny-app && npm run dev                        # port 3000

# Run all tests
cd ziwei-service && npm test
cd astro-service && pytest -v
cd destiny-app && npx vitest run
```
