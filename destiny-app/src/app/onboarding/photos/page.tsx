"use client";

// ============================================================
// DESTINY — Onboarding Step 3: Photos
// 你的視覺門檻 — "Your Visual Threshold"
// Next.js 14 App Router · Tailwind CSS v4 · Client Component
// ============================================================

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";

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
// Upload slot sub-component
// ------------------------------------------------------------------
interface UploadSlotProps {
  index: number;
  file: File | null;
  onUpload: (file: File) => void;
}

function UploadSlot({ index, file, onUpload }: UploadSlotProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const isUploaded = !!file;

  // Generate object URL for preview
  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleClick() {
    inputRef.current?.click();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick();
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  }

  const slotLabel = `Photo ${index + 1}`;

  return (
    <div className="flex flex-col gap-3">
      {/* Upload zone */}
      <button
        type="button"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        aria-label={isUploaded ? `${slotLabel} uploaded — click to change` : `Upload ${slotLabel}`}
        className={
          "relative rounded-3xl overflow-hidden cursor-pointer " +
          "border-2 border-dashed transition-all duration-300 group " +
          "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 " +
          (isUploaded
            ? "border-primary/40 shadow-[0_8px_32px_rgba(217,134,149,0.25)]"
            : "border-[#8c7089]/30 hover:border-primary/50 hover:shadow-[0_4px_20px_rgba(217,134,149,0.15)]")
        }
        style={{ aspectRatio: "3/4" }}
      >
        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="sr-only"
          aria-hidden="true"
          tabIndex={-1}
          onChange={handleFileChange}
        />

        {isUploaded && preview ? (
          /* ---- Uploaded state: show actual photo preview ---- */
          <>
            {/* Actual photo */}
            <img
              src={preview}
              alt={`照片 ${index + 1} 預覽`}
              className="absolute inset-0 w-full h-full object-cover"
            />

            {/* Bottom overlay label */}
            <div className="absolute inset-0 flex flex-col items-center justify-end pb-6 z-10">
              <div className="glass-panel rounded-2xl px-4 py-2.5 border border-white/60 text-center backdrop-blur-md bg-black/20">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <span
                    className="material-symbols-outlined text-sm text-white"
                    style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                    aria-hidden="true"
                  >
                    check_circle
                  </span>
                  <span className="text-xs font-semibold text-white tracking-wide">
                    已選取
                  </span>
                </div>
                <span className="text-[9px] text-white/80">
                  上傳後將自動模糊處理
                </span>
              </div>
            </div>

            {/* Top-right "change" hint on hover */}
            <div
              className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200
                          glass-panel rounded-xl px-2 py-1 border border-white/60 z-20 backdrop-blur-md bg-black/20"
              aria-hidden="true"
            >
              <span className="text-[9px] font-medium text-white">
                變更
              </span>
            </div>
          </>
        ) : (
          /* ---- Empty state: click-to-upload placeholder ---- */
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4">
            {/* Glass icon circle */}
            <div
              className="w-16 h-16 rounded-2xl glass-panel border border-white/60 flex items-center justify-center
                          group-hover:border-primary/40 group-hover:shadow-[0_4px_20px_rgba(217,134,149,0.2)]
                          transition-all duration-300"
            >
              <span
                className="material-symbols-outlined text-3xl text-[#8c7089] group-hover:text-primary transition-colors duration-300"
                style={{ fontVariationSettings: "'FILL' 0, 'wght' 200" }}
                aria-hidden="true"
              >
                add_photo_alternate
              </span>
            </div>

            <div className="text-center">
              <p className="text-xs font-semibold text-[#5c4059] group-hover:text-primary transition-colors duration-200">
                照片 {index + 1}
              </p>
              <p className="text-[10px] text-[#8c7089] mt-0.5">
                點擊上傳 · Click to upload
              </p>
            </div>

            {/* Blur preview chip */}
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full glass-panel border border-white/50">
              <span
                className="material-symbols-outlined text-[11px] text-[#8c7089]"
                style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                aria-hidden="true"
              >
                blur_on
              </span>
              <span className="text-[9px] text-[#8c7089] font-medium">
                高斯模糊
              </span>
            </div>
          </div>
        )}
      </button>

      {/* Slot status label */}
      <div className="flex items-center gap-1.5 justify-center">
        <span
          className="material-symbols-outlined text-sm"
          style={{
            fontVariationSettings: "'FILL' 1, 'wght' 400",
            color: isUploaded ? "#a8e6cf" : "#8c7089",
          }}
          aria-hidden="true"
        >
          {isUploaded ? "check_circle" : "radio_button_unchecked"}
        </span>
        <span className="text-[11px] font-medium text-[#8c7089]">
          {isUploaded ? "已上傳" : "未上傳"}
        </span>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// Page component
// ------------------------------------------------------------------
export default function PhotosPage() {
  const router = useRouter();
  const [files, setFiles] = useState<[File | null, File | null]>([null, null]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const uploaded: [boolean, boolean] = [!!files[0], !!files[1]];

  function handleUpload(index: 0 | 1, file: File) {
    setFiles((prev) => {
      const next: [File | null, File | null] = [...prev] as [File | null, File | null];
      next[index] = file;
      return next;
    });
  }

  const bothUploaded = uploaded[0] && uploaded[1];

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
            photo_camera
          </span>
          <span className="text-[10px] font-medium tracking-widest uppercase text-[#8c7089]">
            Step 3 of 4
          </span>
        </div>

        <h1 className="text-3xl font-sans font-light text-[#5c4059]">
          <span style={gradientText} className="font-semibold">
            你的視覺門檻
          </span>
        </h1>
        <p className="text-sm text-[#8c7089] font-light leading-relaxed max-w-xs mx-auto">
          Upload 2 photos. We&apos;ll blur them — your soul speaks first.
        </p>
      </header>

      {/* ---- Upload grid ---- */}
      <div
        className="grid grid-cols-2 gap-4 sm:gap-6"
        role="group"
        aria-label="照片上傳區域"
      >
        <UploadSlot index={0} file={files[0]} onUpload={(file) => handleUpload(0, file)} />
        <UploadSlot index={1} file={files[1]} onUpload={(file) => handleUpload(1, file)} />
      </div>

      {/* ---- Blur info note ---- */}
      <section
        className="glass-panel rounded-2xl p-4 border border-white/50"
        aria-label="照片處理說明"
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
            <span
              className="material-symbols-outlined text-lg text-primary"
              style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
              aria-hidden="true"
            >
              blur_on
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#5c4059] mb-1">
              照片隱私保護機制
            </p>
            <p className="text-[11px] text-[#8c7089] leading-relaxed">
              照片將自動進行高斯模糊處理，僅保留色調與輪廓。隨著互動深入，照片會逐步清晰。
            </p>
          </div>
        </div>

        {/* Unlock levels */}
        <div className="mt-4 space-y-2" role="list" aria-label="解鎖等級說明">
          {[
            {
              level: "Lv.1",
              desc: "0–10 則訊息 · 高斯模糊",
              color: "#d98695",
              icon: "blur_on",
              blur: "高",
            },
            {
              level: "Lv.2",
              desc: "10–50 則訊息 · 50% 清晰度",
              color: "#8b4a6e",
              icon: "blur_circular",
              blur: "中",
            },
            {
              level: "Lv.3",
              desc: "50+ 則訊息 · 完整高清",
              color: "#3d8b7a",
              icon: "hd",
              blur: "無",
            },
          ].map((tier) => (
            <div
              key={tier.level}
              role="listitem"
              className="flex items-center gap-3"
            >
              <span
                className="text-[10px] font-bold w-8 flex-shrink-0"
                style={{ color: tier.color }}
              >
                {tier.level}
              </span>
              <div
                className="flex-1 h-1 rounded-full"
                style={{
                  background:
                    tier.level === "Lv.1"
                      ? `linear-gradient(90deg, ${tier.color}40, ${tier.color}20)`
                      : tier.level === "Lv.2"
                      ? `linear-gradient(90deg, ${tier.color}70, ${tier.color}30)`
                      : `linear-gradient(90deg, ${tier.color}, ${tier.color}80)`,
                }}
                aria-hidden="true"
              />
              <span className="text-[10px] text-[#8c7089] text-right flex-shrink-0">
                {tier.desc}
              </span>
            </div>
          ))}
        </div>
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
          disabled={!bothUploaded || loading}
          onClick={async () => {
            if (!files[0] || !files[1]) return;
            setError("");
            setLoading(true);
            try {
              const formData = new FormData();
              formData.append("photo1", files[0]);
              formData.append("photo2", files[1]);

              const res = await fetch("/api/onboarding/photos", {
                method: "POST",
                body: formData,
              });
              const json = await res.json();
              if (!res.ok) {
                setError(json.error || "Failed to upload photos");
                setLoading(false);
                return;
              }
              router.push("/onboarding/soul-report");
            } catch {
              setError("Network error. Please try again.");
              setLoading(false);
            }
          }}
          className={
            "w-full max-w-sm flex items-center justify-center gap-2 px-8 py-4 rounded-full " +
            "font-medium text-white text-sm transition-all duration-300 " +
            (bothUploaded && !loading
              ? "shadow-[0_8px_30px_rgba(217,134,149,0.45)] hover:shadow-[0_12px_40px_rgba(217,134,149,0.65)] hover:-translate-y-0.5"
              : "opacity-40 cursor-not-allowed")
          }
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
          }}
          aria-label="Continue to next step"
        >
          <span>{loading ? "Uploading..." : "Continue"}</span>
          <span
            className="material-symbols-outlined text-lg"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
            aria-hidden="true"
          >
            arrow_forward
          </span>
        </button>

        <p className="text-[10px] text-[#8c7089]/70 text-center max-w-xs">
          {bothUploaded
            ? "兩張照片已就緒 · 準備生成你的靈魂原型"
            : `請上傳 ${uploaded.filter(Boolean).length}/2 張照片後繼續`}
        </p>
      </div>
    </div>
  );
}
