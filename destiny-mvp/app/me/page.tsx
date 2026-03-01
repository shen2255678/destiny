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
    const { data: allMatches } = await supabase
      .from("mvp_matches")
      .select("id, name_a, name_b, harmony_score, lust_score, soul_score, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(20);

    const nameLower = profile.display_name.toLowerCase();
    matches = (allMatches ?? []).filter(
      (m) =>
        m.name_a?.toLowerCase().includes(nameLower) ||
        m.name_b?.toLowerCase().includes(nameLower)
    );
  }

  return <MeClient profile={profile} matches={matches} />;
}
