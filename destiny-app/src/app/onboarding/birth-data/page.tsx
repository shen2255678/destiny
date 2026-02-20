"use client";

// ============================================================
// DESTINY — Onboarding Step 1: Birth Data
// 你的硬體規格 — "Your Hardware Specs"
// 4-card precision flow (Phase B.5)
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
// Taiwan cities
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
// Two-hour slots (12 grid cells)
// ------------------------------------------------------------------
const TWO_HOUR_SLOTS = [
  { label: "23:00 - 01:00", start: "23:00", end: "01:00" },
  { label: "01:00 - 03:00", start: "01:00", end: "03:00" },
  { label: "03:00 - 05:00", start: "03:00", end: "05:00" },
  { label: "05:00 - 07:00", start: "05:00", end: "07:00" },
  { label: "07:00 - 09:00", start: "07:00", end: "09:00" },
  { label: "09:00 - 11:00", start: "09:00", end: "11:00" },
  { label: "11:00 - 13:00", start: "11:00", end: "13:00" },
  { label: "13:00 - 15:00", start: "13:00", end: "15:00" },
  { label: "15:00 - 17:00", start: "15:00", end: "17:00" },
  { label: "17:00 - 19:00", start: "17:00", end: "19:00" },
  { label: "19:00 - 21:00", start: "19:00", end: "21:00" },
  { label: "21:00 - 23:00", start: "21:00", end: "23:00" },
] as const;

// ------------------------------------------------------------------
// Precision card definitions
// ------------------------------------------------------------------
type PrecisionCard = "PRECISE" | "TWO_HOUR_SLOT" | "FUZZY_DAY" | "UNKNOWN";

interface CardDef {
  id: PrecisionCard;
  icon: string;
  title: string;
  subtitle: string;
  color: string;
  confidence: string;
}

const PRECISION_CARDS: CardDef[] = [
  {
    id: "PRECISE",
    icon: "verified",
    title: "我有精確時間",
    subtitle: "出生證明或家人確認",
    color: "#d4af37",
    confidence: "黃金級 · 最高精準",
  },
  {
    id: "TWO_HOUR_SLOT",
    icon: "timelapse",
    title: "我知道大概時段",
    subtitle: "約兩小時的範圍",
    color: "#9e9e9e",
    confidence: "白銀級 · 中等精準",
  },
  {
    id: "FUZZY_DAY",
    icon: "wb_twilight",
    title: "我只知道大概",
    subtitle: "早上、下午或晚上",
    color: "#cd7f32",
    confidence: "青銅+級 · 可校正",
  },
  {
    id: "UNKNOWN",
    icon: "help",
    title: "我完全不知道",
    subtitle: "沒關係，我們會幫你找到",
    color: "#8c7089",
    confidence: "青銅級 · 可校正",
  },
];

// ------------------------------------------------------------------
// Style helpers
// ------------------------------------------------------------------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

// ------------------------------------------------------------------
// Sub-components
// ------------------------------------------------------------------

function PrecisionCardButton({
  card,
  selected,
  onClick,
}: {
  card: CardDef;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left rounded-2xl p-4 transition-all duration-200 relative overflow-hidden"
      style={{
        background: selected
          ? `linear-gradient(135deg, ${card.color}20, ${card.color}10)`
          : "rgba(255,255,255,0.45)",
        border: selected ? `1.5px solid ${card.color}60` : "1.5px solid rgba(255,255,255,0.6)",
        boxShadow: selected ? `0 4px 16px ${card.color}20` : "none",
      }}
      aria-pressed={selected}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: `${card.color}18` }}
        >
          <span
            className="material-symbols-outlined text-xl"
            style={{
              color: card.color,
              fontVariationSettings: "'FILL' 1, 'wght' 400",
            }}
            aria-hidden="true"
          >
            {card.icon}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-semibold text-[#5c4059]"
            style={selected ? { color: card.color } : undefined}
          >
            {card.title}
          </p>
          <p className="text-[11px] text-[#8c7089] mt-0.5">{card.subtitle}</p>
        </div>
        {selected && (
          <span
            className="material-symbols-outlined text-base shrink-0"
            style={{ color: card.color, fontVariationSettings: "'FILL' 1" }}
            aria-hidden="true"
          >
            check_circle
          </span>
        )}
      </div>
      {selected && (
        <p className="mt-2 ml-13 text-[10px] font-medium" style={{ color: card.color }}>
          {card.confidence}
        </p>
      )}
    </button>
  );
}

function FuzzyPeriodGrid({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (p: string) => void;
}) {
  const periods = [
    { id: "morning",   label: "早上", range: "06:00 - 12:00", icon: "wb_sunny" },
    { id: "afternoon", label: "下午", range: "12:00 - 18:00", icon: "light_mode" },
    { id: "evening",   label: "晚上", range: "18:00 - 24:00", icon: "nights_stay" },
  ];

  return (
    <div className="grid grid-cols-3 gap-2 mt-3" role="radiogroup" aria-label="出生時段">
      {periods.map((p) => (
        <button
          key={p.id}
          type="button"
          role="radio"
          aria-checked={selected === p.id}
          onClick={() => onSelect(p.id)}
          className="flex flex-col items-center gap-1 p-3 rounded-2xl transition-all duration-200"
          style={{
            background: selected === p.id
              ? "linear-gradient(135deg, rgba(217,134,149,0.18), rgba(247,197,168,0.12))"
              : "rgba(255,255,255,0.4)",
            border: selected === p.id
              ? "1.5px solid rgba(217,134,149,0.5)"
              : "1.5px solid rgba(255,255,255,0.6)",
          }}
        >
          <span
            className="material-symbols-outlined text-xl"
            style={{
              color: selected === p.id ? "#d98695" : "#8c7089",
              fontVariationSettings: "'FILL' 1, 'wght' 400",
            }}
            aria-hidden="true"
          >
            {p.icon}
          </span>
          <span
            className="text-sm font-semibold"
            style={{ color: selected === p.id ? "#d98695" : "#5c4059" }}
          >
            {p.label}
          </span>
          <span className="text-[10px] text-[#8c7089]">{p.range}</span>
        </button>
      ))}
    </div>
  );
}

function TwoHourSlotGrid({
  selected,
  onSelect,
}: {
  selected: string;
  onSelect: (slot: { start: string; end: string }) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-1.5 mt-3" role="radiogroup" aria-label="出生時段 (2小時)">
      {TWO_HOUR_SLOTS.map((slot) => {
        const isSelected = selected === slot.label;
        return (
          <button
            key={slot.label}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onSelect({ start: slot.start, end: slot.end })}
            className="py-2 px-1 rounded-xl text-[11px] font-medium text-center transition-all duration-200"
            style={{
              background: isSelected
                ? "linear-gradient(135deg, rgba(158,158,158,0.25), rgba(158,158,158,0.12))"
                : "rgba(255,255,255,0.4)",
              border: isSelected
                ? "1.5px solid rgba(158,158,158,0.6)"
                : "1.5px solid rgba(255,255,255,0.6)",
              color: isSelected ? "#5c4059" : "#8c7089",
            }}
          >
            {slot.label}
          </button>
        );
      })}
    </div>
  );
}

// ------------------------------------------------------------------
// Page component
// ------------------------------------------------------------------
export default function BirthDataPage() {
  const router = useRouter();

  const [birthDate, setBirthDate] = useState("");
  const [birthPlace, setBirthPlace] = useState("");
  const [selectedCard, setSelectedCard] = useState<PrecisionCard | null>(null);
  const [preciseTime, setPreciseTime] = useState("");
  const [fuzzyPeriod, setFuzzyPeriod] = useState("");
  const [twoHourSlot, setTwoHourSlot] = useState<{ label: string; start: string; end: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isSubSelectionComplete = (): boolean => {
    if (!selectedCard) return false;
    if (selectedCard === "PRECISE") return preciseTime.length > 0;
    if (selectedCard === "TWO_HOUR_SLOT") return twoHourSlot !== null;
    if (selectedCard === "FUZZY_DAY") return fuzzyPeriod.length > 0;
    return true; // UNKNOWN — no sub-selection needed
  };

  const isValid = birthDate.length > 0 && birthPlace.length > 0 && isSubSelectionComplete();

  async function handleSubmit() {
    setError("");
    setLoading(true);
    try {
      const selectedCity = TAIWAN_CITIES.find((c) => c.name === birthPlace);

      // Build payload based on selected card
      let payload: Record<string, unknown> = {
        birth_date: birthDate,
        birth_city: birthPlace,
        birth_lat: selectedCity?.lat,
        birth_lng: selectedCity?.lng,
      };

      if (selectedCard === "PRECISE") {
        payload = { ...payload, accuracy_type: "PRECISE", birth_time_exact: preciseTime };
      } else if (selectedCard === "TWO_HOUR_SLOT") {
        payload = {
          ...payload,
          accuracy_type: "TWO_HOUR_SLOT",
          window_start: twoHourSlot!.start,
          window_end: twoHourSlot!.end,
        };
      } else if (selectedCard === "FUZZY_DAY") {
        payload = { ...payload, accuracy_type: "FUZZY_DAY", fuzzy_period: fuzzyPeriod };
      } else {
        // UNKNOWN → FUZZY_DAY with no period
        payload = { ...payload, accuracy_type: "FUZZY_DAY" };
      }

      const res = await fetch("/api/onboarding/birth-data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
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
  }

  return (
    <div className="flex flex-col gap-6 py-4">
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
          <span style={gradientText} className="font-semibold">你的硬體規格</span>
        </h1>
        <p className="text-sm text-[#8c7089] font-light leading-relaxed">
          Stars remember the moment you arrived.
        </p>
      </header>

      {/* ---- Base fields: date + city ---- */}
      <section className="glass-panel rounded-3xl p-6 space-y-5 border border-white/50" aria-label="出生基本資料">
        {/* Date */}
        <div className="space-y-2">
          <label
            htmlFor="birth-date"
            className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]"
          >
            <span className="material-symbols-outlined text-base text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }} aria-hidden="true">calendar_today</span>
            出生日期
          </label>
          <input
            id="birth-date"
            type="date"
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            max={new Date().toISOString().split("T")[0]}
            className="w-full px-4 py-3 rounded-2xl glass-panel border border-white/60 text-[#5c4059] text-sm font-medium outline-none focus:border-primary/50 focus:shadow-[0_0_0_3px_rgba(217,134,149,0.12)] transition-all duration-200 bg-transparent"
            aria-required="true"
          />
        </div>

        {/* City */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]">
            <span className="material-symbols-outlined text-base text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }} aria-hidden="true">location_on</span>
            出生地點
          </label>
          <Select value={birthPlace} onValueChange={setBirthPlace}>
            <SelectTrigger className="w-full px-4 py-3 rounded-2xl glass-panel border border-white/60 text-[#5c4059] text-sm font-medium bg-transparent h-auto cursor-pointer focus:border-primary/50 focus:ring-[3px] focus:ring-[rgba(217,134,149,0.12)]">
              <SelectValue placeholder="選擇出生城市…" />
            </SelectTrigger>
            <SelectContent className="max-h-60">
              {TAIWAN_CITIES.map((city) => (
                <SelectItem key={city.name} value={city.name}>{city.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </section>

      {/* ---- Precision cards ---- */}
      <section className="space-y-3" aria-label="出生時間精確度">
        <h2 className="text-xs font-semibold tracking-widest uppercase text-[#5c4059] flex items-center gap-2 px-1">
          <span className="material-symbols-outlined text-base text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }} aria-hidden="true">schedule</span>
          你對出生時間的了解程度？
        </h2>

        <div className="space-y-2" role="radiogroup" aria-label="選擇出生時間精確度">
          {PRECISION_CARDS.map((card) => (
            <PrecisionCardButton
              key={card.id}
              card={card}
              selected={selectedCard === card.id}
              onClick={() => {
                setSelectedCard(card.id);
                // Reset sub-selections when switching cards
                setPreciseTime("");
                setFuzzyPeriod("");
                setTwoHourSlot(null);
              }}
            />
          ))}
        </div>
      </section>

      {/* ---- Sub-selection panel ---- */}
      {selectedCard === "PRECISE" && (
        <section className="glass-panel rounded-2xl p-5 border border-[#d4af37]/30 space-y-3" style={{ animation: "fadeSlideIn 0.2s ease-out both" }} aria-label="精確時間輸入">
          <label htmlFor="precise-time" className="flex items-center gap-2 text-xs font-semibold tracking-widest uppercase text-[#5c4059]">
            <span className="material-symbols-outlined text-base" style={{ color: "#d4af37", fontVariationSettings: "'FILL' 1, 'wght' 400" }} aria-hidden="true">workspace_premium</span>
            精確出生時刻
          </label>
          <input
            id="precise-time"
            type="time"
            value={preciseTime}
            onChange={(e) => setPreciseTime(e.target.value)}
            className="w-full px-4 py-3 rounded-2xl glass-panel border text-[#5c4059] text-sm font-medium outline-none transition-all duration-200 bg-transparent"
            style={{ borderColor: "rgba(212,175,55,0.4)" }}
            aria-required="true"
          />
          <p className="text-[10px] text-[#8c7089]">精確出生時間可解鎖完整上升星座與 D9 星盤分析</p>
        </section>
      )}

      {selectedCard === "TWO_HOUR_SLOT" && (
        <section className="glass-panel rounded-2xl p-5 border border-white/50 space-y-2" style={{ animation: "fadeSlideIn 0.2s ease-out both" }} aria-label="選擇兩小時時段">
          <p className="text-xs font-semibold tracking-widest uppercase text-[#5c4059]">選擇最接近的時段</p>
          <TwoHourSlotGrid
            selected={twoHourSlot?.label ?? ""}
            onSelect={(slot) => setTwoHourSlot({ label: TWO_HOUR_SLOTS.find(s => s.start === slot.start)?.label ?? "", ...slot })}
          />
        </section>
      )}

      {selectedCard === "FUZZY_DAY" && (
        <section className="glass-panel rounded-2xl p-5 border border-white/50 space-y-2" style={{ animation: "fadeSlideIn 0.2s ease-out both" }} aria-label="選擇出生時段">
          <p className="text-xs font-semibold tracking-widest uppercase text-[#5c4059]">大概是哪個時段？</p>
          <FuzzyPeriodGrid selected={fuzzyPeriod} onSelect={setFuzzyPeriod} />
        </section>
      )}

      {selectedCard === "UNKNOWN" && (
        <div className="glass-panel rounded-2xl p-4 border border-white/40 flex items-start gap-3" style={{ animation: "fadeSlideIn 0.2s ease-out both" }}>
          <span className="material-symbols-outlined text-xl text-[#8c7089] shrink-0 mt-0.5" aria-hidden="true">auto_fix_high</span>
          <div>
            <p className="text-sm font-medium text-[#5c4059]">沒關係</p>
            <p className="text-xs text-[#8c7089] mt-0.5 leading-relaxed">完成註冊後，我們會透過幾道問題幫你逐步校正星盤，精準度會隨時間提升。</p>
          </div>
        </div>
      )}

      {/* ---- Error ---- */}
      {error && (
        <p className="text-xs text-center py-2 px-3 rounded-lg bg-red-50/80" style={{ color: "#e74c3c" }} role="alert">
          {error}
        </p>
      )}

      {/* ---- CTA ---- */}
      <div className="flex flex-col items-center gap-3">
        <button
          type="button"
          disabled={!isValid || loading}
          onClick={handleSubmit}
          className={
            "w-full max-w-sm flex items-center justify-center gap-2 px-8 py-4 rounded-full " +
            "font-medium text-white text-sm transition-all duration-300 " +
            (isValid && !loading
              ? "shadow-[0_8px_30px_rgba(217,134,149,0.45)] hover:shadow-[0_12px_40px_rgba(217,134,149,0.65)] hover:-translate-y-0.5"
              : "opacity-40 cursor-not-allowed")
          }
          style={{ background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)" }}
          aria-label="Continue to next step"
        >
          <span>{loading ? "Saving..." : "Continue"}</span>
          <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }} aria-hidden="true">arrow_forward</span>
        </button>
        <p className="text-[10px] text-[#8c7089]/70 text-center">你的出生數據採 AES-256 加密儲存，永不對外分享。</p>
      </div>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
