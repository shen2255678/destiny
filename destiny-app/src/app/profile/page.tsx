"use client";

/**
 * DESTINY — Profile Page (Self-View)
 * Route: /profile
 *
 * Displays the user's own "Source Code" — their archetype, base stats, data
 * tier, and astrology summary. Per MVP spec, users only ever see positive data
 * about themselves. Other users see chameleon tags generated relationally, NOT
 * these raw values.
 *
 * Design: healing glassmorphism light theme, consistent with /daily.
 *
 * Usage:
 *   Navigate to /profile — no props required, all data is mocked inline.
 *   Back arrow links to /daily.
 */

import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BaseStat {
  labelZh: string;
  labelEn: string;
  level: number;
  max: number;
  color: string;
  glowColor: string;
}

interface AstroItem {
  planet: string;
  sign: string;
  icon: string;
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const BASE_STATS: BaseStat[] = [
  {
    labelZh: "激情",
    labelEn: "Passion",
    level: 7,
    max: 10,
    color: "#d98695",
    glowColor: "rgba(217,134,149,0.35)",
  },
  {
    labelZh: "穩定",
    labelEn: "Stability",
    level: 5,
    max: 10,
    color: "#a8e6cf",
    glowColor: "rgba(168,230,207,0.35)",
  },
  {
    labelZh: "智識",
    labelEn: "Intellect",
    level: 8,
    max: 10,
    color: "#f7c5a8",
    glowColor: "rgba(247,197,168,0.40)",
  },
];

const ASTRO_ITEMS: AstroItem[] = [
  { planet: "Sun", sign: "Capricorn", icon: "wb_sunny" },
  { planet: "Moon", sign: "Cancer", icon: "dark_mode" },
  { planet: "Venus", sign: "Aquarius", icon: "favorite" },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Decorative ambient gradient blobs — aria-hidden */
function AmbientBlobs() {
  return (
    <>
      <div
        className="absolute top-[-15%] right-[-10%] w-[55%] h-[55%] rounded-full bg-[#f7c5a8] opacity-25 blur-[100px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-[-5%] left-[-8%] w-[45%] h-[45%] rounded-full bg-[#d98695] opacity-15 blur-[110px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute top-[40%] left-[30%] w-[30%] h-[30%] rounded-full bg-[#a8e6cf] opacity-20 blur-[80px] pointer-events-none"
        aria-hidden="true"
      />
    </>
  );
}

/** Top navigation bar with back arrow and page title */
function TopBar() {
  return (
    <header
      className="relative z-20 w-full px-6 py-5 flex items-center gap-4"
      role="banner"
    >
      <Link
        href="/daily"
        className="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200 shrink-0"
        aria-label="Back to Daily Feed"
      >
        <span className="material-symbols-outlined text-xl" aria-hidden="true">
          arrow_back
        </span>
      </Link>

      <div className="flex-1 flex flex-col">
        <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] font-medium">
          Your Source Code
        </p>
        <h1 className="text-lg font-light text-[#5c4059] tracking-wide leading-tight">
          My Source Code
        </h1>
      </div>

      {/* Gold tier indicator in header */}
      <div
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel"
        aria-label="Gold Tier member"
      >
        <span className="text-[#b86e7d] text-xs font-semibold tracking-wider">
          ✦ Gold
        </span>
      </div>
    </header>
  );
}

/** Archetype card — large centered glass card */
function ArchetypeCard() {
  return (
    <section
      className="glass-panel rounded-3xl p-8 relative overflow-hidden breathing-card transition-all duration-500"
      aria-labelledby="archetype-title"
    >
      {/* Decorative background glow inside card */}
      <div
        className="absolute inset-0 bg-gradient-to-br from-[#fcecf0]/60 via-white/20 to-[#fdf2e9]/40 rounded-3xl pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute -top-8 -right-8 w-40 h-40 rounded-full bg-[#d98695] opacity-10 blur-3xl pointer-events-none"
        aria-hidden="true"
      />

      {/* Icon */}
      <div className="relative z-10 flex justify-center mb-5">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center shadow-[0_8px_24px_rgba(217,134,149,0.25)]"
          style={{
            background:
              "linear-gradient(135deg, rgba(217,134,149,0.15), rgba(247,197,168,0.15))",
            border: "1.5px solid rgba(217,134,149,0.3)",
          }}
          aria-hidden="true"
        >
          <span
            className="material-symbols-outlined text-4xl"
            style={{ color: "#d98695" }}
          >
            explore
          </span>
        </div>
      </div>

      {/* Archetype name */}
      <div className="relative z-10 text-center mb-5">
        <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] mb-1">
          Your Archetype
        </p>
        <h2
          id="archetype-title"
          className="text-2xl font-light text-[#5c4059] tracking-wide"
        >
          The Wanderer
        </h2>
        <p className="text-sm text-[#8c7089] mt-0.5 font-light">流浪者</p>
      </div>

      {/* Divider */}
      <div
        className="relative z-10 h-px w-16 mx-auto mb-5 rounded-full"
        style={{
          background: "linear-gradient(90deg, transparent, #d98695, transparent)",
        }}
        aria-hidden="true"
      />

      {/* Positive description */}
      <p className="relative z-10 text-sm text-[#5c4059]/80 leading-relaxed text-center font-light max-w-md mx-auto">
        You carry within you an unquenchable curiosity that draws people and
        ideas toward you like a gentle gravity. Your open-hearted willingness to
        explore the unknown makes you a rare kind of companion — one who brings
        wonder to ordinary moments and sees possibility where others see
        endings. Your connections run deep precisely because you never stop
        growing.
      </p>
    </section>
  );
}

/** Single animated stat bar */
function StatBar({ stat }: { stat: BaseStat }) {
  const pct = (stat.level / stat.max) * 100;

  return (
    <div className="space-y-2" role="group" aria-label={`${stat.labelZh} ${stat.labelEn} level ${stat.level} of ${stat.max}`}>
      {/* Label row */}
      <div className="flex justify-between items-baseline">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-medium text-[#5c4059]">
            {stat.labelZh}
          </span>
          <span className="text-xs text-[#8c7089] font-light">
            {stat.labelEn}
          </span>
        </div>
        <span
          className="text-xs font-semibold tracking-wider"
          style={{ color: stat.color }}
          aria-hidden="true"
        >
          Lv.{stat.level} / {stat.max}
        </span>
      </div>

      {/* Progress track */}
      <div
        className="relative h-2.5 rounded-full overflow-hidden"
        style={{ background: "rgba(92,64,89,0.06)" }}
        role="progressbar"
        aria-valuenow={stat.level}
        aria-valuemin={0}
        aria-valuemax={stat.max}
        aria-label={`${stat.labelEn} progress`}
      >
        {/* Filled bar */}
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${stat.color}99, ${stat.color})`,
            boxShadow: `0 0 8px ${stat.glowColor}`,
          }}
        />

        {/* Level pip markers */}
        {Array.from({ length: stat.max - 1 }, (_, i) => (
          <div
            key={i}
            className="absolute top-0 bottom-0 w-px"
            style={{
              left: `${((i + 1) / stat.max) * 100}%`,
              background: "rgba(255,255,255,0.6)",
            }}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}

/** Base Stats section */
function BaseStatsSection() {
  return (
    <section
      className="glass-panel rounded-2xl p-6 space-y-5"
      aria-labelledby="stats-heading"
    >
      <div className="flex items-center gap-2 mb-1">
        <span
          className="material-symbols-outlined text-lg text-[#d98695]"
          aria-hidden="true"
        >
          bar_chart
        </span>
        <h3
          id="stats-heading"
          className="text-xs uppercase tracking-[0.3em] text-[#8c7089] font-medium"
        >
          Base Stats
        </h3>
      </div>

      {BASE_STATS.map((stat) => (
        <StatBar key={stat.labelEn} stat={stat} />
      ))}
    </section>
  );
}

/** Data Tier badge card */
function DataTierCard() {
  return (
    <section
      className="glass-panel rounded-2xl p-5 flex items-center justify-between"
      aria-label="Data tier: Gold Tier"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #f7c5a8, #d98695)",
            boxShadow: "0 4px 14px rgba(217,134,149,0.35)",
          }}
          aria-hidden="true"
        >
          <span className="material-symbols-outlined text-white text-sm">
            workspace_premium
          </span>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[#8c7089] font-medium">
            Data Tier
          </p>
          <p className="text-sm font-semibold text-[#5c4059] tracking-wide">
            Gold Tier ✦
          </p>
        </div>
      </div>

      <div className="text-right">
        <p className="text-[10px] text-[#8c7089] leading-relaxed font-light max-w-[140px]">
          Precise birth time recorded — full D1 & D9 chart enabled.
        </p>
      </div>
    </section>
  );
}

/** Astrology summary card */
function AstroSummaryCard() {
  return (
    <section
      className="glass-panel rounded-2xl p-6"
      aria-labelledby="astro-heading"
    >
      <div className="flex items-center gap-2 mb-5">
        <span
          className="material-symbols-outlined text-lg text-[#d98695]"
          aria-hidden="true"
        >
          auto_awesome
        </span>
        <h3
          id="astro-heading"
          className="text-xs uppercase tracking-[0.3em] text-[#8c7089] font-medium"
        >
          Astro Summary
        </h3>
      </div>

      <div className="grid grid-cols-3 gap-3" role="list">
        {ASTRO_ITEMS.map((item) => (
          <div
            key={item.planet}
            className="flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-200 hover:bg-white/40 cursor-default"
            style={{ background: "rgba(255,255,255,0.2)" }}
            role="listitem"
            aria-label={`${item.planet}: ${item.sign}`}
          >
            <div
              className="w-9 h-9 rounded-full flex items-center justify-center"
              style={{
                background: "linear-gradient(135deg, rgba(217,134,149,0.15), rgba(247,197,168,0.15))",
                border: "1px solid rgba(217,134,149,0.2)",
              }}
              aria-hidden="true"
            >
              <span
                className="material-symbols-outlined text-base"
                style={{ color: "#d98695" }}
              >
                {item.icon}
              </span>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-[#8c7089] uppercase tracking-wider font-medium">
                {item.planet}
              </p>
              <p className="text-xs text-[#5c4059] font-medium mt-0.5">
                {item.sign}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Subtle note about data source */}
      <p className="mt-4 text-[10px] text-[#8c7089]/70 text-center font-light leading-relaxed">
        Vedic D1 & D9 chart · Tier 1 Gold precision
      </p>
    </section>
  );
}

/** Privacy disclaimer note */
function PrivacyNote() {
  return (
    <aside
      className="glass-panel rounded-2xl p-4 flex items-start gap-3"
      role="note"
      aria-label="Privacy information about profile visibility"
    >
      <span
        className="material-symbols-outlined text-base text-[#d98695] shrink-0 mt-0.5"
        aria-hidden="true"
      >
        info
      </span>
      <p className="text-xs text-[#8c7089] leading-relaxed font-light">
        你的原型與基礎數值只有你看得到。其他用戶看到的是根據你們關係動態生成的變色龍標籤。
      </p>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  return (
    /*
     * Accessibility: landmarks used throughout (header, main, nav via Link,
     * section with aria-labelledby, aside). Focus order follows visual order.
     *
     * Performance: no images — all visuals are CSS gradients and SVG glows.
     * All mock data is static; no client fetches needed here.
     */
    <div className="min-h-screen flex flex-col relative selection:bg-[#d98695] selection:text-white">
      {/* Ambient light blobs */}
      <AmbientBlobs />

      {/* Top navigation */}
      <TopBar />

      {/* Scrollable main content */}
      <main
        className="relative z-10 flex-1 w-full max-w-lg mx-auto px-4 pb-10 flex flex-col gap-5"
        role="main"
        aria-label="My Source Code profile"
      >
        {/* 1 — Large archetype card */}
        <ArchetypeCard />

        {/* 2 — Base stats bars */}
        <BaseStatsSection />

        {/* 3 — Data tier badge */}
        <DataTierCard />

        {/* 4 — Astrology summary */}
        <AstroSummaryCard />

        {/* 5 — Privacy note */}
        <PrivacyNote />
      </main>
    </div>
  );
}
