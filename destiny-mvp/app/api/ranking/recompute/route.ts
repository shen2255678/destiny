import { createClient } from "@/lib/supabase/server";
import { createServiceClient } from "@/lib/supabase/service";
import { NextRequest, NextResponse } from "next/server";

const ASTRO = process.env.ASTRO_SERVICE_URL ?? "http://localhost:8001";
const CONCURRENCY = 5;
const FETCH_TIMEOUT_MS = 5000;
const RECOMPUTE_COOLDOWN_MS = 60 * 60 * 1000; // 1 hour

interface NatalCache {
  western_chart?: Record<string, unknown>;
  bazi_chart?: Record<string, unknown>;
}

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
  flat.rpv_conflict = "argue";
  flat.rpv_power = "follow";
  flat.rpv_energy = "home";
  return flat;
}

export async function POST(req: NextRequest) {
  // 1. Auth
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user)
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  // 2. Parse body
  let body: { card_id: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body.card_id)
    return NextResponse.json(
      { error: "card_id is required" },
      { status: 400 }
    );

  // 3. Verify card belongs to user
  const { data: card } = await supabase
    .from("soul_cards")
    .select("id, natal_cache, owner_id")
    .eq("id", body.card_id)
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

  // 4. Rate limit: reject if last recompute was within the cooldown window
  const service = createServiceClient();
  const cooldownCutoff = new Date(Date.now() - RECOMPUTE_COOLDOWN_MS).toISOString();
  const { count: recentCount } = await service
    .from("ranking_cache")
    .select("id", { count: "exact", head: true })
    .eq("card_a_id", body.card_id)
    .gte("computed_at", cooldownCutoff);

  if (recentCount && recentCount > 0) {
    return NextResponse.json(
      { error: "Recompute on cooldown. Try again in 1 hour." },
      { status: 429 }
    );
  }

  // 5. Delete old cache for this card
  await service.from("ranking_cache").delete().eq("card_a_id", body.card_id);

  // 6. Get all other yin cards with natal_cache
  const { data: otherCards } = await service
    .from("soul_cards")
    .select("id, natal_cache")
    .eq("yin_yang", "yin")
    .neq("owner_id", user.id)
    .not("natal_cache", "is", null);

  if (!otherCards || otherCards.length === 0) {
    return NextResponse.json({ status: "ok", computed: 0 });
  }

  // 7. Batch compute
  const userAFlat = flattenNatalCache(card.natal_cache as NatalCache);
  const targets = otherCards.map(
    (c: { id: string; natal_cache: NatalCache }) => ({
      id: c.id,
      flat: flattenNatalCache(c.natal_cache),
    })
  );

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

  for (let i = 0; i < targets.length; i += CONCURRENCY) {
    const batch = targets.slice(i, i + CONCURRENCY);
    const settled = await Promise.allSettled(
      batch.map(async (t: { id: string; flat: Record<string, unknown> }) => {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
        try {
          const res = await fetch(`${ASTRO}/quick-score`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_a: userAFlat, user_b: t.flat }),
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

  // 8. Insert results
  if (results.length > 0) {
    const rows = results.map((s) => ({
      card_a_id: body.card_id,
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

  return NextResponse.json({ status: "ok", computed: results.length });
}
