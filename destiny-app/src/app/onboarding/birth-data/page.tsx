"use client";

// ============================================================
// DESTINY — Onboarding Step 1: Birth Data
// 你的硬體規格 — "Your Hardware Specs"
// Next.js 14 App Router · Tailwind CSS v4 · Client Component
// ============================================================

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ------------------------------------------------------------------
// Taiwan cities with coordinates for astrology chart calculation
// ------------------------------------------------------------------
const TAIWAN_CITIES = [
  { name: "台北市", lat: 25.0330, lng: 121.5654 },
  { name: "新北市", lat: 25.0120, lng: 121.4657 },
  { name: "桃園市", lat: 24.9936, lng: 121.3010 },
  { name: "台中市", lat: 24.1477, lng: 120.6736 },
  { name: "台南市", lat: 22.9998, lng: 120.2269 },
  { name: "高雄市", lat: 22.6273, lng: 120.3014 },
  { name: "基隆市", lat: 25.1276, lng: 121.7392 },
  { name: "新竹市", lat: 24.8138, lng: 120.9675 },
  { name: "新竹縣", lat: 24.8387, lng: 121.0178 },
  { name: "苗栗縣", lat: 24.5602, lng: 120.8214 },
  { name: "彰化縣", lat: 24.0518, lng: 120.5161 },
  { name: "南投縣", lat: 23.9609, lng: 120.6847 },
  { name: "雲林縣", lat: 23.7092, lng: 120.4313 },
  { name: "嘉義市", lat: 23.4801, lng: 120.4491 },
  { name: "嘉義縣", lat: 23.4518, lng: 120.2551 },
  { name: "屏東縣", lat: 22.6820, lng: 120.4844 },
  { name: "宜蘭縣", lat: 24.7570, lng: 121.7533 },
  { name: "花蓮縣", lat: 23.9910, lng: 121.6017 },
  { name: "台東縣", lat: 22.7583, lng: 121.1444 },
  { name: "澎湖縣", lat: 23.5711, lng: 119.5793 },
  { name: "金門縣", lat: 24.4493, lng: 118.3767 },
  { name: "連江縣", lat: 26.1505, lng: 119.9499 },
] as const;

// ------------------------------------------------------------------
// Data tier indicator config
// ------------------------------------------------------------------
type DataTier = "unknown" | "fuzzy" | "precise";

interface TierConfig {
  label: string;
  chinese: string;
  color: string;
  icon: string;
  description: string;
}

const tierMap: Record<DataTier, TierConfig> = {
  unknown: {
    label: "Bronze Tier",
    chinese: "青銅",
    color: "#cd7f32",
    icon: "workspace_premium",
    description: "基礎星座相容性 · 部分功能受限",
  },
  fuzzy: {
    label: "Silver Tier",
    chinese: "白銀",
    color: "#9e9e9e",
    icon: "workspace_premium",
    description: "模糊邏輯中等精確度 · 大部分功能可用",
  },
  precise: {
    label: "Gold Tier",
    chinese: "黃金",
    color: "#d4af37",
    icon: "workspace_premium",
    description: "完整 D1 & D9 星盤分析 · 最高精確配對",
  },
};

function getTier(birthTime: string): DataTier {
  if (!birthTime || birthTime === "unknown") return "unknown";
  if (birthTime === "precise") return "precise";
  return "fuzzy";
}

// ------------------------------------------------------------------
// Inline style helpers
// ------------------------------------------------------------------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const inputClass =
  "w-full px-4 py-3 rounded-2xl glass-panel border border-white/60 " +
  "text-[#5c4059] placeholder:text-[#8c7089]/60 text-sm font-medium " +
  "outline-none focus:border-primary/50 focus:shadow-[0_0_0_3px_rgba(217,134,149,0.12)] " +
  "transition-all duration-200 bg-transparent appearance-none";

// ------------------------------------------------------------------
// Page component
// ------------------------------------------------------------------
export default function BirthDataPage() {
  const router = useRouter();
  const [birthDate, setBirthDate] = useState("");
  const [birthTimeMode, setBirthTimeMode] = useState("");
  const [preciseTime, setPreciseTime] = useState("");
  const [birthPlace, setBirthPlace] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tier = getTier(birthTimeMode);
  const tierConfig = tierMap[tier];

  const isPrecise = birthTimeMode === "precise";

  const isValid = birthDate.length > 0 && birthTimeMode.length > 0 && birthPlace.length > 0;

  return (
    <div className="flex flex-col gap-8 py-4">
      {/* ---- Header ---- */}
      <header className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border border-primary/20 mb-2">
          <span
            className="material-symbols-outlined text-sm text-primary"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
            aria-hidden="true"
          >
            auto_awesome
          </span>
          <span className="text-[10px] font-medium tracking-widest uppercase text-[#8c7089]">
            Step 1 of 4
          </span>
        </div>

        <h1 className="text-3xl font-sans font-light text-[#5c4059]">
          <span style={gradientText} className="font-semibold">
            你的硬體規格
          </span>
        </h1>
        <p className="text-sm text-[#8c7089] font-light leading-relaxed">
          Stars remember the moment you arrived.
        </p>
      </header>

      {/* ---- Form card ---- */}
      <section
        className="glass-panel rounded-3xl p-6 sm:p-8 space-y-6 border border-white/50"
        aria-label="Birth data form"
      >
        {/* Birth Date */}
        <fieldset>
          <legend className="sr-only">出生資料</legend>

          <div className="space-y-5">
            {/* Date field */}
            <div className="space-y-2">
              <label
                htmlFor="birth-date"
                className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]"
              >
                <span
                  className="material-symbols-outlined text-base text-primary"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  aria-hidden="true"
                >
                  calendar_today
                </span>
                出生日期
              </label>
              <input
                id="birth-date"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className={inputClass}
                aria-required="true"
                max={new Date().toISOString().split("T")[0]}
              />
            </div>

            {/* Birth time mode */}
            <div className="space-y-2">
              <label
                htmlFor="birth-time-mode"
                className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]"
              >
                <span
                  className="material-symbols-outlined text-base text-primary"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  aria-hidden="true"
                >
                  schedule
                </span>
                出生時間
              </label>
              <div className="relative">
                <select
                  id="birth-time-mode"
                  value={birthTimeMode}
                  onChange={(e) => setBirthTimeMode(e.target.value)}
                  className={inputClass + " pr-10 cursor-pointer"}
                  aria-required="true"
                >
                  <option value="" disabled>
                    選擇時間精確度…
                  </option>
                  <option value="precise">精確時間 (最高精準度)</option>
                  <option value="morning">早上 (6–12)</option>
                  <option value="afternoon">下午 (12–18)</option>
                  <option value="evening">晚上 (18–24)</option>
                  <option value="unknown">不清楚</option>
                </select>
                {/* Custom chevron */}
                <span
                  className="material-symbols-outlined text-base text-[#8c7089] absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none"
                  aria-hidden="true"
                >
                  expand_more
                </span>
              </div>
            </div>

            {/* Precise time input — only shown when "精確時間" is selected */}
            {isPrecise && (
              <div
                className="space-y-2"
                style={{
                  animation: "fadeSlideIn 0.25s ease-out both",
                }}
              >
                <label
                  htmlFor="precise-time"
                  className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]"
                >
                  <span
                    className="material-symbols-outlined text-base text-[#d4af37]"
                    style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                    aria-hidden="true"
                  >
                    workspace_premium
                  </span>
                  精確出生時刻
                </label>
                <input
                  id="precise-time"
                  type="time"
                  value={preciseTime}
                  onChange={(e) => setPreciseTime(e.target.value)}
                  className={inputClass + " border-[#d4af37]/40 focus:border-[#d4af37]/70"}
                  aria-required={isPrecise}
                />
                <p className="text-[10px] text-[#8c7089] pl-1">
                  精確出生時間可解鎖完整上升星座與 D9 星盤分析
                </p>
              </div>
            )}

            {/* Birth place — Taiwan city dropdown */}
            <div className="space-y-2">
              <label
                className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]"
              >
                <span
                  className="material-symbols-outlined text-base text-primary"
                  style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                  aria-hidden="true"
                >
                  location_on
                </span>
                出生地點
              </label>
              <Select value={birthPlace} onValueChange={setBirthPlace}>
                <SelectTrigger
                  className="w-full px-4 py-3 rounded-2xl glass-panel border border-white/60 text-[#5c4059] text-sm font-medium bg-transparent h-auto cursor-pointer focus:border-primary/50 focus:ring-[3px] focus:ring-[rgba(217,134,149,0.12)]"
                >
                  <SelectValue placeholder="選擇出生城市…" />
                </SelectTrigger>
                <SelectContent className="max-h-60">
                  {TAIWAN_CITIES.map((city) => (
                    <SelectItem key={city.name} value={city.name}>
                      {city.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </fieldset>
      </section>

      {/* ---- Data tier indicator ---- */}
      <section
        className="glass-panel rounded-2xl p-4 border border-white/50"
        aria-label="資料精確度等級"
        aria-live="polite"
      >
        <div className="flex items-start gap-3">
          {/* Tier badge */}
          <div
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${tierConfig.color}18` }}
          >
            <span
              className="material-symbols-outlined text-xl"
              style={{
                fontVariationSettings: "'FILL' 1, 'wght' 400",
                color: tierConfig.color,
              }}
              aria-hidden="true"
            >
              {tierConfig.icon}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2 mb-1">
              <span
                className="text-xs font-bold tracking-wider"
                style={{ color: tierConfig.color }}
              >
                {tierConfig.label}
              </span>
              <span className="text-[10px] text-[#8c7089]">
                · {tierConfig.chinese}級精準度
              </span>
            </div>
            <p className="text-[11px] text-[#8c7089] leading-relaxed">
              {tierConfig.description}
            </p>

            {/* Progress track — 3 tiers */}
            <div className="flex gap-1 mt-2.5" role="img" aria-label={`精準度: ${tierConfig.label}`}>
              {(["unknown", "fuzzy", "precise"] as DataTier[]).map((t, i) => {
                const tierOrder: Record<DataTier, number> = { unknown: 0, fuzzy: 1, precise: 2 };
                const isActive = tierOrder[tier] >= tierOrder[t];
                const colors: Record<DataTier, string> = {
                  unknown: "#cd7f32",
                  fuzzy: "#9e9e9e",
                  precise: "#d4af37",
                };
                return (
                  <div
                    key={i}
                    className="h-1.5 flex-1 rounded-full transition-all duration-500"
                    style={{
                      background: isActive ? colors[t] : "rgba(255,255,255,0.4)",
                    }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Info note */}
        <p className="mt-3 text-[10px] text-[#8c7089]/80 pl-13 leading-relaxed border-t border-white/30 pt-3 flex items-start gap-1.5">
          <span
            className="material-symbols-outlined text-sm text-primary/60 flex-shrink-0 mt-0.5"
            aria-hidden="true"
          >
            info
          </span>
          提供越精確的出生時間，配對準確度越高 — 精確時間可解鎖黃金級完整星盤。
        </p>
      </section>

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

      {/* ---- Continue CTA ---- */}
      <div className="flex flex-col items-center gap-3">
        <button
          type="button"
          disabled={!isValid || loading}
          onClick={async () => {
            setError("");
            setLoading(true);
            try {
              const selectedCity = TAIWAN_CITIES.find((c) => c.name === birthPlace);
              const res = await fetch("/api/onboarding/birth-data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  birth_date: birthDate,
                  birth_time: birthTimeMode,
                  birth_time_exact: isPrecise ? preciseTime : undefined,
                  birth_city: birthPlace,
                  birth_lat: selectedCity?.lat,
                  birth_lng: selectedCity?.lng,
                }),
              });
              const json = await res.json();
              if (!res.ok) {
                setError(json.error || "Failed to save birth data");
                setLoading(false);
                return;
              }
              router.push("/onboarding/rpv-test");
            } catch {
              setError("Network error. Please try again.");
              setLoading(false);
            }
          }}
          className={
            "w-full max-w-sm flex items-center justify-center gap-2 px-8 py-4 rounded-full " +
            "font-medium text-white text-sm transition-all duration-300 " +
            (isValid && !loading
              ? "shadow-[0_8px_30px_rgba(217,134,149,0.45)] hover:shadow-[0_12px_40px_rgba(217,134,149,0.65)] hover:-translate-y-0.5"
              : "opacity-40 cursor-not-allowed")
          }
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
          }}
          aria-label="Continue to next step"
        >
          <span>{loading ? "Saving..." : "Continue"}</span>
          <span
            className="material-symbols-outlined text-lg"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
            aria-hidden="true"
          >
            arrow_forward
          </span>
        </button>

        <p className="text-[10px] text-[#8c7089]/70 text-center">
          你的出生數據採 AES-256 加密儲存，永不對外分享。
        </p>
      </div>

      {/* Keyframe injection for the precise time field slide-in */}
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
