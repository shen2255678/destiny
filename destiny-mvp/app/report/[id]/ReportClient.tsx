"use client";

import dynamic from "next/dynamic";
import { useState, useCallback } from "react";

const SIGN_ZH: Record<string, string> = {
  Aries: "牡羊座", Taurus: "金牛座", Gemini: "雙子座", Cancer: "巨蟹座",
  Leo: "獅子座", Virgo: "處女座", Libra: "天秤座", Scorpio: "天蠍座",
  Sagittarius: "射手座", Capricorn: "摩羯座", Aquarius: "水瓶座", Pisces: "雙魚座",
};
const ATT_ZH: Record<string, string> = {
  secure: "安全依戀型", anxious: "焦慮依戀型", avoidant: "迴避依戀型", fearful: "恐懼依戀型",
};
const BAZI_ZH: Record<string, string> = {
  Wood: "木", Fire: "火", Earth: "土", Metal: "金", Water: "水",
};
function zh(val: string | undefined, map: Record<string, string>): string {
  if (!val) return "—";
  return map[val] ?? val;
}

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

interface ChartData {
  [key: string]: string;
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
  chartA?: ChartData;
  chartB?: ChartData;
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
  chartA,
  chartB,
}: ReportClientProps) {
  const [copied, setCopied] = useState(false);
  const [chartOpen, setChartOpen] = useState(false);

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

      {/* Collapsible individual chart section */}
      <div style={{ marginTop: 28 }}>
        <button
          onClick={() => setChartOpen((v) => !v)}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "rgba(255,255,255,0.3)",
            border: "1px solid rgba(255,255,255,0.55)",
            borderRadius: chartOpen ? "16px 16px 0 0" : 16,
            padding: "12px 18px",
            fontSize: 13,
            fontWeight: 600,
            color: "#8c7089",
            cursor: "pointer",
            backdropFilter: "blur(8px)",
            transition: "border-radius 0.2s",
          }}
        >
          <span>✦ 查看完整命盤資料</span>
          <span style={{ fontSize: 16, transition: "transform 0.25s", display: "inline-block", transform: chartOpen ? "rotate(180deg)" : "rotate(0deg)" }}>
            ▾
          </span>
        </button>

        {chartOpen && (
          <div style={{
            background: "rgba(255,255,255,0.22)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255,255,255,0.45)",
            borderTop: "none",
            borderRadius: "0 0 16px 16px",
            padding: "16px 18px",
          }}>
            {(!chartA && !chartB) ? (
              <p style={{ fontSize: 11, color: "#c4a0aa", textAlign: "center", margin: 0 }}>
                重新跑一次匹配後可見（舊紀錄不含此資料）
              </p>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {[
                  { name: nameA, chart: chartA },
                  { name: nameB, chart: chartB },
                ].map(({ name, chart }) => (
                  <div key={name}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "#b86e7d", marginBottom: 8, letterSpacing: "0.05em" }}>
                      {name} 命盤
                    </div>
                    {chart ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                        {[
                          { label: "☀ 太陽", key: "sun_sign" },
                          { label: "☽ 月亮", key: "moon_sign" },
                          { label: "↑ 上升", key: "ascendant_sign" },
                          { label: "♀ 金星", key: "venus_sign" },
                          { label: "♂ 火星", key: "mars_sign" },
                          { label: "☿ 水星", key: "mercury_sign" },
                          { label: "♄ 土星", key: "saturn_sign" },
                        ].map(({ label, key }) => (
                          <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                            <span style={{ color: "#8c7089" }}>{label}</span>
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart[key], SIGN_ZH)}</span>
                          </div>
                        ))}
                        <div style={{ marginTop: 4, paddingTop: 4, borderTop: "1px solid rgba(180,130,150,0.15)", display: "flex", flexDirection: "column", gap: 5 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                            <span style={{ color: "#8c7089" }}>🔥 八字元素</span>
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart["bazi_element"], BAZI_ZH)}</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                            <span style={{ color: "#8c7089" }}>🧠 依戀類型</span>
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart["attachment_style"], ATT_ZH)}</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p style={{ fontSize: 11, color: "#c4a0aa", margin: 0 }}>資料不可用</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
