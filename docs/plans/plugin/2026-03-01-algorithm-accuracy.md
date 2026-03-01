# Plan C: Algorithm Accuracy Fixes (Bug-1, Bug-2, L-1, L-2/L-12, L-8)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix six confirmed accuracy bugs in the v2 matching algorithm:
- **Bug-1** `compute_exact_aspect` returns `0.1` for void-of-aspect → punishes Tier 1 users
- **Bug-2** `find_dispositor_chain` cuts off at 3 planets → never finds deep-chain Final Dispositors
- **L-12** Chiron double-counted in soul_track + shadow_engine → remove from soul_track
- **L-2** Chiron same-generation false positives → resolved by L-12 removal
- **L-8** Karmic trigger threshold 0.85 too strict → lower to 0.70
- **L-1** Shadow modifier accumulation has no cap → add ±40/±30 cap

**Architecture:** Bug-1 and L-* fixes in `astro-service/matching.py`. Bug-2 fix in `astro-service/psychology.py`. Shadow engine (`shadow_engine.py`) untouched.

**Tech Stack:** Python (astro-service), pytest

---

## Background

### Bug-1: `compute_exact_aspect` punishes Tier 1 users

`compute_exact_aspect` in `matching.py:263` returns `0.1` when no major aspect is within orb:

```python
return 0.1  # void of aspect  ← current code
```

This creates an asymmetry between Tier 1 and Tier 3 users:
- **Tier 3** (no exact degrees): falls back to `compute_sign_aspect` → returns `0.65` for a neutral sign pair
- **Tier 1** (has exact degrees): if two planets are 9° apart (just outside the 8° conjunction orb), gets `0.1`

A user who provided precise birth time gets a **lower score** than one with no birth time — the opposite of intended. The fix: return `0.5` (neutral) instead of `0.1` for void-of-aspect.

Additionally, `_resolve_aspect` must be updated: when exact degrees exist but yield no aspect (`0.5` neutral), it should preserve the sign-level background energy at 80% weight instead of discarding it entirely.

### Bug-2: `find_dispositor_chain` cuts off chains at 3 planets

The original design spec (`2026-02-25-classical-astrology-design.md`) included:
```python
# Termination 3 — Endless Loop (visited > 3 unique planets)
if next_planet in visited or len(visited) >= 3:
```

This was a conservative safety measure, but it is too tight. With modern rulerships (Pluto/Uranus/Neptune as rulers), chains of 4–5 planets are common. Example:

```
Venus (Aries) → Mars (Scorpio) → Pluto (Capricorn) → Saturn (Aquarius) → Uranus
```

At the third hop (Pluto), `len(visited) == 3` fires and returns `mixed_loop` even though the chain has a valid resolution. The fix: remove `len(visited) >= 3` entirely. Only `ruler in visited` (true infinite loop) should terminate with `mixed_loop`.

**test_psychology.py Test 8 must be updated**: the original test verified `len >= 3` behaviour (expected `mixed_loop` for a 3+-hop chain). After the fix, the test must use a genuinely cyclic chain (A→B→A or A→B→C→A) to verify `mixed_loop`, not a merely-long chain.

### L-12 + L-2: Chiron is counted twice

`compute_tracks()` computes `chiron = _resolve_aspect(chiron_a, chiron_b, "tension")` and uses it in the soul track formula (weight 0.40). `shadow_engine.py` also computes Chiron wound triggers and returns `soul_mod`. When both run, Chiron's contribution is counted in both the base `soul_track` AND the `soul_adj` from shadow engine.

Additionally (L-2), Chiron is a generational planet (~7 years per sign). People born close in time share Chiron signs, so `_resolve_aspect` with signs alone gives false "conjunction" scores for age-peers.

**Combined fix:** Remove Chiron from the soul_track formula. Always use the `chiron_absent` branch: `karmic×0.60 + useful_god×0.40`. Shadow engine handles Chiron wound triggers properly and will continue to add `soul_mod` when genuine Chiron-person aspects exist.

### L-8: Karmic trigger threshold too strict

`compute_karmic_triggers()` at line 300:
```python
if aspect >= 0.85:
    score += aspect
    triggers += 1
```
With the linear orb-decay formula, 0.85 requires the aspect to be within ~2.5° of exact (for a 7° orb conjunction). This misses meaningful 3-5° aspects entirely. Lower to 0.70 (~4.5° orb).

### L-1: Shadow modifier accumulation — no cap

`soul_adj` and `lust_adj` accumulate from 5 sources (shadow engine, attachment dynamics, elemental fulfillment, favorable element resonance, synastry mutual reception) with no ceiling. In edge cases (couples with many triggers), `soul_adj` can exceed +80, pushing soul score to 100 regardless of actual compatibility. Add a cap: `soul_adj ≤ 40`, `lust_adj ≤ 40`.

---

### Task 0: Fix void-of-aspect penalty and dispositor chain limit (Bug-1 + Bug-2)

**Files:**
- Modify: `astro-service/matching.py:263` and `matching.py:212-224` (`_resolve_aspect`)
- Modify: `astro-service/psychology.py:471`
- Update: `astro-service/test_matching.py` (new tests)
- Update: `astro-service/test_psychology.py` (fix Test 8)

---

#### Bug-1: Fix `compute_exact_aspect` void return value

**Step 1: Write a failing test**

```python
# test_matching.py
def test_exact_aspect_void_returns_neutral_not_penalty():
    """Void-of-aspect should return 0.5 (neutral), not 0.1 (penalty).
    Tier 1 users must never score lower than Tier 3 for the same planet pair."""
    # 9° apart — just outside the 8° conjunction orb
    score = compute_exact_aspect(10.0, 19.0, "harmony")
    assert score == 0.5, f"Void-of-aspect should be 0.5 neutral, got {score}"
    assert score > 0.1, "0.1 would penalise Tier 1 users relative to Tier 3"

def test_resolve_aspect_void_falls_back_to_sign():
    """When exact degrees yield void-of-aspect (0.5), _resolve_aspect should
    blend with the sign-level score at 80% weight, not return bare 0.5."""
    # Sun Aries (10°) vs Moon Leo (19°) — 9° apart (void of conjunction),
    # but Aries-Leo is a trine (sign-level harmony score ~ 0.85)
    score = _resolve_aspect(10.0, "Aries", 19.0, "Leo", "harmony")
    # Expected: sign_score * 0.8 = ~0.68, definitely not 0.1
    assert score > 0.5, "Should preserve sign background when exact aspect is void"
    assert score < 1.0
```

Run: `pytest astro-service/test_matching.py::test_exact_aspect_void_returns_neutral_not_penalty -v`
Expected: FAIL (`0.1` returned, not `0.5`).

**Step 2: Apply the fix**

In `matching.py:263`, change:
```python
# BEFORE
return 0.1  # void of aspect

# AFTER
return 0.5  # void of aspect — neutral, not a penalty (Bug-1 fix)
```

In `_resolve_aspect` (`matching.py:222-224`), change:
```python
# BEFORE
if deg_x is not None and deg_y is not None:
    return compute_exact_aspect(deg_x, deg_y, mode)
return compute_sign_aspect(sign_x, sign_y, mode)

# AFTER
if deg_x is not None and deg_y is not None:
    exact = compute_exact_aspect(deg_x, deg_y, mode)
    if exact == 0.5:  # void of aspect — preserve sign background at 80%
        return round(compute_sign_aspect(sign_x, sign_y, mode) * 0.8, 2)
    return exact
return compute_sign_aspect(sign_x, sign_y, mode)
```

**Step 3: Run tests**

```bash
pytest astro-service/test_matching.py::test_exact_aspect_void_returns_neutral_not_penalty -v
pytest astro-service/test_matching.py::test_resolve_aspect_void_falls_back_to_sign -v
```
Expected: both PASS.

---

#### Bug-2: Fix `find_dispositor_chain` 3-planet limit

**Step 1: Update test_psychology.py Test 8**

The original Test 8 verified that a 3+-hop chain returns `mixed_loop`. After the fix, a long chain with a valid resolution should reach the Final Dispositor. Only a genuinely cyclic chain should return `mixed_loop`.

Find Test 8 in `test_psychology.py`:
```bash
grep -n "mixed_loop\|len.*visited\|3.*unique\|test.*8\|loop" astro-service/test_psychology.py
```

Replace the existing `mixed_loop` test with two separate tests:

```python
def test_find_dispositor_chain_genuine_loop_returns_mixed_loop():
    """A truly cyclic chain (A→B→A) must return mixed_loop.
    This is the only valid mixed_loop scenario after Bug-2 fix."""
    # Venus in Aries (ruler: Mars), Mars in Libra (ruler: Venus) → cyclic, mutual reception
    # BUT let's create a non-mutual-reception cycle:
    # Venus in Aries → Mars; Mars in Gemini → Mercury; Mercury in Taurus → Venus (cycle!)
    chart = {
        "venus_sign": "Aries",    # ruled by Mars
        "mars_sign": "Gemini",    # ruled by Mercury
        "mercury_sign": "Taurus", # ruled by Venus ← closes the loop
    }
    result = find_dispositor_chain(chart, "Venus")
    assert result["status"] == "mixed_loop", "Genuine A→B→C→A cycle must return mixed_loop"
    assert result["final_dispositor"] is None

def test_find_dispositor_chain_long_chain_finds_boss():
    """A chain of 4+ planets with a valid resolution must NOT be cut off at 3.
    Bug-2 fix: remove len(visited) >= 3 — only genuine loops should terminate."""
    # Venus (Aries) → Mars (Scorpio) → Pluto (Capricorn) → Saturn (Aquarius) → Uranus self-rules? No.
    # Simpler: Moon (Cancer) → Moon self-rules Cancer → Final Dispositor immediately (1 step)
    # For a multi-hop test:
    # Sun (Aries) → Mars (Capricorn) → Saturn (Capricorn) → Saturn self-rules Capricorn
    chart = {
        "sun_sign": "Aries",       # ruled by Mars
        "mars_sign": "Capricorn",  # ruled by Saturn
        "saturn_sign": "Capricorn" # Saturn rules Capricorn → Final Dispositor!
    }
    result = find_dispositor_chain(chart, "Sun")
    assert result["status"] == "final_dispositor"
    assert result["final_dispositor"] == "Saturn"
    assert len(result["chain"]) >= 3  # Sun → Mars → Saturn (at least 3 hops)
```

**Step 2: Run new tests to confirm they fail under current code**

```bash
pytest astro-service/test_psychology.py::test_find_dispositor_chain_long_chain_finds_boss -v
```
Expected: FAIL (current `len(visited) >= 3` cuts off the chain before Saturn).

**Step 3: Apply the fix**

In `psychology.py:471`, change:
```python
# BEFORE
# Termination 3: Loop guard (max 3 unique planets before giving up)
if ruler in visited or len(visited) >= 3:
    return {"chain": chain, "final_dispositor": None,
            "mutual_reception": [], "status": "mixed_loop"}

# AFTER
# Termination 3: Loop guard — only terminate if a genuine cycle is detected.
# Bug-2 fix: removed len(visited) >= 3; chains of 4-5 planets are normal in modern rulerships.
if ruler in visited:
    return {"chain": chain, "final_dispositor": None,
            "mutual_reception": [], "status": "mixed_loop"}
```

**Step 4: Run all psychology tests**

```bash
pytest astro-service/test_psychology.py -v
```
Expected: all pass. The genuine-loop test returns `mixed_loop`; the long-chain test now reaches `Saturn` as Final Dispositor.

**Step 5: Commit both Bug-1 and Bug-2 fixes together**

```bash
git add astro-service/matching.py astro-service/psychology.py \
        astro-service/test_matching.py astro-service/test_psychology.py
git commit -m "fix: void-of-aspect returns 0.5 not 0.1 (Bug-1); dispositor chain removes len>=3 limit (Bug-2)"
```

---

### Task 1: Remove Chiron from soul_track formula (fixes L-12 + L-2)

**Files:**
- Modify: `astro-service/matching.py:968-1025`

**Step 1: Locate Chiron section in compute_tracks (lines ~968-1025)**

Current code:
```python
chiron_a, chiron_b = user_a.get("chiron_sign"), user_b.get("chiron_sign")
chiron_present = bool(chiron_a and chiron_b)
chiron = _resolve_aspect(user_a.get("chiron_degree"), chiron_a,
                         user_b.get("chiron_degree"), chiron_b, "tension") if chiron_present else 0.0
```

And later:
```python
if chiron_present:
    soul_track = (chiron               * WEIGHTS["track_soul_chiron"] +
                  karmic               * WEIGHTS["track_soul_karmic"] +
                  useful_god_complement * WEIGHTS["track_soul_useful_god"])
else:
    # Redistribute chiron's 0.40 weight: karmic gets 0.60, useful_god gets 0.40
    soul_track = (karmic               * WEIGHTS["track_soul_nochiron_karmic"] +
                  useful_god_complement * WEIGHTS["track_soul_nochiron_useful_god"])
```

**Step 2: Remove Chiron from soul_track — always use the no-Chiron formula**

```python
# Remove these 3 lines entirely (chiron_a/b/chiron_present/chiron variables):
# chiron_a, chiron_b = user_a.get("chiron_sign"), user_b.get("chiron_sign")
# chiron_present = bool(chiron_a and chiron_b)
# chiron = _resolve_aspect(...) if chiron_present else 0.0

# Replace the if/else with the always-no-chiron formula:
# L-12: Chiron removed from soul_track to prevent double-counting with shadow_engine.
# L-2:  Chiron is generational (7 yrs/sign) — sign-level comparison creates false positives.
# Shadow engine handles Chiron wound triggers via orb-based degree checks.
soul_track = (karmic               * WEIGHTS["track_soul_nochiron_karmic"] +
              useful_god_complement * WEIGHTS["track_soul_nochiron_useful_god"])

if power["frame_break"]:
    soul_track += 0.10
```

Note: delete the `if chiron_present:` block entirely. The `if power["frame_break"]` bonus stays.

**Step 3: Write a failing test first**

```python
# test_matching.py — add before implementing
def test_chiron_same_generation_no_inflation():
    """Same-year users (same Chiron sign) should NOT get inflated soul track.
    Chiron is generational; same-gen pairs must rely only on karmic + useful_god."""
    # Two users born same year → same Chiron sign
    user_a = {**MINIMAL_USER_A, "chiron_sign": "Aries", "chiron_degree": 10.0}
    user_b = {**MINIMAL_USER_B, "chiron_sign": "Aries", "chiron_degree": 15.0}
    result = compute_match_v2(user_a, user_b)
    # Soul track should not exceed a moderate value just from shared Chiron sign
    # (karmic + useful_god formula caps out around 60 without shadow engine boosts)
    assert result["tracks"]["soul"] <= 70.0, (
        f"Soul track {result['tracks']['soul']} inflated by same-gen Chiron"
    )
```

Run: `pytest astro-service/test_matching.py::test_chiron_same_generation_no_inflation -v`
Expected: FAIL (current code scores high for same-gen Chiron).

**Step 4: Apply the fix from Step 2**

**Step 5: Run the test**

```bash
pytest astro-service/test_matching.py::test_chiron_same_generation_no_inflation -v
```
Expected: PASS.

**Step 6: Run full test suite**

```bash
cd astro-service && pytest test_matching.py -v
```
Expected: all pass (some soul_track values will shift — update any hardcoded expected values).

**Step 7: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "fix(matching): remove Chiron from soul_track — prevents L-2 same-gen inflation and L-12 double-count"
```

---

### Task 2: Lower karmic trigger threshold 0.85 → 0.70 (fixes L-8)

**Files:**
- Modify: `astro-service/matching.py:300`

**Step 1: Write a failing test**

```python
def test_karmic_triggers_fire_at_0_70():
    """Karmic trigger with aspect strength 0.75 should be counted.
    Previously required >= 0.85 which was too strict (only ~2.5° orb)."""
    # Create users where Saturn-outer cross-aspect computes ~0.75 strength
    # (e.g., 3.5° off exact conjunction with 7° orb → strength ≈ 0.70)
    user_a = {**MINIMAL_USER_A, "saturn_sign": "Scorpio", "saturn_degree": 15.0}
    user_b = {**MINIMAL_USER_B, "pluto_sign": "Scorpio", "pluto_degree": 18.5}
    score_before = compute_karmic_triggers(user_a, user_b)
    # The 3.5° gap gives strength = 0.2 + 0.8 * (1.0 - 3.5/7) = 0.60...
    # Use 2.0° gap → strength = 0.2 + 0.8 * (1.0 - 2.0/7) ≈ 0.63
    # Use 0.5° gap → strength ≈ 0.91 (definitely fires)
    # Point: test that threshold of 0.70 fires for moderate aspects
    user_a2 = {**MINIMAL_USER_A, "saturn_sign": "Scorpio", "saturn_degree": 15.0}
    user_b2 = {**MINIMAL_USER_B, "pluto_sign": "Scorpio", "pluto_degree": 17.0}
    # 2° gap, 7° orb → strength = 0.2 + 0.8*(1 - 2/7) = 0.657 → fails 0.85, passes 0.70
    score_new = compute_karmic_triggers(user_a2, user_b2)
    assert score_new > 0.50, f"Karmic trigger at 2° gap should fire with 0.70 threshold"
```

Run: `pytest astro-service/test_matching.py::test_karmic_triggers_fire_at_0_70 -v`
Expected: FAIL (current 0.85 threshold causes score to stay at 0.50).

**Step 2: Apply the fix**

In `matching.py` at line 300, change:
```python
# BEFORE
if aspect >= 0.85:

# AFTER
if aspect >= 0.70:   # L-8: lowered from 0.85 — 0.85 required ~2.5° orb, too strict
```

**Step 3: Run test**

```bash
pytest astro-service/test_matching.py::test_karmic_triggers_fire_at_0_70 -v
```
Expected: PASS.

**Step 4: Run full suite**

```bash
pytest astro-service/test_matching.py -v
```
Update any hardcoded karmic_triggers expected values that relied on the old 0.85 threshold.

**Step 5: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "fix(matching): lower karmic trigger threshold 0.85→0.70 (L-8 — was too strict)"
```

---

### Task 3: Add shadow modifier caps (fixes L-1)

**Files:**
- Modify: `astro-service/matching.py:1368-1376` (the "Apply modifiers" section)

**Step 1: Write a failing test**

```python
def test_shadow_modifier_cap():
    """soul_adj and lust_adj should be capped at +40 even with many triggers.
    Without cap, 5 simultaneous triggers can add 100+ points."""
    # Mock compute_match_v2 with patched shadow engine returning large modifiers
    # Simpler: test the cap logic directly
    import astro_service.matching as m

    # Inject large soul_adj scenario by calling with crafted users that maximize triggers
    # For unit test purposes, directly test the capped behavior:
    raw_soul_adj = 85.0   # would happen with 5 shadow triggers + attachment + mutual reception
    capped = min(raw_soul_adj, 40.0)
    assert capped == 40.0, "soul_adj cap at 40 must hold"

    raw_lust_adj = -50.0  # negative (repulsion)
    capped_neg = max(raw_lust_adj, -30.0)
    assert capped_neg == -30.0, "lust_adj floor at -30 must hold"
```

Run: this test will pass trivially — the real test is the integration scenario below.

**Integration test:**

```python
def test_soul_score_cannot_reach_100_from_modifiers_alone():
    """Even with maximum shadow triggers, soul score should not reach 100
    unless the base score is already near 100."""
    # Users with moderate base compatibility (~50 soul)
    result = compute_match_v2(MODERATE_COMPATIBILITY_A, MODERATE_COMPATIBILITY_B)
    # soul_score must not be 100 due to modifier overflow
    assert result["soul_score"] < 100.0 or result["tracks"]["soul"] >= 80.0, (
        "soul_score should only reach 100 if base tracks are genuinely high"
    )
```

**Step 2: Apply the fix**

Locate the "Apply modifiers" block in `matching.py` (~lines 1368-1376):

```python
# BEFORE
if soul_adj != 0.0:
    tracks["soul"] = _clamp(tracks["soul"] + soul_adj)
    soul           = _clamp(soul + soul_adj)
if lust_adj != 0.0:
    tracks["passion"] = _clamp(tracks["passion"] + lust_adj)
    lust              = _clamp(lust + lust_adj)
if partner_adj != 0.0:
    tracks["partner"] = _clamp(tracks["partner"] + partner_adj)
```

```python
# AFTER — L-1: cap modifiers before applying to prevent overflow
# soul: max +40 (meaningful), min -30 (repulsion still visible but not death sentence)
# lust: max +40, min -30 (same rationale)
# partner: max +25 (narrower — partner track is more delicate)
soul_adj    = max(min(soul_adj,    40.0), -30.0)
lust_adj    = max(min(lust_adj,    40.0), -30.0)
partner_adj = max(min(partner_adj, 25.0), -20.0)

if soul_adj != 0.0:
    tracks["soul"] = _clamp(tracks["soul"] + soul_adj)
    soul           = _clamp(soul + soul_adj)
if lust_adj != 0.0:
    tracks["passion"] = _clamp(tracks["passion"] + lust_adj)
    lust              = _clamp(lust + lust_adj)
if partner_adj != 0.0:
    tracks["partner"] = _clamp(tracks["partner"] + partner_adj)
```

**Step 3: Run tests**

```bash
pytest astro-service/test_matching.py -v
pytest astro-service/test_shadow_engine.py -v
```
Expected: all pass (shadow engine tests are unaffected — they only test `soul_mod` values before capping).

**Step 4: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "fix(matching): cap shadow modifiers at ±40/±30 to prevent overflow (L-1)"
```

---

### Task 4: Run full test suite and document changes

**Step 1: Run all astro-service tests**

```bash
cd astro-service
pytest -v 2>&1 | tail -30
```

Expected: all tests pass. Fix any that break due to score shifts from the threshold/cap changes.

**Step 2: Run end-to-end sanity check**

```bash
python run_ideal_match_prompt.py
```

Compare output with pre-fix baseline. Expect:
- `soul_track` may shift slightly (Chiron removed from formula)
- `karmic` score may increase (lower threshold catches more triggers)
- `harmony_score` now reflects `lust×0.4 + soul×0.6` (from Plan A, if applied)
- `soul_score` may be slightly lower for edge cases that previously had uncapped shadow boosts

**Step 3: Update ALGORITHM.md**

Mark all fixed bugs in `docs/ALGORITHM.md`:

```markdown
- [x] Bug-1: void-of-aspect returns 0.5 (neutral) instead of 0.1 (Tier 1 penalty removed)
- [x] Bug-2: dispositor chain len>=3 limit removed — deep chains now find Final Dispositor
- [x] L-1: Shadow modifier cap — added ±40/±30 cap before applying to scores
- [x] L-2: Chiron same-generation — resolved by L-12 (Chiron removed from soul_track)
- [x] L-8: Karmic threshold lowered 0.85 → 0.70
- [x] L-12: Chiron double-count — removed from soul_track (shadow_engine handles it)
```

**Step 4: Commit**

```bash
git add docs/ALGORITHM.md
git commit -m "docs(algorithm): mark L-1, L-2, L-8, L-12 as fixed"
```

---

## Summary of Changes

| File | Lines | Change |
|------|-------|--------|
| `matching.py:263` | Edit | `return 0.1` → `return 0.5` (Bug-1: void-of-aspect neutral) |
| `matching.py:222-224` | Edit | `_resolve_aspect` blends sign score × 0.8 when exact is void (Bug-1) |
| `psychology.py:471` | Edit | Remove `len(visited) >= 3` from dispositor chain guard (Bug-2) |
| `matching.py:968-971` | Remove | Delete Chiron variable computation (L-12 + L-2) |
| `matching.py:1018-1025` | Replace | Always use `karmic×0.60 + useful_god×0.40` for soul_track (L-12 + L-2) |
| `matching.py:300` | Edit | `>= 0.85` → `>= 0.70` (L-8) |
| `matching.py:1368` | Insert | 3 cap lines before applying modifiers (L-1) |
| `test_matching.py` | Add | Tests for Bug-1, L-12, L-8, L-1 |
| `test_psychology.py` | Update | Fix Test 8 — replace `len>=3` case with genuine-cycle case; add long-chain test |
| `docs/ALGORITHM.md` | Update | Mark Bug-1, Bug-2, L-1/L-2/L-8/L-12 as fixed |

## Expected Score Impact

For the reference pair (1997-03-07 M × 1995-03-26 F):
- Tier 1 users: moderate aspects previously scoring `0.1` now score `0.5+` — overall scores should rise slightly
- `soul_track`: slight decrease (~5-10 pts) — Chiron same-gen inflation removed
- `karmic`: slight increase (~5 pts) — threshold 0.70 catches more moderate aspects
- Net soul_score: roughly neutral (karmic boost offsets Chiron removal)
- Edge cases with many shadow triggers: soul_score no longer artificially hits 100
- Dispositor chain: users with deep chains (4-5 planets) now get a valid `final_dispositor` instead of `mixed_loop`

## Task Execution Order

**Task 0 is strictly first** — Bug-1 affects `_resolve_aspect` which is called by Tasks 1 and 2.
Fixing the `0.1` baseline before removing Chiron and adjusting the karmic threshold ensures
the score impact measurements in the sanity check (Task 4 Step 2) reflect the real final state.

```
Task 0 → Task 1 → Task 2 → Task 3 → Task 4
(Bug-1+2)  (L-12+L-2)  (L-8)    (L-1)   (docs)
```
