import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { MeClient } from "./MeClient";

export default async function MePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profiles } = await supabase
    .from("soul_cards")
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, created_at")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false })
    .limit(1);

  const profile = profiles?.[0] ?? null;

  let matches: Array<{
    id: string;
    name_a: string | null;
    name_b: string | null;
    harmony_score: number | null;
    lust_score: number | null;
    soul_score: number | null;
    created_at: string;
  }> = [];

  if (profile) {
    // Strip PostgREST filter metacharacters from name to prevent filter injection
    const safeName = profile.display_name.replace(/[(),]/g, "");
    const { data: matchData } = await supabase
      .from("mvp_matches")
      .select("id, name_a, name_b, harmony_score, lust_score, soul_score, created_at")
      .eq("user_id", user.id)
      .or(`name_a.ilike.%${safeName}%,name_b.ilike.%${safeName}%`)
      .order("created_at", { ascending: false })
      .limit(20);
    matches = matchData ?? [];
  }

  return <MeClient profile={profile} matches={matches} />;
}
