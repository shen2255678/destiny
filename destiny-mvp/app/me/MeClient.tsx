"use client";

import { useState } from "react";
import Link from "next/link";

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
function zh(val: string | undefined | null, map: Record<string, string>): string {
  if (!val) return "—";
  return map[val] ?? val;
}

interface Profile {
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
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
  const [promptOpen, setPromptOpen] = useState(false);

  const c = (profile?.natal_cache ?? {}) as Record<string, unknown>;

  async function toggleYinYang(val: "yin" | "yang") {
    setYinYang(val);
    if (profile) {
      await fetch(`/api/profiles/${profile.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yin_yang: val }),
      });
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

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#5c4059", letterSpacing: "0.08em", marginBottom: 4 }}>
          ✦ 我的命盤
        </h1>
        <p style={{ color: "#8c7089", fontSize: 13 }}>{profile.display_name}</p>
      </div>

      {/* Yin-Yang toggle */}
      <div style={{
        background: "rgba(255,255,255,0.35)", backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)", borderRadius: 20,
        padding: "20px 24px", marginBottom: 24,
        display: "flex", alignItems: "center", gap: 20,
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

      {/* Planet grid */}
      <div style={{
        background: "rgba(255,255,255,0.3)", backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)", borderRadius: 20,
        padding: "20px 24px", marginBottom: 24,
      }}>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 12 }}>
          行星速覽 · Tier {profile.data_tier}
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px" }}>
          {[
            { label: "☀ 太陽", key: "sun_sign" },
            { label: "☽ 月亮", key: "moon_sign" },
            { label: "↑ 上升", key: "ascendant_sign" },
            { label: "♀ 金星", key: "venus_sign" },
            { label: "♂ 火星", key: "mars_sign" },
            { label: "☿ 水星", key: "mercury_sign" },
            { label: "♄ 土星", key: "saturn_sign" },
          ].map(({ label, key }) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "#8c7089" }}>{label}</span>
              <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c[key] as string, SIGN_ZH)}</span>
            </div>
          ))}
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: "#8c7089" }}>🔥 八字元素</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c["bazi_element"] as string, BAZI_ZH)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: "#8c7089" }}>🧠 依戀類型</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c["attachment_style"] as string, ATT_ZH)}</span>
          </div>
        </div>
      </div>

      {/* Prompt preview (collapsible) */}
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => setPromptOpen((v) => !v)}
          style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.55)",
            borderRadius: promptOpen ? "16px 16px 0 0" : 16, padding: "12px 18px",
            fontSize: 13, fontWeight: 600, color: "#8c7089", cursor: "pointer",
            backdropFilter: "blur(8px)",
          }}
        >
          <span>🔍 命盤原始資料預覽</span>
          <span style={{ transform: promptOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block", transition: "transform 0.25s" }}>▾</span>
        </button>
        {promptOpen && (
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
