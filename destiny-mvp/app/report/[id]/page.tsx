import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import { ReportClient } from "./ReportClient";
import { PromptPreviewPanel } from "@/components/PromptPreviewPanel";
import { translateShadowTag, translatePsychTrigger } from "@/lib/shadowTagsZh";

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

  // --- Field mapping: API uses different names than what TarotCard expects ---
  const quadrantMap: Record<string, string> = {
    soulmate: "靈魂伴侶",
    lover: "激情愛人",
    partner: "命定正緣",
    colleague: "靈魂知己",
  };
  const spicyMap: Record<string, string> = {
    HIGH_VOLTAGE: "⚡ 高壓電場",
    SOULMATE: "✦ 宿命羈絆",
    STABLE: "◎ 穩定共振",
    MODERATE: "◈ 溫和共鳴",
  };

  const quadrant = (r.quadrant as string) ?? "";
  const spiciness = (r.spiciness_level as string) ?? "";
  const archetype =
    [quadrantMap[quadrant], spicyMap[spiciness]].filter(Boolean).join(" · ") ||
    "神秘原型";

  // psychological_tags = shadow tags from shadow_engine — translate to Chinese sentences
  const shadowTags = ((r.psychological_tags as string[]) ?? []).map(translateShadowTag);

  // psychological_triggers = named dynamics — translate to Chinese
  const toxicTraps = ((r.psychological_triggers as string[]) ?? []).map(translatePsychTrigger);

  // resonance_badges = special badges like "命理雙重認證"
  const resonanceBadges = (r.resonance_badges as string[]) ?? [];

  // Build a report text from algorithm data (no LLM required)
  const primaryTrackMap: Record<string, string> = {
    friend: "朋友軌",
    passion: "激情軌",
    partner: "伴侶軌",
    soul: "靈魂軌",
  };
  const primaryTrack = (r.primary_track as string) ?? "";
  const karmicTension = r.karmic_tension as number | undefined;
  const highVoltage = r.high_voltage as boolean | undefined;

  const reportLines: string[] = [];
  if (primaryTrack)
    reportLines.push(
      `主要連結類型：${primaryTrackMap[primaryTrack] ?? primaryTrack}`
    );
  if (karmicTension !== undefined && karmicTension > 0)
    reportLines.push(`業力張力：${karmicTension.toFixed(1)}`);
  if (highVoltage) reportLines.push("⚡ 高壓警告：此組合觸發業力或陰影動態");
  if (resonanceBadges.length > 0)
    reportLines.push(`命理認證：${resonanceBadges.join("、")}`);
  if (toxicTraps.length > 0)
    reportLines.push(`心理觸發：${toxicTraps.join(" | ")}`);

  const reportText =
    reportLines.join("\n") || "演算法解析完成，啟用 LLM 模式可獲得深度報告。";

  const chartA = (r.user_a_chart as Record<string, unknown>) ?? undefined;
  const chartB = (r.user_b_chart as Record<string, unknown>) ?? undefined;

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
        archetype={archetype}
        shadowTags={shadowTags}
        toxicTraps={toxicTraps}
        reportText={reportText}
        chartA={Object.keys(chartA ?? {}).length > 0 ? chartA : undefined}
        chartB={Object.keys(chartB ?? {}).length > 0 ? chartB : undefined}
      />
      <PromptPreviewPanel
        reportJson={r}
        nameA={match.name_a ?? "A"}
        nameB={match.name_b ?? "B"}
      />
    </main>
  );
}
