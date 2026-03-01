"use client";

import React, { useState } from "react";
import Link from "next/link";
import { translateShadowTag } from "@/lib/shadowTagsZh";

// ── Translation maps ──────────────────────────────────────────────────────────

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
  fire: "火", water: "水", wood: "木", metal: "金", earth: "土",
};
const ELEMENT_ZH: Record<string, string> = {
  Fire: "火", Water: "水", Wood: "木", Metal: "金", Earth: "土",
};
const ATT_DOM_ZH: Record<string, string> = {
  strong: "強勢", weak: "弱勢", balanced: "均衡",
};
const ZWDS_PALACE_ZH: Record<string, string> = {
  ming: "命宮", spouse: "夫妻宮", karma: "福德宮", wealth: "財帛宮",
  career: "官祿宮", health: "疾厄宮", travel: "遷移宮", friends: "交友宮",
  children: "子女宮", property: "田宅宮", siblings: "兄弟宮", parent: "父母宮",
};
const KARMIC_TAG_ZH: Record<string, string> = {
  Karmic_Love_Venus_Rx: "金星逆行：不配被愛的業力課題",
  Suppressed_Anger_Mars_Rx: "火星逆行：壓抑的怒火",
  Internal_Dialogue_Mercury_Rx: "水星逆行：深邃但難以言說的內心",
  Karmic_Crisis_SUN: "太陽業力危機度數",
  Karmic_Crisis_MOON: "月亮業力危機度數",
  Karmic_Crisis_VENUS: "金星業力危機度數",
  Karmic_Crisis_MARS: "火星業力危機度數",
  Karmic_Crisis_MERCURY: "水星業力危機度數",
  Blind_Impulse_MARS: "火星盲衝——行動前易失控",
  Blind_Impulse_SUN: "太陽盲衝——自我表達有時無法自制",
};

function zh(val: string | undefined | null, map: Record<string, string>): string {
  if (!val) return "—";
  return map[val] ?? val;
}

function translateKarmicTag(tag: string): string {
  if (KARMIC_TAG_ZH[tag]) return KARMIC_TAG_ZH[tag];
  // Axis_Sign_Cancer_Cap → "巨蟹-摩羯 業力軸線"
  if (tag.startsWith("Axis_Sign_")) {
    const parts = tag.replace("Axis_Sign_", "").split("_");
    return parts.map((p) => SIGN_ZH[p] ?? p).join("-") + " 業力軸線";
  }
  // North_Node_House_5 → "北交點在第5宮"
  if (tag.startsWith("North_Node_House_")) {
    return `北交點在第${tag.replace("North_Node_House_", "")}宮`;
  }
  // North_Node_Sign_Scorpio → "北交點在天蠍座"
  if (tag.startsWith("North_Node_Sign_")) {
    const sign = tag.replace("North_Node_Sign_", "");
    return `北交點在${SIGN_ZH[sign] ?? sign}`;
  }
  // Axis_House_1_7 → "第1-7宮業力軸線"
  if (tag.startsWith("Axis_House_")) {
    const parts = tag.replace("Axis_House_", "").split("_");
    return `第${parts[0]}-${parts[1]}宮業力軸線`;
  }
  return tag;
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface Profile {
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
  lat: number | null;
  lng: number | null;
  data_tier: number;
  gender: string;
  yin_yang: string;
  natal_cache: Record<string, unknown> | null;
}

interface Match {
  id: string;
  name_a: string | null;
  name_b: string | null;
  harmony_score: number | null;
  lust_score: number | null;
  soul_score: number | null;
  created_at: string;
}

// ── Shared styles ─────────────────────────────────────────────────────────────

const glassCard: React.CSSProperties = {
  background: "rgba(255,255,255,0.3)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.6)",
  borderRadius: 20,
  padding: "20px 24px",
  marginBottom: 24,
};

const sectionTitle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  color: "#b86e7d",
  marginBottom: 12,
  letterSpacing: "0.06em",
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

// ── Main component ────────────────────────────────────────────────────────────

export function MeClient({
  profile,
  matches,
}: {
  profile: Profile | null;
  matches: Match[];
}) {
  const [yinYang, setYinYang] = useState<"yin" | "yang">(
    (profile?.yin_yang as "yin" | "yang") ?? "yang"
  );
  const [rawOpen, setRawOpen] = useState(false);

  const c = (profile?.natal_cache ?? {}) as Record<string, unknown>;

  async function toggleYinYang(val: "yin" | "yang") {
    const prev = yinYang;
    setYinYang(val);
    if (profile) {
      const res = await fetch(`/api/profiles/${profile.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yin_yang: val }),
      });
      if (!res.ok) setYinYang(prev);
    }
  }

  if (!profile) {
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: "48px 24px", textAlign: "center" }}>
        <p style={{ color: "#8c7089", fontSize: 14, marginBottom: 24 }}>
          你還沒有儲存任何命盤卡。
        </p>
        <Link
          href="/lounge"
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            color: "#fff",
            padding: "10px 28px",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 600,
            textDecoration: "none",
          }}
        >
          ✦ 前往命運大廳
        </Link>
      </main>
    );
  }

  const isYin = yinYang === "yin";

  // Extract nested structures
  const bazi = (c.bazi ?? {}) as Record<string, unknown>;
  const fourPillars = (bazi.four_pillars ?? {}) as Record<string, string>;
  const elementProfile = (c.element_profile ?? {}) as Record<string, unknown>;
  const dominant = (elementProfile.dominant ?? []) as string[];
  const deficiency = (elementProfile.deficiency ?? []) as string[];
  const smTags = (c.sm_tags ?? []) as string[];
  const karmicTags = (c.karmic_tags ?? []) as string[];
  const zwds = c.zwds as {
    palaces: Record<string, { main_stars: string[]; malevolent_stars: string[]; is_empty: boolean }>;
    body_palace_name?: string;
    five_element?: string;
    four_transforms?: { hua_lu?: string; hua_quan?: string; hua_ke?: string; hua_ji?: string };
  } | undefined;
  const palaces = zwds?.palaces ?? {};

  // Retrograde planets
  const rxPlanets: string[] = [];
  if (c.mercury_rx) rxPlanets.push("☿ 水星逆行");
  if (c.venus_rx) rxPlanets.push("♀ 金星逆行");
  if (c.mars_rx) rxPlanets.push("♂ 火星逆行");

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#5c4059", letterSpacing: "0.08em", marginBottom: 4 }}>
          ✦ 我的命盤
        </h1>
        <p style={{ color: "#8c7089", fontSize: 13 }}>{profile.display_name} · Tier {profile.data_tier}</p>
      </div>

      {/* Yin-Yang toggle */}
      <div style={{
        background: "rgba(255,255,255,0.3)", backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)", borderRadius: 20,
        padding: "20px 24px", marginBottom: 24,
        display: "flex", alignItems: "center", gap: "20px",
      }}>
        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
          {isYin ? (
            <>
              <path d="M30 5 A25 25 0 0 0 30 55 A25 25 0 0 1 30 5 Z" fill="#5c4059" opacity="0.8" />
              <path d="M30 5 A25 25 0 0 1 30 55 A25 25 0 0 0 30 5 Z" fill="#f4e0e8" opacity="0.5" />
            </>
          ) : (
            <>
              <path d="M30 5 A25 25 0 0 1 30 55 A25 25 0 0 0 30 5 Z" fill="#f4d5be" opacity="0.8" />
              <path d="M30 5 A25 25 0 0 0 30 55 A25 25 0 0 1 30 5 Z" fill="#f4e0e8" opacity="0.4" />
            </>
          )}
        </svg>
        <div>
          <p style={{ fontSize: 11, color: "#8c7089", marginBottom: 8 }}>你的命盤極性</p>
          <div style={{ display: "flex", gap: 8 }}>
            {(["yin", "yang"] as const).map((v) => (
              <button
                key={v}
                onClick={() => toggleYinYang(v)}
                style={{
                  padding: "6px 16px", borderRadius: 999, fontSize: 12, cursor: "pointer",
                  fontWeight: yinYang === v ? 700 : 400,
                  background: yinYang === v ? "rgba(217,134,149,0.2)" : "rgba(255,255,255,0.4)",
                  border: yinYang === v ? "1px solid rgba(217,134,149,0.5)" : "1px solid rgba(255,255,255,0.6)",
                  color: yinYang === v ? "#b86e7d" : "#8c7089",
                  transition: "all 0.2s",
                }}
              >
                {v === "yin" ? "☽ 陰" : "☀ 陽"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Planet grid — expanded */}
      <div style={glassCard}>
        <p style={sectionTitle}>✦ 行星速覽</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" }}>
          {[
            { label: "☀ 太陽", key: "sun_sign" },
            { label: "☽ 月亮", key: "moon_sign" },
            { label: "↑ 上升", key: "ascendant_sign" },
            { label: "↓ 下降", key: "house7_sign" },
            { label: "♀ 金星", key: "venus_sign" },
            { label: "♂ 火星", key: "mars_sign" },
            { label: "☿ 水星", key: "mercury_sign" },
            { label: "♃ 木星", key: "jupiter_sign" },
            { label: "♄ 土星", key: "saturn_sign" },
            { label: "☊ 北交點", key: "north_node_sign" },
            { label: "⚷ 凱龍", key: "chiron_sign" },
            { label: "⚵ 婚神星", key: "juno_sign" },
            ...(profile.data_tier === 1 ? [
              { label: "⚸ 莉莉絲", key: "lilith_sign" },
              { label: "🔮 命運點", key: "vertex_sign" },
            ] : []),
          ].map(({ label, key }) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
              <span style={{ color: "#8c7089" }}>{label}</span>
              <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c[key] as string, SIGN_ZH)}</span>
            </div>
          ))}
        </div>

        {/* Retrograde */}
        {rxPlanets.length > 0 && (
          <div style={{ marginTop: 10, paddingTop: 8, borderTop: "1px solid rgba(180,130,150,0.15)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
              <span style={{ color: "#8c7089" }}>逆行</span>
              <span style={{ color: "#b86e7d", fontWeight: 600 }}>{rxPlanets.join("  ")}</span>
            </div>
          </div>
        )}

        {/* Base info */}
        <div style={{ marginTop: 10, paddingTop: 8, borderTop: "1px solid rgba(180,130,150,0.15)", display: "flex", flexDirection: "column", gap: 5 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
            <span style={{ color: "#8c7089" }}>🔥 八字主元素</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c.bazi_element as string, BAZI_ZH)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
            <span style={{ color: "#8c7089" }}>🧠 依戀類型</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c.attachment_style as string, ATT_ZH)}</span>
          </div>
          {c.emotional_capacity !== undefined && (
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
              <span style={{ color: "#8c7089" }}>💗 情緒容量</span>
              <span style={{ color: "#5c4059", fontWeight: 600 }}>{String(c.emotional_capacity)} / 100</span>
            </div>
          )}
        </div>
      </div>

      {/* BaZi section */}
      {!!(fourPillars.year || bazi.day_master_element) && (
        <div style={glassCard}>
          <p style={sectionTitle}>🔥 八字四柱</p>
          {fourPillars.year && (
            <div style={{ display: "flex", gap: 8, marginBottom: 12, justifyContent: "center" }}>
              {["year", "month", "day", "hour"].map((p) => (
                <div key={p} style={{
                  flex: 1, textAlign: "center",
                  background: "rgba(255,255,255,0.4)", borderRadius: 10,
                  padding: "8px 4px", border: "1px solid rgba(255,255,255,0.6)",
                }}>
                  <div style={{ fontSize: 10, color: "#c4a0aa", marginBottom: 4 }}>
                    {p === "year" ? "年" : p === "month" ? "月" : p === "day" ? "日" : "時"}
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#5c4059" }}>
                    {(fourPillars[p] as string) || "—"}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {!!bazi.day_master && (
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#8c7089" }}>日主</span>
                <span style={{ color: "#5c4059", fontWeight: 600 }}>
                  {bazi.day_master as string} ({zh(bazi.day_master_element as string, BAZI_ZH)})
                  {bazi.day_master_strength ? ` · ${zh(bazi.day_master_strength as string, ATT_DOM_ZH)}` : ""}
                </span>
              </div>
            )}
            {dominant.length > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#8c7089" }}>五行強勢</span>
                <span style={{ color: "#d97706", fontWeight: 600 }}>
                  {dominant.map((e) => ELEMENT_ZH[e] ?? e).join("、")}
                </span>
              </div>
            )}
            {deficiency.length > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: "#8c7089" }}>五行缺乏</span>
                <span style={{ color: "#7c3aed", fontWeight: 600 }}>
                  {deficiency.map((e) => ELEMENT_ZH[e] ?? e).join("、")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ZWDS section */}
      {zwds && (
        <div style={glassCard}>
          <p style={sectionTitle}>✦ 紫微斗數</p>
          {zwds.five_element && (
            <p style={{ fontSize: 11, color: "#8c7089", marginBottom: 10 }}>
              {zwds.five_element}
              {zwds.body_palace_name ? ` · 身宮：${zwds.body_palace_name}` : ""}
              {zwds.four_transforms ? ` · 化祿：${zwds.four_transforms.hua_lu ?? "—"} 化忌：${zwds.four_transforms.hua_ji ?? "—"}` : ""}
            </p>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {["ming", "spouse", "karma", "wealth", "career"].map((key) => {
              const palace = palaces[key];
              if (!palace) return null;
              const stars = palace.main_stars ?? [];
              const bad = palace.malevolent_stars ?? [];
              return (
                <div key={key} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                  fontSize: 11, paddingBottom: 6, borderBottom: "1px solid rgba(180,130,150,0.1)",
                }}>
                  <span style={{ color: "#8c7089", minWidth: 60 }}>{ZWDS_PALACE_ZH[key] ?? key}</span>
                  <span style={{ color: "#5c4059", fontWeight: 600, flex: 1, textAlign: "right" }}>
                    {stars.length > 0 ? stars.join("、") : "空宮"}
                    {bad.length > 0 ? <span style={{ color: "#b86e7d", fontWeight: 400 }}> · {bad.join(" ")}</span> : null}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Psychology section */}
      {(smTags.length > 0 || karmicTags.length > 0) && (
        <div style={glassCard}>
          <p style={sectionTitle}>🧬 靈魂分析</p>
          {smTags.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 10, color: "#c4a0aa", marginBottom: 6 }}>權力動態</p>
              <div>
                {smTags.map((tag) => (
                  <span key={tag} style={pill("#b86e7d")} title={tag}>
                    {translateShadowTag(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}
          {karmicTags.length > 0 && (
            <div>
              <p style={{ fontSize: 10, color: "#c4a0aa", marginBottom: 6 }}>業力標籤</p>
              <div>
                {karmicTags.map((tag) => (
                  <span key={tag} style={pill("#7c3aed")} title={tag}>
                    {translateKarmicTag(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw data preview (collapsible) */}
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => setRawOpen((v) => !v)}
          style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.55)",
            borderRadius: rawOpen ? "16px 16px 0 0" : 16, padding: "12px 18px",
            fontSize: 13, fontWeight: 600, color: "#8c7089", cursor: "pointer",
            backdropFilter: "blur(8px)",
          }}
        >
          <span>🔍 命盤原始資料</span>
          <span style={{ transform: rawOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block", transition: "transform 0.25s" }}>▾</span>
        </button>
        {rawOpen && (
          <div style={{
            background: "rgba(0,0,0,0.04)", border: "1px solid rgba(255,255,255,0.45)",
            borderTop: "none", borderRadius: "0 0 16px 16px", padding: "16px 18px",
            maxHeight: 320, overflowY: "auto",
          }}>
            <pre style={{ fontSize: 10, color: "#5c4059", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0 }}>
              {JSON.stringify(c, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Match history */}
      <div>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 12 }}>
          ✦ 合盤記錄（連連看）
        </p>
        {matches.length === 0 ? (
          <p style={{ fontSize: 12, color: "#c4a0aa" }}>
            還沒有合盤記錄，{" "}
            <Link href="/lounge" style={{ color: "#d98695" }}>去解析命運</Link>
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {matches.map((m) => {
              const nameLower = profile.display_name.toLowerCase();
              const other = m.name_a?.toLowerCase().includes(nameLower) ? m.name_b : m.name_a;
              return (
                <Link
                  key={m.id}
                  href={`/report/${m.id}`}
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.55)",
                    borderRadius: 14, padding: "12px 16px", textDecoration: "none",
                    backdropFilter: "blur(8px)", transition: "all 0.2s",
                  }}
                >
                  <div>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#5c4059" }}>
                      {profile.display_name} × {other ?? "？"}
                    </span>
                    <span style={{ fontSize: 10, color: "#c4a0aa", marginLeft: 8 }}>
                      {new Date(m.created_at).toLocaleDateString("zh-TW")}
                    </span>
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 700, color: "#b86e7d" }}>
                    ♥ {m.harmony_score ?? "—"}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
