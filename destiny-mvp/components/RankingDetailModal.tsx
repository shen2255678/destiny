"use client";

import React from "react";

const TRACK_ZH: Record<string, string> = {
  friend: "知心好友",
  passion: "熱情火花",
  partner: "穩定夥伴",
  soul: "靈魂伴侶",
};

const QUADRANT_ZH: Record<string, string> = {
  soulmate: "靈魂伴侶象限",
  lover: "命定雙生象限",
  partner: "正緣伴侶象限",
  colleague: "知心好友象限",
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

function TrackBar({
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
        gap: 10,
        marginBottom: 10,
      }}
    >
      <span
        style={{
          fontSize: 12,
          color: "#8c7089",
          width: 60,
          flexShrink: 0,
          textAlign: "right",
        }}
      >
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 8,
          borderRadius: 4,
          background: "rgba(0,0,0,0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(value, 100)}%`,
            height: "100%",
            borderRadius: 4,
            background: color,
            transition: "width 0.5s ease",
          }}
        />
      </div>
      <span
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "#5c4059",
          width: 28,
          textAlign: "right",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export function RankingDetailModal({
  item,
  onClose,
}: {
  item: RankingItem;
  onClose: () => void;
}) {
  const trackLabel = TRACK_ZH[item.primary_track] ?? item.primary_track;
  const quadrantLabel = item.quadrant
    ? QUADRANT_ZH[item.quadrant] ?? item.quadrant
    : null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          zIndex: 90,
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 100,
          width: "min(420px, 90vw)",
          background: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.7)",
          borderRadius: 24,
          padding: "32px 28px 24px",
          boxShadow: "0 8px 40px rgba(92,64,89,0.15)",
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: 12,
            right: 12,
            width: 32,
            height: 32,
            borderRadius: 8,
            border: "none",
            background: "transparent",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 20, color: "#8c7089" }}
          >
            close
          </span>
        </button>

        {/* Title */}
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 28, color: "#d98695", marginBottom: 4 }}
          >
            auto_awesome
          </span>
          <h2
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: "#5c4059",
              margin: "4px 0 0",
            }}
          >
            命運共振分析
          </h2>
        </div>

        {/* Harmony score */}
        <div style={{ textAlign: "center", marginBottom: 16 }}>
          <span
            style={{
              fontSize: 48,
              fontWeight: 800,
              color: "#5c4059",
              lineHeight: 1,
            }}
          >
            {item.harmony}
          </span>
          <span
            style={{
              fontSize: 14,
              color: "#8c7089",
              marginLeft: 4,
            }}
          >
            分
          </span>
          <div style={{ marginTop: 6 }}>
            <span
              style={{
                display: "inline-block",
                padding: "4px 14px",
                borderRadius: 999,
                fontSize: 13,
                fontWeight: 600,
                background: "rgba(184,110,125,0.12)",
                color: "#b86e7d",
                border: "1px solid rgba(184,110,125,0.25)",
              }}
            >
              {trackLabel}
            </span>
          </div>
        </div>

        {/* Quadrant */}
        {quadrantLabel && (
          <p
            style={{
              textAlign: "center",
              fontSize: 12,
              color: "#a08a9d",
              marginBottom: 16,
            }}
          >
            {quadrantLabel}
          </p>
        )}

        {/* Four-track bars */}
        <div style={{ marginBottom: 16 }}>
          <TrackBar
            label={TRACK_ZH.friend}
            value={item.tracks.friend ?? 0}
            color="#6bb8a0"
          />
          <TrackBar
            label={TRACK_ZH.passion}
            value={item.tracks.passion ?? 0}
            color="#e07888"
          />
          <TrackBar
            label={TRACK_ZH.partner}
            value={item.tracks.partner ?? 0}
            color="#d4a054"
          />
          <TrackBar
            label={TRACK_ZH.soul}
            value={item.tracks.soul ?? 0}
            color="#7c5c8a"
          />
        </div>

        {/* Labels */}
        {item.labels && item.labels.length > 0 && (
          <div style={{ textAlign: "center", marginBottom: 20 }}>
            <span style={{ fontSize: 12, color: "#8c7089" }}>
              {item.labels.join(" x ")}
            </span>
          </div>
        )}

        {/* View full report button (future: triggers /compute-enriched + YinYangCollision) */}
        <button
          onClick={() => {
            // TODO: trigger full /compute-enriched + animation → /report/[id]
            onClose();
          }}
          style={{
            width: "100%",
            padding: "12px 0",
            borderRadius: 14,
            border: "none",
            background: "linear-gradient(135deg, #d98695, #b86e7d)",
            color: "#fff",
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
            letterSpacing: "0.04em",
          }}
        >
          查看完整報告
        </button>
      </div>
    </>
  );
}
