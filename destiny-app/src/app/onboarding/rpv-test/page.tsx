"use client";

// ============================================================
// DESTINY — Onboarding Step 2: RPV Test
// 你的作業系統 — "Your Operating System"
// Next.js 14 App Router · Tailwind CSS v4 · Client Component
// ============================================================

import { useState } from "react";
import { useRouter } from "next/navigation";

// ------------------------------------------------------------------
// Question / option data
// ------------------------------------------------------------------
interface Option {
  id: string;
  label: string;
  sublabel: string;
  icon: string;
}

interface Question {
  id: number;
  chinese: string;
  english: string;
  options: [Option, Option];
}

const questions: Question[] = [
  {
    id: 1,
    chinese: "吵架的時候，你傾向…",
    english: "When you argue, you tend to...",
    options: [
      {
        id: "1A",
        label: "冷處理",
        sublabel: "需要空間",
        icon: "ac_unit",
      },
      {
        id: "1B",
        label: "直接溝通",
        sublabel: "當面解決",
        icon: "record_voice_over",
      },
    ],
  },
  {
    id: 2,
    chinese: "在關係中，你比較喜歡…",
    english: "In relationships, you prefer to...",
    options: [
      {
        id: "2A",
        label: "掌控大局",
        sublabel: "做決定",
        icon: "shield_person",
      },
      {
        id: "2B",
        label: "配合對方",
        sublabel: "享受被帶領",
        icon: "diversity_1",
      },
    ],
  },
  {
    id: 3,
    chinese: "理想的週末是…",
    english: "Your ideal weekend is...",
    options: [
      {
        id: "3A",
        label: "在家追劇",
        sublabel: "看書、充電",
        icon: "cottage",
      },
      {
        id: "3B",
        label: "出去社交",
        sublabel: "探索新地方",
        icon: "explore",
      },
    ],
  },
];

// ------------------------------------------------------------------
// Inline style helpers
// ------------------------------------------------------------------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

// ------------------------------------------------------------------
// Option card sub-component
// ------------------------------------------------------------------
interface OptionCardProps {
  option: Option;
  isSelected: boolean;
  onSelect: () => void;
}

function OptionCard({ option, isSelected, onSelect }: OptionCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
      className={
        "flex-1 flex flex-col items-center gap-3 p-5 rounded-2xl glass-panel " +
        "border-2 transition-all duration-250 cursor-pointer text-center " +
        "hover:-translate-y-0.5 active:scale-[0.98] " +
        (isSelected
          ? "border-primary shadow-[0_0_0_3px_rgba(217,134,149,0.2),0_8px_24px_rgba(217,134,149,0.3)] bg-primary/8"
          : "border-white/60 hover:border-primary/40 hover:shadow-[0_4px_16px_rgba(217,134,149,0.15)]")
      }
    >
      {/* Icon */}
      <span
        className="material-symbols-outlined text-3xl transition-colors duration-200"
        style={{
          fontVariationSettings: isSelected ? "'FILL' 1, 'wght' 400" : "'FILL' 0, 'wght' 300",
          color: isSelected ? "#d98695" : "#8c7089",
        }}
        aria-hidden="true"
      >
        {option.icon}
      </span>

      {/* Labels */}
      <div>
        <p
          className="text-sm font-semibold leading-tight transition-colors duration-200"
          style={{ color: isSelected ? "#d98695" : "#5c4059" }}
        >
          {option.label}
        </p>
        <p className="text-[11px] text-[#8c7089] mt-0.5">{option.sublabel}</p>
      </div>

      {/* Selection indicator dot */}
      <div
        className={
          "w-4 h-4 rounded-full border-2 transition-all duration-200 " +
          (isSelected
            ? "border-primary bg-primary"
            : "border-[#8c7089]/30 bg-transparent")
        }
        aria-hidden="true"
      >
        {isSelected && (
          <span
            className="material-symbols-outlined text-[10px] text-white flex items-center justify-center w-full h-full leading-none"
            style={{ fontVariationSettings: "'FILL' 1, 'wght' 700" }}
          >
            check
          </span>
        )}
      </div>
    </button>
  );
}

// ------------------------------------------------------------------
// Page component
// ------------------------------------------------------------------
// Map option IDs to DB values
const optionMap: Record<string, { field: string; value: string }> = {
  "1A": { field: "rpv_conflict", value: "cold_war" },
  "1B": { field: "rpv_conflict", value: "argue" },
  "2A": { field: "rpv_power", value: "control" },
  "2B": { field: "rpv_power", value: "follow" },
  "3A": { field: "rpv_energy", value: "home" },
  "3B": { field: "rpv_energy", value: "out" },
};

export default function RpvTestPage() {
  const router = useRouter();
  const [selections, setSelections] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totalAnswered = Object.keys(selections).length;
  const allAnswered = totalAnswered === questions.length;

  function handleSelect(questionId: number, optionId: string) {
    setSelections((prev) => ({ ...prev, [questionId]: optionId }));
  }

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
            psychology
          </span>
          <span className="text-[10px] font-medium tracking-widest uppercase text-[#8c7089]">
            Step 2 of 4
          </span>
        </div>

        <h1 className="text-3xl font-sans font-light text-[#5c4059]">
          <span style={gradientText} className="font-semibold">
            你的作業系統
          </span>
        </h1>
        <p className="text-sm text-[#8c7089] font-light">
          3 questions. No right answers. Only truth.
        </p>
      </header>

      {/* ---- Progress micro-bar ---- */}
      <div
        className="flex gap-1.5"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={questions.length}
        aria-valuenow={totalAnswered}
        aria-label={`已回答 ${totalAnswered} / ${questions.length} 題`}
      >
        {questions.map((q) => (
          <div
            key={q.id}
            className="flex-1 h-1 rounded-full transition-all duration-400"
            style={{
              background: selections[q.id]
                ? "linear-gradient(90deg, #d98695, #f7c5a8)"
                : "rgba(255,255,255,0.4)",
            }}
          />
        ))}
      </div>

      {/* ---- Question cards ---- */}
      <div className="flex flex-col gap-5">
        {questions.map((q, qi) => {
          const isAnswered = !!selections[q.id];

          return (
            <article
              key={q.id}
              className={
                "glass-panel rounded-3xl p-6 border transition-all duration-300 " +
                (isAnswered
                  ? "border-primary/30 shadow-[0_4px_20px_rgba(217,134,149,0.12)]"
                  : "border-white/50")
              }
              aria-label={`Question ${q.id}: ${q.chinese}`}
            >
              {/* Question header */}
              <div className="flex items-baseline gap-2 mb-4">
                <span
                  className="text-xs font-bold tracking-widest text-primary/70"
                  aria-hidden="true"
                >
                  Q{qi + 1}
                </span>
                <div>
                  <p className="text-sm font-semibold text-[#5c4059] leading-snug">
                    {q.chinese}
                  </p>
                  <p className="text-[11px] text-[#8c7089] font-light">
                    {q.english}
                  </p>
                </div>
                {/* Answered checkmark */}
                {isAnswered && (
                  <span
                    className="ml-auto flex-shrink-0 material-symbols-outlined text-base text-primary"
                    style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                    aria-label="已回答"
                  >
                    check_circle
                  </span>
                )}
              </div>

              {/* Options row */}
              <div
                className="flex gap-3"
                role="group"
                aria-label={`${q.chinese} 的選項`}
              >
                {q.options.map((opt) => (
                  <OptionCard
                    key={opt.id}
                    option={opt}
                    isSelected={selections[q.id] === opt.id}
                    onSelect={() => handleSelect(q.id, opt.id)}
                  />
                ))}
              </div>
            </article>
          );
        })}
      </div>

      {/* ---- Note ---- */}
      {allAnswered && (
        <p
          className="text-center text-xs text-[#8c7089] animate-fade-in"
          style={{ animation: "fadeIn 0.4s ease-out both" }}
        >
          你的回答將與對方的動態配對 — 沒有標準答案，只有相性。
        </p>
      )}

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
          disabled={!allAnswered || loading}
          onClick={async () => {
            setError("");
            setLoading(true);
            try {
              // Map selections to DB fields
              const payload: Record<string, string> = {};
              for (const optionId of Object.values(selections)) {
                const mapping = optionMap[optionId];
                if (mapping) payload[mapping.field] = mapping.value;
              }

              const res = await fetch("/api/onboarding/rpv-test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              const json = await res.json();
              if (!res.ok) {
                setError(json.error || "Failed to save RPV results");
                setLoading(false);
                return;
              }
              router.push("/onboarding/photos");
            } catch {
              setError("Network error. Please try again.");
              setLoading(false);
            }
          }}
          className={
            "w-full max-w-sm flex items-center justify-center gap-2 px-8 py-4 rounded-full " +
            "font-medium text-white text-sm transition-all duration-300 " +
            (allAnswered && !loading
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

        {!allAnswered && (
          <p className="text-[10px] text-[#8c7089]/70 text-center">
            請回答全部 {questions.length} 題後繼續
          </p>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
