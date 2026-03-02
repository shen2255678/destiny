import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { RankingClient } from "./RankingClient";

export default async function RankingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  // Fetch user's 命緣模式 (yin) cards for ranking
  // yin_yang='yin' means the user has opted into ranking (命緣模式)
  const { data: yinCards } = await supabase
    .from("soul_cards")
    .select("id, display_name, natal_cache")
    .eq("owner_id", user.id)
    .eq("yin_yang", "yin")
    .not("natal_cache", "is", null)
    .order("created_at", { ascending: false });

  return <RankingClient yinCards={yinCards ?? []} />;
}
