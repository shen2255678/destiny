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
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, profile_card_data, ideal_match_data, avatar_icon, avatar_url, created_at")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data ?? []);
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

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
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body.label || body.label.length > 50 || !body.birth_date) {
    return NextResponse.json({ error: "label (1–50 chars) and birth_date are required" }, { status: 400 });
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(body.birth_date)) {
    return NextResponse.json({ error: "birth_date must be YYYY-MM-DD" }, { status: 400 });
  }
  if (!["M", "F"].includes(body.gender)) {
    return NextResponse.json({ error: "Invalid gender: must be M or F" }, { status: 400 });
  }
  if (!([1, 2, 3] as number[]).includes(body.data_tier)) {
    return NextResponse.json({ error: "Invalid data_tier: must be 1, 2, or 3" }, { status: 400 });
  }
  if (body.avatar_icon !== undefined && (typeof body.avatar_icon !== "string" || body.avatar_icon.length < 1 || body.avatar_icon.length > 8)) {
    return NextResponse.json({ error: "avatar_icon must be a string ≤8 chars" }, { status: 400 });
  }
  if (
    typeof body.lat !== "number" || body.lat < -90 || body.lat > 90 ||
    typeof body.lng !== "number" || body.lng < -180 || body.lng > 180
  ) {
    return NextResponse.json({ error: "Invalid lat/lng values" }, { status: 400 });
  }

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

  // Compute ZWDS chart and merge into natal_cache (Tier 1 + birth_time only, non-blocking)
  if (natal_cache !== null && body.data_tier === 1 && body.birth_time) {
    try {
      const [year, month, day] = body.birth_date.split("-").map(Number);
      const zwdsRes = await fetch(`${ASTRO}/compute-zwds-chart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          birth_year: year,
          birth_month: month,
          birth_day: day,
          birth_time: body.birth_time,
          gender: body.gender,
        }),
      });
      if (zwdsRes.ok) {
        const zwdsData = await zwdsRes.json();
        if (zwdsData.chart) {
          natal_cache = { ...natal_cache, zwds: zwdsData.chart };
        }
      }
    } catch {
      // zwds computation failed — keep natal_cache without zwds
    }
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
      avatar_icon: body.avatar_icon ?? "✦",
      natal_cache,
    })
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, avatar_icon")
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}
