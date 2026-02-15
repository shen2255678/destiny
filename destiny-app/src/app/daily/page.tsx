"use client";

/**
 * DESTINY — Daily Feed Page
 * Route: /daily
 *
 * Layout: healing glassmorphism light theme
 * 12-col grid:
 *   - Left sidebar  (col-span-3): Vibrational State + Moon Phase
 *   - Main section  (col-span-9): 3 match cards (Passion | Wildcard | Stability)
 *
 * Requires in layout.tsx:
 *   <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
 *
 * Usage:
 *   Navigate to /daily — no props required, all data is mocked inline.
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NavItem {
  icon: string;
  label: string;
  active?: boolean;
  href: string;
}

interface MatchTag {
  label: string;
  colorClass: string;
  borderClass: string;
}

interface MatchCard {
  id: string;
  type: "passion" | "wildcard" | "stability";
  archetype: string;
  label: string;
  matchPct: string;
  icon: string;
  tags: MatchTag[];
  radarScores: { passion: number; stability: number; communication: number };
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const NAV_ITEMS: NavItem[] = [
  { icon: "grid_view", label: "Deck", href: "/connections" },
  { icon: "auto_awesome", label: "Daily", active: true, href: "/daily" },
  { icon: "history_edu", label: "History", href: "/connections" },
  { icon: "settings", label: "Config", href: "/profile" },
];

const MATCH_CARDS: MatchCard[] = [
  {
    id: "passion",
    type: "passion",
    archetype: "The Catalyst",
    label: "High Passion",
    matchPct: "98%",
    icon: "lock",
    tags: [
      { label: "Magnetic", colorClass: "text-[#b86e7d]", borderClass: "border-[#d98695]/20" },
      { label: "Intense", colorClass: "text-[#b86e7d]", borderClass: "border-[#d98695]/20" },
      { label: "Spontaneous", colorClass: "text-[#b86e7d]", borderClass: "border-[#d98695]/20" },
    ],
    radarScores: { passion: 95, stability: 62, communication: 80 },
  },
  {
    id: "wildcard",
    type: "wildcard",
    archetype: "The Mirror",
    label: "Tension",
    matchPct: "87%",
    icon: "visibility_off",
    tags: [
      { label: "Unpredictable", colorClass: "text-[#8b4a6e]", borderClass: "border-[#e6b3cc]/20" },
      { label: "Reflective", colorClass: "text-[#8b4a6e]", borderClass: "border-[#e6b3cc]/20" },
      { label: "Transformative", colorClass: "text-[#8b4a6e]", borderClass: "border-[#e6b3cc]/20" },
    ],
    radarScores: { passion: 88, stability: 45, communication: 72 },
  },
  {
    id: "stability",
    type: "stability",
    archetype: "The Anchor",
    label: "High Stability",
    matchPct: "89%",
    icon: "lock",
    tags: [
      { label: "Grounding", colorClass: "text-teal-700", borderClass: "border-teal-200" },
      { label: "Nurturing", colorClass: "text-teal-700", borderClass: "border-teal-200" },
      { label: "Devoted", colorClass: "text-teal-700", borderClass: "border-teal-200" },
    ],
    radarScores: { passion: 65, stability: 94, communication: 85 },
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** SVG circle progress — shows vibrational intensity as a ring */
function VibrationalRing() {
  const radius = 60;
  const circumference = 2 * Math.PI * radius; // ≈ 376.99
  // 85 % → dashoffset = circumference * (1 - 0.85)
  const dashOffset = circumference * (1 - 0.85);

  return (
    <div className="relative w-32 h-32 flex items-center justify-center mb-4">
      <svg
        className="w-full h-full -rotate-90"
        viewBox="0 0 128 128"
        aria-hidden="true"
      >
        {/* Track ring */}
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="rgba(217,134,149,0.12)"
          strokeWidth="3"
        />
        {/* Progress ring */}
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="#d98695"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="opacity-80 drop-shadow-md"
        />
      </svg>
      {/* Centre label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-light tracking-tight text-[#5c4059]">SOUL</span>
        <span className="text-[10px] uppercase tracking-wider text-[#d98695] font-medium">
          Resonance
        </span>
      </div>
    </div>
  );
}

/** Left sidebar — vibrational state card + moon phase widget */
function Sidebar() {
  return (
    <aside className="hidden lg:flex lg:col-span-3 flex-col gap-6 h-full justify-center">
      {/* Vibrational State card */}
      <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group transition-all duration-500 hover:shadow-lg">
        {/* Decorative icon */}
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity text-[#d98695] pointer-events-none">
          <span className="material-symbols-outlined text-5xl select-none">
            incomplete_circle
          </span>
        </div>

        <h3 className="text-xs uppercase tracking-widest text-[#8c7089] mb-4">
          Current Vibrational State
        </h3>

        <div className="flex flex-col items-center py-4">
          <VibrationalRing />
        </div>

        <p className="text-sm text-[#8c7089] leading-relaxed text-center font-light">
          Your recent interactions suggest a craving for volatility and
          high-stakes emotional exchange.
        </p>

        <div className="mt-6 pt-6 border-t border-[#d98695]/10 flex justify-between text-xs text-[#8c7089] font-medium">
          <span>Intensity</span>
          <span className="text-[#d98695]">High (85%)</span>
        </div>
      </div>

      {/* Moon phase widget */}
      <div className="glass-panel rounded-2xl p-5 flex items-center justify-between group hover:bg-white/40 transition-colors cursor-pointer">
        <div>
          <h4 className="text-sm text-[#5c4059] font-medium">Waning Crescent</h4>
          <span className="text-xs text-[#8c7089]">Releasing attachments</span>
        </div>
        <div className="w-10 h-10 bg-[#d98695]/10 rounded-full flex items-center justify-center text-[#d98695]">
          <span className="material-symbols-outlined" aria-hidden="true">
            dark_mode
          </span>
        </div>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Match Card sub-components
// ---------------------------------------------------------------------------

/** Abstract gradient image area — replaces external images */
function CardImageArea({ type }: { type: MatchCard["type"] }) {
  const gradientMap: Record<MatchCard["type"], string> = {
    passion:
      "bg-gradient-to-br from-pink-100 via-rose-50 to-white",
    wildcard:
      "bg-gradient-to-br from-[#fdfbfb] to-[#fcecf0]",
    stability:
      "bg-gradient-to-br from-teal-50 via-cyan-50 to-white",
  };

  // Abstract blobs that substitute for the fluid-art images
  const blobMap: Record<MatchCard["type"], React.ReactNode> = {
    passion: (
      <>
        <div className="absolute top-4 left-4 w-24 h-24 rounded-full bg-rose-300/40 blur-2xl group-hover:scale-110 transition-transform duration-1000" />
        <div className="absolute bottom-8 right-6 w-20 h-20 rounded-full bg-pink-400/30 blur-xl group-hover:scale-105 transition-transform duration-700" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-16 rounded-full bg-fuchsia-200/40 blur-2xl" />
        {/* Fade-to-white overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent opacity-80" />
      </>
    ),
    wildcard: (
      <>
        <div className="absolute top-6 left-1/2 -translate-x-1/2 w-28 h-28 rounded-full bg-[#e6b3cc]/50 blur-2xl group-hover:rotate-12 transition-transform duration-[2s]" />
        <div className="absolute bottom-12 left-6 w-16 h-16 rounded-full bg-[#d98695]/30 blur-xl" />
        <div className="absolute top-8 right-4 w-14 h-14 rounded-full bg-[#f7c5a8]/40 blur-xl" />
        {/* Subtle geometric lines layer */}
        <svg
          className="absolute inset-0 w-full h-full opacity-10 group-hover:opacity-20 transition-opacity duration-700"
          viewBox="0 0 300 260"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="150" cy="130" r="80" stroke="#d98695" strokeWidth="0.5" />
          <circle cx="150" cy="130" r="50" stroke="#d98695" strokeWidth="0.5" />
          <circle cx="150" cy="130" r="20" stroke="#d98695" strokeWidth="0.5" />
          <line x1="150" y1="50" x2="150" y2="210" stroke="#d98695" strokeWidth="0.5" />
          <line x1="70" y1="130" x2="230" y2="130" stroke="#d98695" strokeWidth="0.5" />
          <line x1="94" y1="74" x2="206" y2="186" stroke="#d98695" strokeWidth="0.3" />
          <line x1="206" y1="74" x2="94" y2="186" stroke="#d98695" strokeWidth="0.3" />
        </svg>
      </>
    ),
    stability: (
      <>
        <div className="absolute top-4 right-4 w-24 h-24 rounded-full bg-teal-200/50 blur-2xl group-hover:scale-110 transition-transform duration-1000" />
        <div className="absolute bottom-8 left-6 w-20 h-20 rounded-full bg-cyan-300/30 blur-xl group-hover:scale-105 transition-transform duration-700" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-28 h-14 rounded-full bg-emerald-100/60 blur-2xl" />
        {/* Ripple wave layers */}
        <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent opacity-80" />
      </>
    ),
  };

  return (
    <div className={`flex-1 ${gradientMap[type]} relative overflow-hidden`}>
      {blobMap[type]}
    </div>
  );
}

/** Lock / visibility icon overlay centred on the card image */
function CardIconOverlay({
  icon,
  type,
  isWildcard,
}: {
  icon: string;
  type: MatchCard["type"];
  isWildcard: boolean;
}) {
  const sizeClass = isWildcard ? "w-20 h-20" : "w-16 h-16";
  const borderClass = isWildcard
    ? "border-2 border-[#d98695]/30 group-hover:border-[#d98695]"
    : type === "stability"
    ? "border border-[#9be3d5]"
    : "border border-[#ff9eb5]";
  const iconColorClass =
    type === "stability"
      ? "text-[#9be3d5]"
      : type === "wildcard"
      ? "text-[#d98695]"
      : "text-[#ff9eb5]";
  const iconSizeClass = isWildcard ? "text-3xl" : "text-2xl";

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div
        className={`${sizeClass} ${borderClass} rounded-full flex items-center justify-center bg-white/20 backdrop-blur-sm group-hover:bg-white/40 transition-all duration-500 shadow-sm`}
      >
        <span
          className={`material-symbols-outlined ${iconColorClass} ${iconSizeClass}`}
          aria-hidden="true"
        >
          {icon}
        </span>
      </div>
    </div>
  );
}

/** Footer content inside a card */
function CardFooter({ card }: { card: MatchCard }) {
  const isWildcard = card.type === "wildcard";
  const labelColorClass =
    card.type === "stability"
      ? "text-teal-600"
      : card.type === "wildcard"
      ? "text-[#d98695]"
      : "text-[#b86e7d]";

  const radarColors = {
    passion: "#d98695",
    stability: "#a8e6cf",
    communication: "#f7c5a8",
  };

  return (
    <div
      className={`${
        isWildcard
          ? "p-6 bg-white/90 border-t border-[#d98695]/10"
          : "p-5 bg-white/60 border-t border-white/50 backdrop-blur-md"
      } relative z-10`}
    >
      <div className="flex justify-between items-start mb-2">
        <span
          className={`text-xs font-bold ${labelColorClass} tracking-widest uppercase`}
        >
          {card.label}
        </span>
        <span className="text-xs text-[#8c7089] font-medium">{card.matchPct}</span>
      </div>

      <h3
        className={`text-[#5c4059] font-light ${
          isWildcard ? "text-xl font-medium" : "text-lg"
        } font-sans mb-3`}
      >
        {card.archetype}
      </h3>

      {/* Radar scores */}
      <div className="space-y-1 mb-3">
        {(Object.entries(card.radarScores) as [string, number][]).map(([key, value]) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-[9px] text-[#8c7089] w-[72px] capitalize">{key}</span>
            <div className="flex-1 h-1 rounded-full bg-black/5">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${value}%`,
                  backgroundColor: radarColors[key as keyof typeof radarColors],
                }}
              />
            </div>
            <span className="text-[9px] font-medium" style={{ color: radarColors[key as keyof typeof radarColors] }}>
              {value}
            </span>
          </div>
        ))}
      </div>

      {/* Chameleon tags */}
      {card.tags && card.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {card.tags.map((tag) => (
            <span
              key={tag.label}
              className={`text-[10px] px-2 py-0.5 rounded-full bg-white/50 border ${tag.borderClass} ${tag.colorClass}`}
            >
              {tag.label}
            </span>
          ))}
        </div>
      )}

      {/* Accept / Pass buttons */}
      <div className="flex gap-2 mt-1">
        <button
          className="flex-1 py-2 rounded-full glass-panel border border-white/60 text-[10px] uppercase tracking-widest text-[#8c7089] font-medium hover:bg-white/60 transition-colors cursor-pointer"
          aria-label={`Pass on ${card.archetype}`}
        >
          Pass
        </button>
        <button
          className="flex-1 py-2 rounded-full text-[10px] uppercase tracking-widest text-white font-medium shadow-[0_4px_15px_rgba(217,134,149,0.3)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)] transition-all cursor-pointer"
          style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
          aria-label={`Accept ${card.archetype}`}
        >
          Accept
        </button>
      </div>
    </div>
  );
}

/** Single match card — passion | wildcard | stability */
function MatchCardItem({ card }: { card: MatchCard }) {
  const isWildcard = card.type === "wildcard";

  // Halo glow layer — colour differs by type
  const haloGradient =
    card.type === "passion"
      ? "from-[#ff9eb5] to-white"
      : card.type === "stability"
      ? "from-[#9be3d5] to-white"
      : "from-[#d98695] via-[#f7c5a8] to-white";

  const haloOpacity = isWildcard
    ? "opacity-40 group-hover:opacity-80"
    : "opacity-0 group-hover:opacity-70";

  const haloBlur = isWildcard ? "blur-2xl" : "blur-xl";
  const haloInset = isWildcard ? "-inset-[3px]" : "-inset-[2px]";

  const cardBg = isWildcard
    ? "bg-white/80 border-white shadow-xl"
    : "bg-white/40 border-white/60 shadow-sm";

  const heightClass = isWildcard ? "lg:h-[540px]" : "lg:h-[500px]";
  const hoverTranslate = isWildcard
    ? "hover:-translate-y-6"
    : "hover:-translate-y-4";

  return (
    <div
      className={`relative ${isWildcard ? "w-full lg:w-[34%] max-w-[340px] z-10" : "w-full lg:w-[30%] max-w-[320px]"} ${heightClass} group cursor-pointer breathing-card transition-all duration-500 ${hoverTranslate}`}
      role="article"
      aria-label={`Match card: ${card.archetype}`}
    >
      {/* Glow halo */}
      <div
        className={`absolute ${haloInset} bg-gradient-to-b ${haloGradient} rounded-2xl ${haloOpacity} ${haloBlur} transition duration-700 pointer-events-none`}
        aria-hidden="true"
      />

      {/* Card body */}
      <div
        className={`relative h-full ${cardBg} backdrop-blur-xl rounded-2xl overflow-hidden border flex flex-col`}
      >
        {/* Abstract image zone */}
        <CardImageArea type={card.type} />

        {/* Centred icon overlay */}
        <CardIconOverlay
          icon={card.icon}
          type={card.type}
          isWildcard={isWildcard}
        />

        {/* Footer info */}
        <CardFooter card={card} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Social Energy Bar
// ---------------------------------------------------------------------------

type SocialEnergyLevel = "high" | "medium" | "low";

const ENERGY_CONFIG: Record<SocialEnergyLevel, { emoji: string; color: string; glow: string; label: string; desc: string }> = {
  high: { emoji: "\u{1F7E2}", color: "#4ade80", glow: "rgba(74,222,128,0.4)", label: "High", desc: "想認識新靈魂" },
  medium: { emoji: "\u{1F7E1}", color: "#facc15", glow: "rgba(250,204,21,0.4)", label: "Medium", desc: "簡單聊聊就好" },
  low: { emoji: "\u{1F535}", color: "#60a5fa", glow: "rgba(96,165,250,0.4)", label: "Low", desc: "請給予空間" },
};

const ENERGY_CYCLE: SocialEnergyLevel[] = ["high", "medium", "low"];

function SocialEnergyToggle({ energy, onToggle }: { energy: SocialEnergyLevel; onToggle: () => void }) {
  const config = ENERGY_CONFIG[energy];
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={onToggle}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border border-white/50 hover:bg-white/60 transition-all duration-200 cursor-pointer"
        aria-label={`社交能量: ${config.label} — ${config.desc}。點擊切換`}
      >
        <div
          className="w-2.5 h-2.5 rounded-full transition-all duration-300"
          style={{ backgroundColor: config.color, boxShadow: `0 0 8px ${config.glow}` }}
        />
        <span className="text-[10px] font-medium tracking-wider text-[#5c4059] uppercase">
          {config.label}
        </span>
      </button>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 rounded-xl glass-panel border border-white/50 shadow-lg whitespace-nowrap z-50">
          <p className="text-[10px] text-[#8c7089] font-medium mb-1">社交能量條</p>
          <p className="text-xs text-[#5c4059]">{config.emoji} {config.desc}</p>
          <p className="text-[9px] text-[#8c7089] mt-1">點擊切換狀態</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Top Header
// ---------------------------------------------------------------------------

function TopHeader({ energy, onToggleEnergy }: { energy: SocialEnergyLevel; onToggleEnergy: () => void }) {
  const router = useRouter();

  const headerLinks = [
    { label: "Archives", href: "/connections" },
    { label: "Settings", href: "/profile" },
  ];

  return (
    <header
      className="relative z-20 w-full px-8 py-6 flex justify-between items-center"
      role="banner"
    >
      {/* Left — live indicator + page title */}
      <div className="flex items-center gap-3">
        <div
          className="w-3 h-3 bg-[#d98695] rounded-full animate-pulse shadow-[0_0_10px_#d98695]"
          aria-hidden="true"
        />
        <h1 className="text-xs uppercase tracking-[0.3em] text-[#5c4059]/80 font-semibold">
          The Black Box // Daily Feed
        </h1>
      </div>

      {/* Centre — nav links (hidden on mobile) */}
      <nav
        className="hidden md:flex items-center gap-8 text-sm font-medium text-[#8c7089]/80"
        aria-label="Main navigation"
      >
        {headerLinks.map((link) => (
          <button
            key={link.label}
            onClick={() => router.push(link.href)}
            className="cursor-pointer hover:text-[#d98695] transition-colors bg-transparent border-none p-0"
          >
            {link.label}
          </button>
        ))}
      </nav>

      {/* Right — energy toggle + notification + avatar */}
      <div className="flex items-center gap-4">
        {/* Social Energy Toggle */}
        <SocialEnergyToggle energy={energy} onToggle={onToggleEnergy} />

        <button
          className="relative p-2 rounded-full hover:bg-white/40 transition-colors group"
          aria-label="Notifications (1 unread)"
        >
          <span
            className="material-symbols-outlined text-[#8c7089] group-hover:text-[#d98695] text-2xl"
            aria-hidden="true"
          >
            notifications
          </span>
          <span
            className="absolute top-2 right-2 w-2 h-2 bg-[#d98695] rounded-full"
            aria-hidden="true"
          />
        </button>

        {/* Avatar — clickable, navigates to profile */}
        <button
          onClick={() => router.push("/profile")}
          className="w-10 h-10 rounded-full bg-gradient-to-br from-[#d98695] to-[#f7c5a8] p-[2px] cursor-pointer"
          aria-label="Go to profile"
        >
          <div className="w-full h-full rounded-full bg-gradient-to-br from-[#fcecf0] to-[#fdf2e9] border-2 border-white flex items-center justify-center">
            <span
              className="material-symbols-outlined text-[#d98695] text-base"
              aria-hidden="true"
            >
              person
            </span>
          </div>
        </button>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Floating Bottom Nav
// ---------------------------------------------------------------------------

function FloatingNav() {
  const router = useRouter();

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
      <nav
        className="bg-white/80 backdrop-blur-lg border border-white px-2 py-2 rounded-full shadow-[0_10px_40px_-10px_rgba(217,134,149,0.3)] flex items-center gap-1"
        aria-label="Bottom navigation"
      >
        {NAV_ITEMS.map((item) => {
          const isActive = item.active;
          return (
            <div key={item.label} className="relative group">
              <button
                onClick={() => router.push(item.href)}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
                  isActive
                    ? "bg-gradient-to-br from-[#d98695] to-[#b86e7d] text-white shadow-[0_4px_12px_rgba(217,134,149,0.4)] hover:shadow-[0_6px_16px_rgba(217,134,149,0.6)] scale-110 mx-2"
                    : "bg-transparent hover:bg-[#d98695]/10 text-[#8c7089] hover:text-[#d98695]"
                }`}
              >
                <span
                  className="material-symbols-outlined text-xl"
                  aria-hidden="true"
                >
                  {item.icon}
                </span>
              </button>
              {/* Tooltip */}
              {!isActive && (
                <span className="absolute -top-10 left-1/2 -translate-x-1/2 scale-0 group-hover:scale-100 transition-transform bg-[#5c4059] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap pointer-events-none">
                  {item.label}
                </span>
              )}
            </div>
          );
        })}
      </nav>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function DailyFeedPage() {
  const [energy, setEnergy] = useState<SocialEnergyLevel>("medium");

  // Load social energy from API
  useEffect(() => {
    fetch("/api/profile/energy")
      .then((res) => res.ok ? res.json() : null)
      .then((data) => { if (data?.social_energy) setEnergy(data.social_energy); })
      .catch(() => {});
  }, []);

  const handleToggleEnergy = useCallback(() => {
    const currentIdx = ENERGY_CYCLE.indexOf(energy);
    const nextEnergy = ENERGY_CYCLE[(currentIdx + 1) % ENERGY_CYCLE.length];
    setEnergy(nextEnergy);
    // Persist to DB (fire-and-forget)
    fetch("/api/profile/energy", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ social_energy: nextEnergy }),
    }).catch(() => {});
  }, [energy]);

  return (
    <div className="min-h-screen flex flex-col overflow-hidden relative selection:bg-[#d98695] selection:text-white">
      {/* Ambient light blobs — decorative, aria-hidden */}
      <div
        className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-[#f7c5a8] opacity-30 blur-[100px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#d98695] opacity-20 blur-[120px] pointer-events-none"
        aria-hidden="true"
      />

      {/* Top header */}
      <TopHeader energy={energy} onToggleEnergy={handleToggleEnergy} />

      {/* Main content grid */}
      <main
        className="relative z-10 flex-1 w-full max-w-7xl mx-auto px-4 md:px-6 py-4 grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-8 lg:h-[calc(100vh-100px)]"
        role="main"
        aria-label="Daily match feed"
      >
        {/* ---- Left sidebar (col 1–3) ---- */}
        <Sidebar />

        {/* ---- Cards section (col 4–12) ---- */}
        <section
          className="col-span-1 lg:col-span-9 flex flex-col h-full relative"
          aria-label="Today's matched Source Codes"
        >
          {/* Section heading */}
          <div className="text-center mb-8 mt-4">
            <h2 className="text-xl md:text-2xl font-light text-[#5c4059] tracking-wide">
              The stars have aligned these three{" "}
              <span className="text-[#d98695] font-normal">Source Codes</span>{" "}
              for you.
            </h2>
            <p className="text-sm text-[#8c7089] mt-2 tracking-wide font-light">
              Select a card to initiate resonance sequence.
            </p>
          </div>

          {/* Three match cards */}
          <div
            className="flex-1 flex flex-col lg:flex-row items-center justify-center gap-6 px-4 pb-16 w-full"
            role="list"
            aria-label="Match cards"
          >
            {MATCH_CARDS.map((card) => (
              <MatchCardItem key={card.id} card={card} />
            ))}
          </div>
        </section>
      </main>

      {/* Floating bottom navigation */}
      <FloatingNav />
    </div>
  );
}
