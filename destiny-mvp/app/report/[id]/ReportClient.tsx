"use client";

import dynamic from "next/dynamic";

// Dynamic import avoids SSR issues with framer-motion
const TarotCard = dynamic(
  () => import("@/components/TarotCard").then((m) => m.TarotCard),
  { ssr: false }
);

interface TrackScores {
  friend?: number;
  passion?: number;
  partner?: number;
  soul?: number;
}

interface ReportClientProps {
  nameA: string;
  nameB: string;
  harmonyScore: number;
  lustScore: number;
  soulScore: number;
  tracks: TrackScores;
  labels: string[];
  archetype: string;
  shadowTags: string[];
  toxicTraps: string[];
  reportText: string;
}

export function ReportClient({
  nameA,
  nameB,
  harmonyScore,
  lustScore,
  soulScore,
  tracks,
  labels,
  archetype,
  shadowTags,
  toxicTraps,
  reportText,
}: ReportClientProps) {
  const scoreItems = [
    { label: "Harmony", value: harmonyScore, color: "#b86e7d" },
    { label: "VibeScore", value: lustScore, color: "#d98695" },
    { label: "ChemScore", value: soulScore, color: "#a8e6cf" },
    { label: "Friend", value: tracks.friend ?? 0, color: "#818cf8" },
    { label: "Passion", value: tracks.passion ?? 0, color: "#f472b6" },
    { label: "Partner", value: tracks.partner ?? 0, color: "#34d399" },
  ];

  return (
    <>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#5c4059", letterSpacing: "0.08em", marginBottom: 6 }}>
          ✦ 命運解析報告
        </h1>
        <p style={{ color: "#8c7089", fontSize: 13 }}>
          {nameA} × {nameB}
        </p>
      </div>

      {/* Score grid */}
      <div style={{
        background: "rgba(255,255,255,0.35)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)",
        borderRadius: 20,
        padding: "20px 24px",
        marginBottom: 32,
        boxShadow: "0 8px 32px rgba(217,134,149,0.1)",
      }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, textAlign: "center" }}>
          {scoreItems.map(({ label, value, color }) => (
            <div key={label}>
              <div style={{ fontSize: 10, color: "#8c7089", marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color }}>{Math.round(value)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Labels */}
      {labels.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
          {labels.map((tag) => (
            <span key={tag} style={{
              background: "rgba(217,134,149,0.12)",
              color: "#b86e7d",
              border: "1px solid rgba(217,134,149,0.3)",
              padding: "4px 12px",
              borderRadius: 999,
              fontSize: 12,
            }}>
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {/* 3D Tarot Card */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        <TarotCard
          front={{ archetype, resonance: labels.slice(0, 6), vibeScore: lustScore, chemScore: soulScore }}
          back={{ shadow: shadowTags, toxicTraps, reportText }}
        />
        <p style={{ color: "#8c7089", fontSize: 11 }}>點擊卡片翻面 → 查看陰暗面分析</p>
      </div>
    </>
  );
}
