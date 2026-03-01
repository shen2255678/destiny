import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import { ReportClient } from "./ReportClient";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: match, error } = await supabase
    .from("mvp_matches")
    .select("*")
    .eq("id", id)
    .single();

  if (error || !match) {
    notFound();
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const r = ((match.report_json as any) ?? {}) as Record<string, unknown>;
  const tracks = (match.tracks as Record<string, number>) ?? {};
  const labels = (match.labels as string[]) ?? [];

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "32px 24px" }}>
      <ReportClient
        nameA={match.name_a ?? "A"}
        nameB={match.name_b ?? "B"}
        harmonyScore={match.harmony_score ?? 50}
        lustScore={match.lust_score ?? 50}
        soulScore={match.soul_score ?? 50}
        tracks={tracks}
        labels={labels}
        archetype={(r.archetype as string) ?? "神秘原型"}
        shadowTags={(r.shadow_tags as string[]) ?? []}
        toxicTraps={(r.toxic_traps as string[]) ?? []}
        reportText={(r.report_text as string) ?? ""}
      />
    </main>
  );
}
