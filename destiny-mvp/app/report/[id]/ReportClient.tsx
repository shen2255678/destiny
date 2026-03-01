"use client";

import dynamic from "next/dynamic";
import { useState, useCallback } from "react";

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
  const [copied, setCopied] = useState(false);

  const copyLink = useCallback(() => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, []);
  const scoreItems = [
    { label: "綜合評分", value: harmonyScore, color: "#b86e7d", hint: "整體相容性總分，由費洛蒙與靈魂共鳴加權計算" },
    { label: "費洛蒙值", value: lustScore, color: "#d98695", hint: "生理吸引力與慾望張力——越高代表越有肉體化學反應" },
    { label: "靈魂共鳴", value: soulScore, color: "#a8e6cf", hint: "精神深度與靈魂契合度——越高代表越有宿命感與深層連結" },
    { label: "朋友軌", value: tracks.friend ?? 0, color: "#818cf8", hint: "思維默契與溝通共振——適合智識交流與創意合作的連結" },
    { label: "激情軌", value: tracks.passion ?? 0, color: "#f472b6", hint: "致命吸引力與慾望強度——高分是費洛蒙陷阱，也可能是危險荷爾蒙" },
    { label: "伴侶軌", value: tracks.partner ?? 0, color: "#34d399", hint: "日常生活互補與現實相處能力——越高越能走入長期穩定關係" },
  ];

  return (
    <>
      <div style={{ marginBottom: 28, display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#5c4059", letterSpacing: "0.08em", marginBottom: 6 }}>
            ✦ 命運解析報告
          </h1>
          <p style={{ color: "#8c7089", fontSize: 13 }}>
            {nameA} × {nameB}
          </p>
        </div>
        <button
          onClick={copyLink}
          title="複製報告連結"
          style={{
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: copied ? "rgba(52,211,153,0.15)" : "rgba(255,255,255,0.4)",
            border: copied ? "1px solid rgba(52,211,153,0.5)" : "1px solid rgba(255,255,255,0.6)",
            borderRadius: 999,
            padding: "7px 14px",
            fontSize: 12,
            fontWeight: 600,
            color: copied ? "#059669" : "#8c7089",
            cursor: "pointer",
            backdropFilter: "blur(8px)",
            transition: "all 0.2s",
          }}
        >
          {copied ? "✓ 已複製" : "⎘ 複製連結"}
        </button>
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
          {scoreItems.map(({ label, value, color, hint }) => (
            <div key={label} title={hint} style={{ cursor: "help", position: "relative" }}>
              <div style={{ fontSize: 10, color: "#8c7089", marginBottom: 4 }}>{label}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color }}>{Math.round(value)}</div>
              <div style={{ fontSize: 9, color: "#c4a0aa", marginTop: 3 }}>ℹ</div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 10, color: "#c4a0aa", textAlign: "center", marginTop: 12, marginBottom: 0 }}>
          將滑鼠移到數字上可查看說明
        </p>
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
