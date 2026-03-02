"use client";

import React from "react";

const TRACK_ZH: Record<string, string> = {
  friend: "知心好友",
  passion: "熱情火花",
  partner: "穩定夥伴",
  soul: "靈魂伴侶",
};

interface RankingItem {
  cache_id: string;
  rank: number;
  harmony: number;
  lust: number;
  soul: number;
  primary_track: string;
  quadrant: string | null;
  labels: string[];
  tracks: Record<string, number>;
}

const glassCard: React.CSSProperties = {
  background: "rgba(255,255,255,0.3)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.6)",
  borderRadius: 20,
  padding: "16px 20px",
  marginBottom: 12,
  cursor: "pointer",
  transition: "transform 0.15s, box-shadow 0.15s",
};

const pill = (color: string): React.CSSProperties => ({
  display: "inline-block",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 11,
  background: `${color}18`,
  color,
  border: `1px solid ${color}44`,
  margin: "2px 3px 2px 0",
});

function ProgressBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginTop: 4,
      }}
    >
      <span style={{ fontSize: 11, color: "#8c7089", width: 32, flexShrink: 0 }}>
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 6,
          borderRadius: 3,
          background: "rgba(0,0,0,0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(value, 100)}%`,
            height: "100%",
            borderRadius: 3,
            background: color,
            transition: "width 0.4s ease",
          }}
        />
      </div>
      <span style={{ fontSize: 11, color: "#8c7089", width: 24, textAlign: "right" }}>
        {value}
      </span>
    </div>
  );
}

export function RankingCard({
  item,
  onClick,
}: {
  item: RankingItem;
  onClick: () => void;
}) {
  const trackLabel = TRACK_ZH[item.primary_track] ?? item.primary_track;
  const labels = (item.labels ?? []).slice(0, 2);

  return (
    <div
      style={glassCard}
      onClick={onClick}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow =
          "0 4px 20px rgba(217,134,149,0.15)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {/* Top row: rank + harmony + track label */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: "#b86e7d",
            minWidth: 28,
          }}
        >
          #{item.rank}
        </span>
        <span
          style={{
            fontSize: 24,
            fontWeight: 800,
            color: "#5c4059",
          }}
        >
          {item.harmony}
        </span>
        <span style={{ fontSize: 11, color: "#8c7089", marginTop: 4 }}>分</span>
        <span style={{ ...pill("#b86e7d"), marginLeft: "auto" }}>
          {trackLabel}
        </span>
      </div>

      {/* Labels */}
      {labels.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          {labels.map((l, i) => (
            <span key={i} style={pill("#7c5c8a")}>
              {l}
            </span>
          ))}
        </div>
      )}

      {/* Progress bars */}
      <ProgressBar label="磁場" value={item.lust} color="#e07888" />
      <ProgressBar label="靈魂" value={item.soul} color="#7c5c8a" />
    </div>
  );
}
