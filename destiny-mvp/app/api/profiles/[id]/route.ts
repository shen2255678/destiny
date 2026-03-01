// destiny-mvp/app/api/profiles/[id]/route.ts
import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  let body: { yin_yang?: "yin" | "yang" };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (body.yin_yang !== undefined && !["yin", "yang"].includes(body.yin_yang)) {
    return NextResponse.json({ error: "yin_yang must be 'yin' or 'yang'" }, { status: 400 });
  }

  if (body.yin_yang === undefined) {
    return NextResponse.json({ error: "At least one field (yin_yang) is required" }, { status: 400 });
  }
  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (body.yin_yang !== undefined) updates.yin_yang = body.yin_yang;

  const { data, error } = await supabase
    .from("soul_cards")
    .update(updates)
    .eq("id", id)
    .eq("owner_id", user.id)
    .select("id, yin_yang")
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json(data);
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { error } = await supabase
    .from("soul_cards")
    .delete()
    .eq("id", id)
    .eq("owner_id", user.id);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return new NextResponse(null, { status: 204 });
}
