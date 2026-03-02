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

  let body: {
    yin_yang?: "yin" | "yang";
    avatar_icon?: string;
    display_name?: string;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (body.yin_yang !== undefined && !["yin", "yang"].includes(body.yin_yang)) {
    return NextResponse.json({ error: "yin_yang must be 'yin' or 'yang'" }, { status: 400 });
  }
  if (body.avatar_icon !== undefined && (typeof body.avatar_icon !== "string" || body.avatar_icon.length < 1 || body.avatar_icon.length > 8)) {
    return NextResponse.json({ error: "avatar_icon must be a string ≤8 chars" }, { status: 400 });
  }
  if (body.display_name !== undefined && (typeof body.display_name !== "string" || body.display_name.length < 1 || body.display_name.length > 50)) {
    return NextResponse.json({ error: "display_name must be 1–50 chars" }, { status: 400 });
  }
  if (body.yin_yang === undefined && body.avatar_icon === undefined && body.display_name === undefined) {
    return NextResponse.json({ error: "At least one field required" }, { status: 400 });
  }
  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (body.yin_yang !== undefined)    updates.yin_yang = body.yin_yang;
  if (body.avatar_icon !== undefined) updates.avatar_icon = body.avatar_icon;
  if (body.display_name !== undefined) updates.display_name = body.display_name;

  const { data, error } = await supabase
    .from("soul_cards")
    .update(updates)
    .eq("id", id)
    .eq("owner_id", user.id)
    .select("id, yin_yang, avatar_icon, display_name")
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
