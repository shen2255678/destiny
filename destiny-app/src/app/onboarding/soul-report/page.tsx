"use client";

// ============================================================
// DESTINY — Onboarding Step 4: Soul Report
// 你的靈魂原型 — "Your Soul Archetype" (The Reveal)
// Next.js 14 App Router · Tailwind CSS v4 · Client Component
// ============================================================

import { useEffect, useState } from "react";
import Link from "next/link";

// ------------------------------------------------------------------
// Types for API response
// ------------------------------------------------------------------
interface Archetype {
  archetype_name: string;
  archetype_desc: string;
  tags: string[];
  stats: { key: string; label: string; english: string; level: number; max: number; color: string }[];
}

// Fallback archetype while loading
const fallbackArchetype: Archetype = {
  archetype_name: "Decoding...",
  archetype_desc: "你的靈魂正在被解碼...",
  tags: [],
  stats: [
    { key: "passion", label: "激情", english: "Passion", level: 0, max: 10, color: "#d98695" },
    { key: "stability", label: "穩定", english: "Stability", level: 0, max: 10, color: "#a8e6cf" },
    { key: "intellect", label: "智識", english: "Intellect", level: 0, max: 10, color: "#f7c5a8" },
  ],
};

// ------------------------------------------------------------------
// Inline style helpers
// ------------------------------------------------------------------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 50%, #a8e6cf 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const heroGradient: React.CSSProperties = {
  background: "linear-gradient(135deg, #b86e7d 0%, #d98695 40%, #f7c5a8 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

// ------------------------------------------------------------------
// Animated stat bar
// ------------------------------------------------------------------
interface StatBarProps {
  label: string;
  english: string;
  level: number;
  max: number;
  color: string;
  animationDelay: number;
  isVisible: boolean;
}

function StatBar({ label, english, level, max, color, animationDelay, isVisible }: StatBarProps) {
  const percentage = (level / max) * 100;

  return (
    <div className="space-y-2">
      {/* Label row */}
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold text-[#5c4059]">{label}</span>
          <span className="text-[11px] text-[#8c7089]">{english}</span>
        </div>
        <div className="flex items-baseline gap-1">
          <span
            className="text-lg font-bold"
            style={{ color }}
          >
            {level}
          </span>
          <span className="text-xs text-[#8c7089]">/{max}</span>
        </div>
      </div>

      {/* Bar track */}
      <div
        className="h-2.5 rounded-full bg-white/40 overflow-hidden"
        role="meter"
        aria-valuenow={level}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={`${label} level ${level} of ${max}`}
      >
        <div
          className="h-full rounded-full transition-all ease-out"
          style={{
            width: isVisible ? `${percentage}%` : "0%",
            background: `linear-gradient(90deg, ${color}cc, ${color})`,
            transitionDuration: "1s",
            transitionDelay: `${animationDelay}ms`,
            boxShadow: `0 0 8px ${color}60`,
          }}
        />
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// Page component
// ------------------------------------------------------------------
export default function SoulReportPage() {
  const [phase, setPhase] = useState<"loading" | "reveal" | "bars">("loading");
  const [data, setData] = useState<Archetype>(fallbackArchetype);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchArchetype() {
      try {
        const res = await fetch("/api/onboarding/soul-report");
        const json = await res.json();
        if (res.ok && json.data) {
          setData(json.data);
        } else {
          setError(json.error || "Failed to generate archetype");
        }
      } catch {
        setError("Network error. Please try again.");
      }
      // Phase 1: reveal after data loads
      const t1 = setTimeout(() => setPhase("reveal"), 300);
      const t2 = setTimeout(() => setPhase("bars"), 900);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }
    fetchArchetype();
  }, []);

  const isRevealed = phase === "reveal" || phase === "bars";
  const barsVisible = phase === "bars";

  return (
    <div className="flex flex-col gap-8 py-4">
      {/* ---- Header ---- */}
      <header
        className="text-center space-y-2 transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transform: isRevealed ? "translateY(0)" : "translateY(12px)",
        }}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border border-primary/20 mb-2">
          <span
            className="material-symbols-outlined text-sm text-primary animate-soft-pulse"
            style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
            aria-hidden="true"
          >
            auto_awesome
          </span>
          <span className="text-[10px] font-medium tracking-widest uppercase text-[#8c7089]">
            Step 4 of 4 · Soul Report
          </span>
        </div>

        <h1 className="text-3xl font-sans font-light text-[#5c4059]">
          <span style={gradientText} className="font-semibold">
            你的靈魂原型
          </span>
        </h1>
        <p className="text-sm text-[#8c7089] font-light">
          Your Soul Archetype has been decoded.
        </p>
      </header>

      {/* ---- Archetype reveal card ---- */}
      <section
        aria-label="靈魂原型"
        className="glass-panel rounded-3xl overflow-hidden border border-white/50
                   shadow-[0_16px_48px_rgba(217,134,149,0.2)] transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transform: isRevealed ? "translateY(0) scale(1)" : "translateY(20px) scale(0.97)",
        }}
      >
        {/* Top gradient accent */}
        <div
          className="h-2"
          style={{
            background:
              "linear-gradient(90deg, #d98695 0%, #f7c5a8 50%, #a8e6cf 100%)",
          }}
          aria-hidden="true"
        />

        <div className="p-6 sm:p-8 text-center">
          {/* Icon halo */}
          <div className="relative inline-flex items-center justify-center mb-5">
            {/* Outer glow ring */}
            <div
              className="absolute w-28 h-28 rounded-full animate-soft-pulse"
              style={{
                background:
                  "radial-gradient(circle, rgba(217,134,149,0.2) 0%, transparent 70%)",
              }}
              aria-hidden="true"
            />
            {/* Inner icon circle */}
            <div
              className="relative w-20 h-20 rounded-2xl flex items-center justify-center"
              style={{
                background:
                  "linear-gradient(135deg, rgba(217,134,149,0.15) 0%, rgba(247,197,168,0.1) 100%)",
                border: "1.5px solid rgba(217,134,149,0.3)",
              }}
            >
              <span
                className="material-symbols-outlined text-5xl text-primary"
                style={{ fontVariationSettings: "'FILL' 0, 'wght' 200" }}
                aria-hidden="true"
              >
                explore
              </span>
            </div>
          </div>

          {/* Archetype name */}
          <h2
            className="text-4xl font-sans font-semibold mb-1"
            style={heroGradient}
          >
            {data.archetype_name}
          </h2>
          <p className="text-lg font-light text-[#8c7089] mb-5">
            {data.archetype_name}
          </p>

          {/* Tags */}
          <div
            className="flex flex-wrap justify-center gap-2 mb-6"
            role="list"
            aria-label="Archetype traits"
          >
            {data.tags.map((tag) => (
              <span
                key={tag}
                role="listitem"
                className="px-3 py-1 rounded-full text-xs font-medium
                           bg-primary/10 text-primary border border-primary/20"
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Description */}
          <p className="text-sm text-[#8c7089] leading-relaxed max-w-md mx-auto text-left sm:text-center">
            {data.archetype_desc}
          </p>
        </div>
      </section>

      {/* ---- Base stats ---- */}
      <section
        aria-label="靈魂基礎屬性"
        className="glass-panel rounded-3xl p-6 sm:p-8 border border-white/50 space-y-5
                   transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transform: isRevealed ? "translateY(0)" : "translateY(16px)",
          transitionDelay: "150ms",
        }}
      >
        {/* Section title */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="material-symbols-outlined text-lg text-primary"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
            aria-hidden="true"
          >
            bar_chart
          </span>
          <h3 className="text-xs font-semibold tracking-widest uppercase text-[#5c4059]">
            Base Stats
          </h3>
        </div>

        {/* Stat bars */}
        {data.stats.map((stat, i) => (
          <StatBar
            key={stat.key}
            label={stat.label}
            english={stat.english}
            level={stat.level}
            max={stat.max}
            color={stat.color}
            animationDelay={i * 180}
            isVisible={barsVisible}
          />
        ))}
      </section>

      {/* ---- Data tier badge ---- */}
      <div
        className="flex justify-center transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transitionDelay: "300ms",
        }}
      >
        <div
          className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full glass-panel border"
          style={{ borderColor: "rgba(212,175,55,0.4)" }}
          role="status"
          aria-label="Data accuracy tier: Gold"
        >
          <span
            className="material-symbols-outlined text-lg"
            style={{
              fontVariationSettings: "'FILL' 1, 'wght' 400",
              color: "#d4af37",
            }}
            aria-hidden="true"
          >
            workspace_premium
          </span>
          <span className="text-sm font-semibold" style={{ color: "#d4af37" }}>
            Gold Tier
          </span>
          <span className="text-[#d4af37] font-bold text-base">✦</span>
          <span className="text-xs text-[#8c7089]">完整星盤解析</span>
        </div>
      </div>

      {/* ---- Privacy note ---- */}
      <p
        className="text-center text-[11px] text-[#8c7089]/80 leading-relaxed max-w-xs mx-auto
                   transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transitionDelay: "400ms",
        }}
      >
        你的原型只有你看得到，對方看到的是動態標籤。
        <br />
        <span className="text-[#8c7089]/60">
          Your archetype is private. Others only see dynamic Chameleon Tags.
        </span>
      </p>

      {/* ---- Error message ---- */}
      {error && (
        <p
          className="text-xs text-center py-2 px-3 rounded-lg bg-red-50/80"
          style={{ color: "#e74c3c" }}
          role="alert"
        >
          {error}
        </p>
      )}

      {/* ---- Enter DESTINY CTA ---- */}
      <div
        className="flex flex-col items-center gap-3 transition-all duration-700"
        style={{
          opacity: isRevealed ? 1 : 0,
          transform: isRevealed ? "translateY(0)" : "translateY(8px)",
          transitionDelay: "500ms",
        }}
      >
        <Link
          href="/daily"
          className="w-full max-w-sm flex items-center justify-center gap-2.5 px-8 py-4 rounded-full
                     font-semibold text-white text-sm transition-all duration-300
                     shadow-[0_8px_30px_rgba(217,134,149,0.5)] hover:shadow-[0_12px_50px_rgba(217,134,149,0.7)]
                     hover:-translate-y-1 active:scale-[0.98]"
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
          }}
        >
          <span
            className="material-symbols-outlined text-xl"
            style={{ fontVariationSettings: "'FILL' 1, 'wght' 300" }}
            aria-hidden="true"
          >
            spa
          </span>
          <span>Enter DESTINY</span>
          <span
            className="material-symbols-outlined text-lg"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
            aria-hidden="true"
          >
            arrow_forward
          </span>
        </Link>

        <p className="text-[10px] text-[#8c7089]/60 text-center">
          你的靈魂已解碼 · 每日 21:00 推送 3 位命運候選人
        </p>
      </div>
    </div>
  );
}
