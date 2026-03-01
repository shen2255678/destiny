# Plan A: Fix harmony_score Formula

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the `harmony_score = soul_score` alias with a real weighted formula (`lust×0.4 + soul×0.6`), so the UI-facing "綜合評分" actually reflects both axes.

**Architecture:** Single-line fix in `matching.py` return dict + update downstream test assertions. No schema changes required.

**Tech Stack:** Python (astro-service), pytest, TypeScript (destiny-mvp lounge page)

---

## Background

`compute_match_v2()` currently returns:
```python
"harmony_score": round(soul, 1),   # matching.py:1447 — BUG: pure soul alias
```

This means "綜合評分 72" and "靈魂共鳴 72" are always identical — confusing and misleading. The intended semantic is a weighted blend: soul-depth matters more (0.6) than physical pull (0.4), per product philosophy.

---

### Task 1: Fix harmony_score formula in matching.py

**Files:**
- Modify: `astro-service/matching.py:1447`

**Step 1: Open matching.py and locate line 1447**

```python
# BEFORE (line 1447)
"harmony_score":           round(soul, 1),

# AFTER
"harmony_score":           round(lust * 0.4 + soul * 0.6, 1),
```

The variables `lust` and `soul` are both in scope at that point (computed earlier in the function). No other changes needed in this function.

**Step 2: Verify manually with a sanity check**

Given the test values from `run_ideal_match_prompt.py` defaults (1997-03-07 × 1995-03-26):
- lust ≈ 29.0, soul ≈ 72.1
- New harmony = 29.0 × 0.4 + 72.1 × 0.6 = **54.9** (was 72.1)

This is a meaningful difference — the old alias was misleading users by showing 72/72.

**Step 3: Commit**

```bash
git add astro-service/matching.py
git commit -m "fix(matching): harmony_score = lust*0.4 + soul*0.6 instead of soul alias"
```

---

### Task 2: Update test_matching.py assertions

**Files:**
- Modify: `astro-service/test_matching.py`

**Step 1: Find harmony_score assertions**

```bash
grep -n "harmony_score" astro-service/test_matching.py
```

**Step 2: Update each assertion to use the weighted formula**

For each test that asserts on `harmony_score`, change the expected value from `soul_score` to `round(lust * 0.4 + soul * 0.6, 1)`.

Example pattern:
```python
# BEFORE
assert result["harmony_score"] == result["soul_score"]

# AFTER
expected_harmony = round(result["lust_score"] * 0.4 + result["soul_score"] * 0.6, 1)
assert result["harmony_score"] == expected_harmony
```

Also add a dedicated test to document the contract:

```python
def test_harmony_score_is_weighted_blend():
    """harmony_score should be lust*0.4 + soul*0.6, not a soul alias."""
    result = compute_match_v2(SAMPLE_USER_A, SAMPLE_USER_B)
    expected = round(result["lust_score"] * 0.4 + result["soul_score"] * 0.6, 1)
    assert result["harmony_score"] == expected
    # Verify it is NOT equal to soul alone (unless they happen to be equal by chance)
    # This is a documentation assertion, not a strict inequality test
```

**Step 3: Run tests**

```bash
cd astro-service
pytest test_matching.py -v -k "harmony"
pytest test_matching.py -v   # full suite
```

Expected: all tests pass.

**Step 4: Commit**

```bash
git add astro-service/test_matching.py
git commit -m "test(matching): update harmony_score assertions to weighted formula"
```

---

### Task 3: Verify destiny-mvp lounge page reads correctly

**Files:**
- Read: `destiny-mvp/app/lounge/page.tsx`

**Step 1: Check how harmony is consumed**

Look for `scores.harmony` in the lounge page. Current code:
```typescript
harmony = Math.round(scores.harmony),  // reads harmony_score from API
```

This reads `harmony_score` from the API response correctly — no change needed. The UI will automatically show the new blended value.

**Step 2: Check destiny_pipeline.py**

```bash
grep -n "harmony" astro-service/destiny_pipeline.py
```

In `_build_scores()`:
```python
"harmony": round(m.get("harmony_score", 0), 1),
```

This just passes through whatever `compute_match_v2` returns — no change needed.

**Step 3: Confirm run_ideal_match_prompt.py output**

Run with defaults to verify the new harmony shows a blended value:
```bash
cd astro-service
python run_ideal_match_prompt.py
```

The printed output should now show harmony ≠ soul (previously they were identical).

**Step 4: Commit (if any changes needed)**

If no changes needed in lounge/page.tsx or destiny_pipeline.py:
```bash
git commit --allow-empty -m "chore: verify harmony_score downstream consumers — no changes needed"
```

---

## Expected Outcome

| Field | Before | After |
|-------|--------|-------|
| `harmony_score` | 72.1 (= soul alias) | 54.9 (= lust×0.4 + soul×0.6) |
| `lust_score` | 29.0 | 29.0 (unchanged) |
| `soul_score` | 72.1 | 72.1 (unchanged) |

The "綜合評分" in the UI will now be a meaningful blend, not a duplicate of "靈魂共鳴".
