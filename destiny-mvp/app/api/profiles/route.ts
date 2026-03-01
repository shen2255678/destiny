// destiny-mvp/app/api/profiles/route.ts
import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

const ASTRO = process.env.ASTRO_SERVICE_URL ?? "http://localhost:8001";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { data, error } = await supabase
    .from("soul_cards")
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, profile_card_data, ideal_match_data, created_at")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data ?? []);
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  // Free tier check
  const { count } = await supabase
    .from("soul_cards")
    .select("id", { count: "exact", head: true })
    .eq("owner_id", user.id);

  if ((count ?? 0) >= 1) {
    return NextResponse.json({ error: "upgrade_required" }, { status: 403 });
  }

  const body = await req.json() as {
    label: string;
    birth_date: string;
    birth_time?: string;
    lat: number;
    lng: number;
    data_tier: 1 | 2 | 3;
    gender: "M" | "F";
    yin_yang?: "yin" | "yang";
  };

  // Calculate chart (non-blocking on failure)
  let natal_cache: Record<string, unknown> | null = null;
  try {
    const chartRes = await fetch(`${ASTRO}/calculate-chart`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        birth_date: body.birth_date,
        birth_time_exact: body.birth_time || null,
        lat: body.lat,
        lng: body.lng,
        data_tier: body.data_tier,
      }),
    });
    if (chartRes.ok) natal_cache = await chartRes.json();
  } catch {
    // astro-service down — save profile without chart cache
  }

  const { data, error } = await supabase
    .from("soul_cards")
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
      natal_cache,
    })
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache")
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}
