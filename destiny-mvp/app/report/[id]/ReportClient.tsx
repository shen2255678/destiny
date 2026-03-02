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

const QUADRANT_LABEL: Record<string, string> = {
  soulmate:  "靈魂伴侶象限",
  lover:     "命定雙生象限",
  partner:   "正緣伴侶象限",
  colleague: "知心好友象限",
};

// Dynamic import avoids SSR issues with framer-motion
const TarotCard = dynamic(
  () => import("@/components/TarotCard").then((m) => m.TarotCard),
  { ssr: false }
);

/** Dual-axis quadrant plot — inline SVG, no deps */
function QuadrantPlot({ lust, soul }: { lust: number; soul: number }) {
  const W = 200, H = 200, PAD = 28;
  const inner = W - PAD * 2;

  const toX = (v: number) => PAD + (v / 100) * inner;
  const toY = (v: number) => PAD + ((100 - v) / 100) * inner;

  const dotX = toX(lust);
  const dotY = toY(soul);

  const labels = [
    { x: PAD + inner * 0.25, y: PAD + inner * 0.25, text: "正緣伴侶", color: "#3498db" },
    { x: PAD + inner * 0.75, y: PAD + inner * 0.25, text: "靈魂伴侶", color: "#9b59b6" },
    { x: PAD + inner * 0.25, y: PAD + inner * 0.75, text: "知心好友", color: "#7f8c8d" },
    { x: PAD + inner * 0.75, y: PAD + inner * 0.75, text: "命定雙生", color: "#e74c3c" },
  ];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: 220 }}>
      <rect x={PAD} y={PAD} width={inner} height={inner} fill="#1a0f1e" rx={4} />
      <line x1={W / 2} y1={PAD} x2={W / 2} y2={W - PAD} stroke="#5c4059" strokeWidth={1} strokeDasharray="3,3" />
      <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="#5c4059" strokeWidth={1} strokeDasharray="3,3" />
      {labels.map((l, i) => (
        <text key={i} x={l.x} y={l.y} textAnchor="middle" dominantBaseline="middle"
          fontSize={8} fill={l.color} opacity={0.6} fontFamily="sans-serif">
          {l.text}
        </text>
      ))}
      <line x1={PAD} y1={W - PAD} x2={W - PAD} y2={W - PAD} stroke="#8c7089" strokeWidth={1} />
      <line x1={PAD} y1={PAD} x2={PAD} y2={W - PAD} stroke="#8c7089" strokeWidth={1} />
      <text x={W / 2} y={W - 6} textAnchor="middle" fontSize={8} fill="#8c7089" fontFamily="sans-serif">肉體費洛蒙</text>
      <text x={8} y={H / 2} textAnchor="middle" fontSize={8} fill="#8c7089" fontFamily="sans-serif"
        transform={`rotate(-90, 8, ${H / 2})`}>靈魂共鳴</text>
      <circle cx={dotX} cy={dotY} r={7} fill="#c084fc" opacity={0.9} />
      <circle cx={dotX} cy={dotY} r={7} fill="none" stroke="#e9d5ff" strokeWidth={1.5} />
    </svg>
  );
}

/** Horizontal track bars replacing raw track numbers */
function TrackBars({ tracks }: { tracks: Record<string, number> }) {
  const items = [
    { key: "friend",  label: "朋友緣",    color: "#60a5fa" },
    { key: "passion", label: "激情張力",   color: "#f87171" },
    { key: "partner", label: "正緣伴侶",   color: "#a78bfa" },
    { key: "soul",    label: "業力靈魂",   color: "#34d399" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, width: "100%" }}>
      {items.map(({ key, label, color }) => {
        const val = Math.round(tracks[key] ?? 0);
        return (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "#8c7089", width: 52, flexShrink: 0 }}>{label}</span>
            <div style={{ flex: 1, height: 6, background: "#2d1f35", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: 3,
                transition: "width 0.6s ease" }} />
            </div>
            <span style={{ fontSize: 10, color: "#c084fc", width: 24, textAlign: "right" }}>{val}</span>
          </div>
        );
      })}
    </div>
  );
}

interface TrackScores {
  friend?: number;
  passion?: number;
  partner?: number;
  soul?: number;
}

interface ChartData {
  [key: string]: unknown;
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
  quadrant?: string;
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
  quadrant,
}: ReportClientProps) {
  const [copied, setCopied] = useState(false);
  const [chartOpen, setChartOpen] = useState(false);
  const [savingSlot, setSavingSlot] = useState<null | "A" | "B">(null);
  const [saveLabel, setSaveLabel] = useState("");
  const [saveMsg, setSaveMsg] = useState("");

  async function saveProfile(slot: "A" | "B") {
    const chart = slot === "A" ? chartA : chartB;
    const name = slot === "A" ? nameA : nameB;
    if (!chart) {
      setSaveMsg("❌ 無命盤資料（請重新跑一次匹配）");
      setSavingSlot(null);
      return;
    }
    setSaveMsg("儲存中...");
    const res = await fetch("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        label: saveLabel || name,
        birth_date: (chart["birth_date"] as string) ?? "1990-01-01",
        birth_time: (chart["birth_time_exact"] as string) ?? undefined,
        lat: (chart["lat"] as number) ?? 25.033,
        lng: (chart["lng"] as number) ?? 121.565,
        data_tier: (chart["data_tier"] as number) ?? 3,
        gender: (chart["gender"] as string) ?? "M",
      }),
    });
    if (res.status === 403) {
      setSaveMsg("❌ 免費方案限 1 張命盤，升級解鎖更多");
      setSavingSlot(null);
      return;
    }
    if (!res.ok) {
      setSaveMsg("❌ 儲存失敗");
      setSavingSlot(null);
      return;
    }
    setSaveMsg("✓ 已儲存到我的命盤");
    setSavingSlot(null);
    setSaveLabel("");
    setTimeout(() => setSaveMsg(""), 4000);
  }

  const copyLink = useCallback(() => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, []);

  // Normalised tracks for TrackBars (needs Record<string, number>)
  const tracksNorm: Record<string, number> = {
    friend:  tracks.friend  ?? 0,
    passion: tracks.passion ?? 0,
    partner: tracks.partner ?? 0,
    soul:    tracks.soul    ?? 0,
  };

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

      {/* Quadrant + Track Bars card */}
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
        <div style={{ display: "flex", gap: 24, alignItems: "flex-start", flexWrap: "wrap" }}>
          {/* Quadrant plot */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10, flexShrink: 0 }}>
            <QuadrantPlot lust={lustScore} soul={soulScore} />
            <div style={{ fontSize: 11, color: "#8c7089", textAlign: "center" }}>
              綜合契合指數{" "}
              <span style={{ color: "#c084fc", fontWeight: 700 }}>{Math.round(harmonyScore)}</span>
              {quadrant && QUADRANT_LABEL[quadrant] ? (
                <>
                  {" · "}
                  <span style={{ color: "#e9d5ff" }}>{QUADRANT_LABEL[quadrant]}</span>
                </>
              ) : null}
            </div>
          </div>

          {/* Track bars */}
          <div style={{ flex: 1, minWidth: 180, display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <div style={{ fontSize: 11, color: "#8c7089", marginBottom: 10, fontWeight: 600, letterSpacing: "0.05em" }}>
              四軌共振分析
            </div>
            <TrackBars tracks={tracksNorm} />
          </div>
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
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart[key] as string, SIGN_ZH)}</span>
                          </div>
                        ))}
                        <div style={{ marginTop: 4, paddingTop: 4, borderTop: "1px solid rgba(180,130,150,0.15)", display: "flex", flexDirection: "column", gap: 5 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                            <span style={{ color: "#8c7089" }}>🔥 八字元素</span>
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart["bazi_element"] as string, BAZI_ZH)}</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                            <span style={{ color: "#8c7089" }}>🧠 依戀類型</span>
                            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(chart["attachment_style"] as string, ATT_ZH)}</span>
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

      {/* Save profile buttons */}
      <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 10 }}>
        {savingSlot ? (
          <div style={{
            background: "rgba(255,255,255,0.35)", backdropFilter: "blur(12px)",
            border: "1px solid rgba(255,255,255,0.6)", borderRadius: 16, padding: "16px 20px",
          }}>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 10 }}>
              儲存 {savingSlot === "A" ? nameA : nameB} 的命盤：
            </p>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={saveLabel}
                onChange={(e) => setSaveLabel(e.target.value)}
                placeholder={savingSlot === "A" ? nameA : nameB}
                style={{
                  flex: 1, padding: "7px 12px", borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.5)",
                  fontSize: 12, color: "#5c4059",
                }}
              />
              <button
                onClick={() => saveProfile(savingSlot)}
                style={{ padding: "7px 18px", borderRadius: 10, background: "#d98695", color: "#fff", border: "none", fontSize: 12, cursor: "pointer" }}
              >
                確認
              </button>
              <button
                onClick={() => { setSavingSlot(null); setSaveLabel(""); setSaveMsg(""); }}
                style={{ padding: "7px 12px", borderRadius: 10, border: "1px solid rgba(200,160,170,0.4)", background: "transparent", fontSize: 12, color: "#8c7089", cursor: "pointer" }}
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={() => { setSavingSlot("A"); setSaveLabel(""); setSaveMsg(""); }}
              style={{ flex: 1, padding: "10px", borderRadius: 12, background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.6)", fontSize: 12, color: "#8c7089", cursor: "pointer", backdropFilter: "blur(8px)" }}
            >
              💾 儲存 {nameA} 的命盤
            </button>
            <button
              onClick={() => { setSavingSlot("B"); setSaveLabel(""); setSaveMsg(""); }}
              style={{ flex: 1, padding: "10px", borderRadius: 12, background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.6)", fontSize: 12, color: "#8c7089", cursor: "pointer", backdropFilter: "blur(8px)" }}
            >
              💾 儲存 {nameB} 的命盤
            </button>
          </div>
        )}
        {saveMsg && (
          <p style={{ fontSize: 12, color: saveMsg.startsWith("✓") ? "#34d399" : "#c0392b", textAlign: "center" }}>
            {saveMsg}
          </p>
        )}
      </div>
    </>
  );
}
