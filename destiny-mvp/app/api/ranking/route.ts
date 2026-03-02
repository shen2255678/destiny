import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/service";
import { NextRequest, NextResponse } from "next/server";

const ASTRO = process.env.ASTRO_SERVICE_URL ?? "http://localhost:8001";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const CONCURRENCY = 5;

interface NatalCache {
  western_chart?: Record<string, unknown>;
  bazi_chart?: Record<string, unknown>;
}

/** Flatten natal_cache JSONB into the flat dict compute_quick_score expects. */
function flattenNatalCache(nc: NatalCache): Record<string, unknown> {
  const flat: Record<string, unknown> = {};
  const wc = (nc.western_chart ?? {}) as Record<string, unknown>;
  const bc = (nc.bazi_chart ?? {}) as Record<string, unknown>;
  Object.assign(flat, wc);
  flat.bazi_element = bc.day_master_element ?? wc.bazi_element;
  flat.bazi_month_branch = bc.bazi_month_branch ?? wc.bazi_month_branch;
  flat.bazi_day_branch = bc.bazi_day_branch ?? wc.bazi_day_branch;
  flat.bazi = bc;
  if (!flat.data_tier) flat.data_tier = wc.data_tier ?? 3;
  // RPV neutral defaults — soul_cards doesn't store RPV data
  flat.rpv_conflict = "argue";
  flat.rpv_power = "follow";
  flat.rpv_energy = "home";
  return flat;
}

const FETCH_TIMEOUT_MS = 5000;

/** Call astro-service /quick-score with concurrency limit. */
async function batchQuickScore(
  userA: Record<string, unknown>,
  targets: Array<{ id: string; flat: Record<string, unknown> }>,
  concurrency: number
): Promise<
  Array<{
    card_b_id: string;
    harmony: number;
    lust: number;
    soul: number;
    primary_track: string;
    quadrant: string;
    labels: string[];
    tracks: Record<string, number>;
  }>
> {
  const results: Array<{
    card_b_id: string;
    harmony: number;
    lust: number;
    soul: number;
    primary_track: string;
    quadrant: string;
    labels: string[];
    tracks: Record<string, number>;
  }> = [];

  for (let i = 0; i < targets.length; i += concurrency) {
    const batch = targets.slice(i, i + concurrency);
    const settled = await Promise.allSettled(
      batch.map(async (t) => {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
        try {
          const res = await fetch(`${ASTRO}/quick-score`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_a: userA, user_b: t.flat }),
            signal: controller.signal,
          });
          if (!res.ok) return null;
          const data = await res.json();
          return { card_b_id: t.id, ...data };
        } finally {
          clearTimeout(timer);
        }
      })
    );
    for (const s of settled) {
      if (s.status === "fulfilled" && s.value) results.push(s.value);
    }
  }
  return results;
}

export async function GET(req: NextRequest) {
  // 1. Auth
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  // 2. Parse params
  const { searchParams } = new URL(req.url);
  const cardId = searchParams.get("card_id");
  const offset = parseInt(searchParams.get("offset") ?? "0", 10);
  const limit = Math.min(parseInt(searchParams.get("limit") ?? "20", 10), 50);

  if (!cardId)
    return NextResponse.json(
      { error: "card_id is required" },
      { status: 400 }
    );

  // 3. Verify card belongs to user + has natal_cache
  const { data: card } = await supabase
    .from("soul_cards")
    .select("id, natal_cache, owner_id")
    .eq("id", cardId)
    .maybeSingle();

  if (!card || card.owner_id !== user.id)
    return NextResponse.json(
      { error: "Card not found or not yours" },
      { status: 404 }
    );
  if (!card.natal_cache)
    return NextResponse.json(
      { error: "Card has no natal data" },
      { status: 400 }
    );

  // 4. Check ranking_cache freshness
  const service = createServiceClient();
  const cutoff = new Date(Date.now() - CACHE_TTL_MS).toISOString();

  const { count: freshCount } = await service
    .from("ranking_cache")
    .select("id", { count: "exact", head: true })
    .eq("card_a_id", cardId)
    .gte("computed_at", cutoff);

  // 5. If no fresh cache, do incremental compute
  if (!freshCount || freshCount === 0) {
    // Get all other yin cards with natal_cache
    const { data: otherCards } = await service
      .from("soul_cards")
      .select("id, natal_cache")
      .eq("yin_yang", "yin")
      .neq("owner_id", user.id)
      .not("natal_cache", "is", null);

    if (otherCards && otherCards.length > 0) {
      // Get existing fresh cache pairs to skip
      const { data: existingPairs } = await service
        .from("ranking_cache")
        .select("card_b_id")
        .eq("card_a_id", cardId)
        .gte("computed_at", cutoff);

      const existingSet = new Set(
        (existingPairs ?? []).map((p: { card_b_id: string }) => p.card_b_id)
      );

      const toCompute = otherCards
        .filter((c: { id: string }) => !existingSet.has(c.id))
        .map((c: { id: string; natal_cache: NatalCache }) => ({
          id: c.id,
          flat: flattenNatalCache(c.natal_cache),
        }));

      if (toCompute.length > 0) {
        const userAFlat = flattenNatalCache(card.natal_cache as NatalCache);
        const scored = await batchQuickScore(
          userAFlat,
          toCompute,
          CONCURRENCY
        );

        // UPSERT to ranking_cache
        if (scored.length > 0) {
          const rows = scored.map((s) => ({
            card_a_id: cardId,
            card_b_id: s.card_b_id,
            harmony: s.harmony,
            lust: s.lust,
            soul: s.soul,
            primary_track: s.primary_track,
            quadrant: s.quadrant ?? null,
            labels: s.labels ?? [],
            tracks: s.tracks ?? {},
            computed_at: new Date().toISOString(),
          }));

          await service.from("ranking_cache").upsert(rows, {
            onConflict: "card_a_id,card_b_id",
          });
        }
      }
    }
  }

  // 6. Return paginated results sorted by harmony DESC
  const { data: rankings, count: total } = await service
    .from("ranking_cache")
    .select("id, harmony, lust, soul, primary_track, quadrant, labels, tracks, computed_at", {
      count: "exact",
    })
    .eq("card_a_id", cardId)
    .order("harmony", { ascending: false })
    .range(offset, offset + limit - 1);

  const items = (rankings ?? []).map(
    (
      r: {
        id: string;
        harmony: number;
        lust: number;
        soul: number;
        primary_track: string;
        quadrant: string | null;
        labels: string[];
        tracks: Record<string, number>;
        computed_at: string;
      },
      i: number
    ) => ({
      cache_id: r.id,
      rank: offset + i + 1,
      harmony: r.harmony,
      lust: r.lust,
      soul: r.soul,
      primary_track: r.primary_track,
      quadrant: r.quadrant,
      labels: r.labels,
      tracks: r.tracks,
    })
  );

  const latestComputedAt =
    rankings && rankings.length > 0 ? rankings[0].computed_at : null;

  return NextResponse.json({
    rankings: items,
    total: total ?? 0,
    computed_at: latestComputedAt,
  });
}
