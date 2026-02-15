"use client";

/**
 * DESTINY — Profile Page (Self-View + Edit)
 * Route: /profile
 *
 * Loads real user data from GET /api/profile/me.
 * Supports editing: display_name, birth data, RPV test, and photos.
 * Archetype and Base Stats are system-generated (read-only).
 */

import Link from "next/link";
import { useEffect, useState, useRef } from "react";

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

interface PhotoRecord {
  id: string;
  storage_path: string;
  blurred_path: string;
  upload_order: number;
}

interface ProfileData {
  display_name: string | null;
  gender: string;
  birth_date: string;
  birth_time: string | null;
  birth_time_exact: string | null;
  birth_city: string;
  data_tier: number;
  rpv_conflict: string | null;
  rpv_power: string | null;
  rpv_energy: string | null;
  sun_sign: string | null;
  moon_sign: string | null;
  venus_sign: string | null;
  archetype_name: string | null;
  archetype_desc: string | null;
  photos: PhotoRecord[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TIER_LABELS: Record<number, { name: string; desc: string }> = {
  1: { name: "Gold Tier", desc: "Precise birth time recorded — full D1 & D9 chart enabled." },
  2: { name: "Silver Tier", desc: "Fuzzy birth time — medium accuracy with fuzzy logic." },
  3: { name: "Bronze Tier", desc: "Birth date only — limited astrology data." },
};

const BIRTH_TIME_OPTIONS = [
  { value: "precise", label: "精確時間" },
  { value: "morning", label: "早上 (6-12)" },
  { value: "afternoon", label: "下午 (12-18)" },
  { value: "unknown", label: "不確定" },
];

const RPV_OPTIONS = {
  conflict: [
    { value: "cold_war", label: "冷處理", icon: "ac_unit" },
    { value: "argue", label: "直接溝通", icon: "record_voice_over" },
  ],
  power: [
    { value: "control", label: "主導掌控", icon: "shield" },
    { value: "follow", label: "配合跟隨", icon: "volunteer_activism" },
  ],
  energy: [
    { value: "home", label: "宅在家", icon: "home" },
    { value: "out", label: "往外跑", icon: "flight_takeoff" },
  ],
};

const TAIWAN_CITIES = [
  "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市",
  "基隆市", "新竹市", "新竹縣", "嘉義市", "嘉義縣", "苗栗縣",
  "彰化縣", "南投縣", "雲林縣", "屏東縣", "宜蘭縣", "花蓮縣",
  "台東縣", "澎湖縣", "金門縣", "連江縣",
];

// ---------------------------------------------------------------------------
// Sub-components (Display)
// ---------------------------------------------------------------------------

function AmbientBlobs() {
  return (
    <>
      <div className="absolute top-[-15%] right-[-10%] w-[55%] h-[55%] rounded-full bg-[#f7c5a8] opacity-25 blur-[100px] pointer-events-none" aria-hidden="true" />
      <div className="absolute bottom-[-5%] left-[-8%] w-[45%] h-[45%] rounded-full bg-[#d98695] opacity-15 blur-[110px] pointer-events-none" aria-hidden="true" />
      <div className="absolute top-[40%] left-[30%] w-[30%] h-[30%] rounded-full bg-[#a8e6cf] opacity-20 blur-[80px] pointer-events-none" aria-hidden="true" />
    </>
  );
}

function TopBar({ dataTier, isEditing, onToggleEdit, saving }: {
  dataTier: number;
  isEditing: boolean;
  onToggleEdit: () => void;
  saving: boolean;
}) {
  const tier = TIER_LABELS[dataTier] || TIER_LABELS[3];
  return (
    <header className="relative z-20 w-full px-6 py-5 flex items-center gap-4" role="banner">
      <Link
        href="/daily"
        className="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200 shrink-0"
        aria-label="Back to Daily Feed"
      >
        <span className="material-symbols-outlined text-xl" aria-hidden="true">arrow_back</span>
      </Link>

      <div className="flex-1 flex flex-col">
        <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] font-medium">Your Source Code</p>
        <h1 className="text-lg font-light text-[#5c4059] tracking-wide leading-tight">My Source Code</h1>
      </div>

      <button
        onClick={onToggleEdit}
        disabled={saving}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200"
        aria-label={isEditing ? "Cancel editing" : "Edit profile"}
      >
        <span className="material-symbols-outlined text-sm" aria-hidden="true">
          {isEditing ? "close" : "edit"}
        </span>
        <span className="text-xs font-medium tracking-wide">
          {isEditing ? "取消" : "編輯"}
        </span>
      </button>

      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel" aria-label={`${tier.name} member`}>
        <span className="text-[#b86e7d] text-xs font-semibold tracking-wider">
          {dataTier === 1 ? "✦ Gold" : dataTier === 2 ? "✦ Silver" : "✦ Bronze"}
        </span>
      </div>
    </header>
  );
}

function ArchetypeCard({ name, desc }: { name: string | null; desc: string | null }) {
  return (
    <section className="glass-panel rounded-3xl p-8 relative overflow-hidden breathing-card transition-all duration-500" aria-labelledby="archetype-title">
      <div className="absolute inset-0 bg-gradient-to-br from-[#fcecf0]/60 via-white/20 to-[#fdf2e9]/40 rounded-3xl pointer-events-none" aria-hidden="true" />
      <div className="absolute -top-8 -right-8 w-40 h-40 rounded-full bg-[#d98695] opacity-10 blur-3xl pointer-events-none" aria-hidden="true" />

      <div className="relative z-10 flex justify-center mb-5">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center shadow-[0_8px_24px_rgba(217,134,149,0.25)]"
          style={{ background: "linear-gradient(135deg, rgba(217,134,149,0.15), rgba(247,197,168,0.15))", border: "1.5px solid rgba(217,134,149,0.3)" }}
          aria-hidden="true"
        >
          <span className="material-symbols-outlined text-4xl" style={{ color: "#d98695" }}>explore</span>
        </div>
      </div>

      <div className="relative z-10 text-center mb-5">
        <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] mb-1">Your Archetype</p>
        <h2 id="archetype-title" className="text-2xl font-light text-[#5c4059] tracking-wide">
          {name || "Decoding..."}
        </h2>
      </div>

      <div className="relative z-10 h-px w-16 mx-auto mb-5 rounded-full" style={{ background: "linear-gradient(90deg, transparent, #d98695, transparent)" }} aria-hidden="true" />

      <p className="relative z-10 text-sm text-[#5c4059]/80 leading-relaxed text-center font-light max-w-md mx-auto">
        {desc || "你的靈魂正在被解碼..."}
      </p>
    </section>
  );
}

function StatBar({ stat }: { stat: BaseStat }) {
  const pct = (stat.level / stat.max) * 100;
  return (
    <div className="space-y-2" role="group" aria-label={`${stat.labelZh} ${stat.labelEn} level ${stat.level} of ${stat.max}`}>
      <div className="flex justify-between items-baseline">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-medium text-[#5c4059]">{stat.labelZh}</span>
          <span className="text-xs text-[#8c7089] font-light">{stat.labelEn}</span>
        </div>
        <span className="text-xs font-semibold tracking-wider" style={{ color: stat.color }} aria-hidden="true">
          Lv.{stat.level} / {stat.max}
        </span>
      </div>
      <div className="relative h-2.5 rounded-full overflow-hidden" style={{ background: "rgba(92,64,89,0.06)" }} role="progressbar" aria-valuenow={stat.level} aria-valuemin={0} aria-valuemax={stat.max}>
        <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${stat.color}99, ${stat.color})`, boxShadow: `0 0 8px ${stat.glowColor}` }} />
        {Array.from({ length: stat.max - 1 }, (_, i) => (
          <div key={i} className="absolute top-0 bottom-0 w-px" style={{ left: `${((i + 1) / stat.max) * 100}%`, background: "rgba(255,255,255,0.6)" }} aria-hidden="true" />
        ))}
      </div>
    </div>
  );
}

function BaseStatsSection({ stats }: { stats: BaseStat[] }) {
  return (
    <section className="glass-panel rounded-2xl p-6 space-y-5" aria-labelledby="stats-heading">
      <div className="flex items-center gap-2 mb-1">
        <span className="material-symbols-outlined text-lg text-[#d98695]" aria-hidden="true">bar_chart</span>
        <h3 id="stats-heading" className="text-xs uppercase tracking-[0.3em] text-[#8c7089] font-medium">Base Stats</h3>
      </div>
      {stats.map((stat) => (
        <StatBar key={stat.labelEn} stat={stat} />
      ))}
    </section>
  );
}

function DataTierCard({ tier }: { tier: number }) {
  const info = TIER_LABELS[tier] || TIER_LABELS[3];
  return (
    <section className="glass-panel rounded-2xl p-5 flex items-center justify-between" aria-label={`Data tier: ${info.name}`}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, #f7c5a8, #d98695)", boxShadow: "0 4px 14px rgba(217,134,149,0.35)" }} aria-hidden="true">
          <span className="material-symbols-outlined text-white text-sm">workspace_premium</span>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[#8c7089] font-medium">Data Tier</p>
          <p className="text-sm font-semibold text-[#5c4059] tracking-wide">{info.name} {tier === 1 ? "✦" : ""}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-[10px] text-[#8c7089] leading-relaxed font-light max-w-[140px]">{info.desc}</p>
      </div>
    </section>
  );
}

function AstroSummaryCard({ items, tier }: { items: AstroItem[]; tier: number }) {
  const tierLabel = tier === 1 ? "Gold" : tier === 2 ? "Silver" : "Bronze";
  return (
    <section className="glass-panel rounded-2xl p-6" aria-labelledby="astro-heading">
      <div className="flex items-center gap-2 mb-5">
        <span className="material-symbols-outlined text-lg text-[#d98695]" aria-hidden="true">auto_awesome</span>
        <h3 id="astro-heading" className="text-xs uppercase tracking-[0.3em] text-[#8c7089] font-medium">Astro Summary</h3>
      </div>
      <div className="grid grid-cols-3 gap-3" role="list">
        {items.map((item) => (
          <div key={item.planet} className="flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-200 hover:bg-white/40 cursor-default" style={{ background: "rgba(255,255,255,0.2)" }} role="listitem" aria-label={`${item.planet}: ${item.sign}`}>
            <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, rgba(217,134,149,0.15), rgba(247,197,168,0.15))", border: "1px solid rgba(217,134,149,0.2)" }} aria-hidden="true">
              <span className="material-symbols-outlined text-base" style={{ color: "#d98695" }}>{item.icon}</span>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-[#8c7089] uppercase tracking-wider font-medium">{item.planet}</p>
              <p className="text-xs text-[#5c4059] font-medium mt-0.5">{item.sign || "—"}</p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-[10px] text-[#8c7089]/70 text-center font-light leading-relaxed">
        Vedic D1 & D9 chart · Tier {tier} {tierLabel} precision
      </p>
    </section>
  );
}

function PrivacyNote() {
  return (
    <aside className="glass-panel rounded-2xl p-4 flex items-start gap-3" role="note">
      <span className="material-symbols-outlined text-base text-[#d98695] shrink-0 mt-0.5" aria-hidden="true">info</span>
      <p className="text-xs text-[#8c7089] leading-relaxed font-light">
        你的原型與基礎數值只有你看得到。其他用戶看到的是根據你們關係動態生成的變色龍標籤。
      </p>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Edit Form Components
// ---------------------------------------------------------------------------

function EditSection({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <section className="glass-panel rounded-2xl p-6 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="material-symbols-outlined text-lg text-[#d98695]" aria-hidden="true">{icon}</span>
        <h3 className="text-xs uppercase tracking-[0.3em] text-[#8c7089] font-medium">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs text-[#8c7089] font-medium tracking-wide">{label}</label>
      {children}
    </div>
  );
}

const inputClass = "w-full px-3 py-2.5 rounded-xl glass-panel border border-white/50 text-sm text-[#5c4059] placeholder:text-[#8c7089]/50 focus:outline-none focus:ring-2 focus:ring-[#d98695]/30 focus:border-[#d98695]/40 transition-all duration-200";
const selectClass = inputClass + " appearance-none bg-white/30";

function OptionPill({ selected, onClick, icon, label }: { selected: boolean; onClick: () => void; icon: string; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 rounded-xl border transition-all duration-200 ${
        selected
          ? "border-[#d98695]/50 bg-[#d98695]/10 text-[#5c4059] shadow-[0_2px_8px_rgba(217,134,149,0.15)]"
          : "border-white/50 glass-panel text-[#8c7089] hover:border-[#d98695]/30"
      }`}
    >
      <span className="material-symbols-outlined text-base" style={{ color: selected ? "#d98695" : "#8c7089" }} aria-hidden="true">{icon}</span>
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Photo Edit Component
// ---------------------------------------------------------------------------

function PhotoEditSection({ photos, onUpload, uploading }: {
  photos: PhotoRecord[];
  onUpload: (files: [File, File]) => void;
  uploading: boolean;
}) {
  const input1Ref = useRef<HTMLInputElement>(null);
  const input2Ref = useRef<HTMLInputElement>(null);
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [preview1, setPreview1] = useState<string | null>(null);
  const [preview2, setPreview2] = useState<string | null>(null);

  useEffect(() => {
    if (!file1) { setPreview1(null); return; }
    const url = URL.createObjectURL(file1);
    setPreview1(url);
    return () => URL.revokeObjectURL(url);
  }, [file1]);

  useEffect(() => {
    if (!file2) { setPreview2(null); return; }
    const url = URL.createObjectURL(file2);
    setPreview2(url);
    return () => URL.revokeObjectURL(url);
  }, [file2]);

  const hasExisting = photos.length > 0;

  return (
    <EditSection title="Photos" icon="photo_camera">
      {hasExisting && !file1 && !file2 && (
        <p className="text-xs text-[#8c7089] font-light">
          已上傳 {photos.length} 張照片。選擇新照片以替換。
        </p>
      )}
      <div className="grid grid-cols-2 gap-4">
        {[0, 1].map((i) => {
          const file = i === 0 ? file1 : file2;
          const preview = i === 0 ? preview1 : preview2;
          const inputRef = i === 0 ? input1Ref : input2Ref;
          const setFile = i === 0 ? setFile1 : setFile2;
          return (
            <button
              key={i}
              type="button"
              onClick={() => inputRef.current?.click()}
              className="aspect-square rounded-2xl glass-panel border border-dashed border-[#d98695]/30 flex flex-col items-center justify-center gap-2 hover:border-[#d98695]/60 hover:bg-white/40 transition-all duration-200 overflow-hidden relative"
            >
              {preview ? (
                <img src={preview} alt={`Photo ${i + 1} preview`} className="absolute inset-0 w-full h-full object-cover" />
              ) : (
                <>
                  <span className="material-symbols-outlined text-2xl text-[#d98695]/50" aria-hidden="true">add_photo_alternate</span>
                  <span className="text-[10px] text-[#8c7089]">照片 {i + 1}</span>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setFile(f);
                }}
              />
            </button>
          );
        })}
      </div>
      {file1 && file2 && (
        <button
          type="button"
          onClick={() => onUpload([file1, file2])}
          disabled={uploading}
          className="w-full py-3 rounded-xl text-sm font-medium text-white tracking-wider shadow-[0_4px_14px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)] transition-all duration-200 disabled:opacity-50"
          style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
        >
          {uploading ? "上傳中..." : "上傳照片"}
        </button>
      )}
      {(file1 && !file2) || (!file1 && file2) ? (
        <p className="text-[10px] text-[#d98695] text-center">請選擇兩張照片後上傳</p>
      ) : null}
    </EditSection>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="min-h-screen flex flex-col relative">
      <AmbientBlobs />
      <div className="relative z-10 flex-1 w-full max-w-lg mx-auto px-4 py-20 flex flex-col items-center justify-center gap-4">
        <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, rgba(217,134,149,0.15), rgba(247,197,168,0.15))", border: "1.5px solid rgba(217,134,149,0.3)" }}>
          <span className="material-symbols-outlined text-3xl text-[#d98695] animate-pulse">hourglass_top</span>
        </div>
        <p className="text-sm text-[#8c7089] font-light animate-pulse">Loading your Source Code...</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Edit form state
  const [editDisplayName, setEditDisplayName] = useState("");
  const [editBirthDate, setEditBirthDate] = useState("");
  const [editBirthTime, setEditBirthTime] = useState("");
  const [editBirthTimeExact, setEditBirthTimeExact] = useState("");
  const [editBirthCity, setEditBirthCity] = useState("");
  const [editRpvConflict, setEditRpvConflict] = useState("");
  const [editRpvPower, setEditRpvPower] = useState("");
  const [editRpvEnergy, setEditRpvEnergy] = useState("");

  // Fetch profile data
  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await fetch("/api/profile/me");
        if (!res.ok) throw new Error("Failed to load profile");
        const json = await res.json();
        setProfile(json.data);
        // Populate edit fields
        const d = json.data;
        setEditDisplayName(d.display_name || "");
        setEditBirthDate(d.birth_date || "");
        setEditBirthTime(d.birth_time || "unknown");
        setEditBirthTimeExact(d.birth_time_exact || "");
        setEditBirthCity(d.birth_city || "");
        setEditRpvConflict(d.rpv_conflict || "");
        setEditRpvPower(d.rpv_power || "");
        setEditRpvEnergy(d.rpv_energy || "");
      } catch {
        setError("無法載入個人資料");
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  function handleToggleEdit() {
    if (isEditing && profile) {
      // Reset edit fields on cancel
      setEditDisplayName(profile.display_name || "");
      setEditBirthDate(profile.birth_date || "");
      setEditBirthTime(profile.birth_time || "unknown");
      setEditBirthTimeExact(profile.birth_time_exact || "");
      setEditBirthCity(profile.birth_city || "");
      setEditRpvConflict(profile.rpv_conflict || "");
      setEditRpvPower(profile.rpv_power || "");
      setEditRpvEnergy(profile.rpv_energy || "");
    }
    setIsEditing(!isEditing);
    setError(null);
    setSuccessMsg(null);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await fetch("/api/profile/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          display_name: editDisplayName || null,
          birth_date: editBirthDate,
          birth_time: editBirthTime,
          birth_time_exact: editBirthTime === "precise" ? editBirthTimeExact : null,
          birth_city: editBirthCity,
          rpv_conflict: editRpvConflict || null,
          rpv_power: editRpvPower || null,
          rpv_energy: editRpvEnergy || null,
        }),
      });
      if (!res.ok) {
        const json = await res.json();
        throw new Error(json.error || "Save failed");
      }
      const json = await res.json();
      setProfile((prev) => prev ? { ...prev, ...json.data } : prev);
      setIsEditing(false);
      setSuccessMsg("已儲存");
      setTimeout(() => setSuccessMsg(null), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "儲存失敗");
    } finally {
      setSaving(false);
    }
  }

  async function handlePhotoUpload(files: [File, File]) {
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("photo1", files[0]);
      formData.append("photo2", files[1]);
      const res = await fetch("/api/profile/me/photos", { method: "POST", body: formData });
      if (!res.ok) {
        const json = await res.json();
        throw new Error(json.error || "Upload failed");
      }
      const json = await res.json();
      setProfile((prev) => prev ? { ...prev, photos: json.data } : prev);
      setSuccessMsg("照片已更新");
      setTimeout(() => setSuccessMsg(null), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "照片上傳失敗");
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <LoadingSkeleton />;
  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[#8c7089]">{error || "無法載入個人資料"}</p>
      </div>
    );
  }

  // Build display data from profile
  const baseStats: BaseStat[] = [
    { labelZh: "激情", labelEn: "Passion", level: 7, max: 10, color: "#d98695", glowColor: "rgba(217,134,149,0.35)" },
    { labelZh: "穩定", labelEn: "Stability", level: 5, max: 10, color: "#a8e6cf", glowColor: "rgba(168,230,207,0.35)" },
    { labelZh: "智識", labelEn: "Intellect", level: 8, max: 10, color: "#f7c5a8", glowColor: "rgba(247,197,168,0.40)" },
  ];

  const astroItems: AstroItem[] = [
    { planet: "Sun", sign: profile.sun_sign || "—", icon: "wb_sunny" },
    { planet: "Moon", sign: profile.moon_sign || "—", icon: "dark_mode" },
    { planet: "Venus", sign: profile.venus_sign || "—", icon: "favorite" },
  ];

  return (
    <div className="min-h-screen flex flex-col relative selection:bg-[#d98695] selection:text-white">
      <AmbientBlobs />
      <TopBar dataTier={profile.data_tier} isEditing={isEditing} onToggleEdit={handleToggleEdit} saving={saving} />

      <main className="relative z-10 flex-1 w-full max-w-lg mx-auto px-4 pb-10 flex flex-col gap-5" role="main" aria-label="My Source Code profile">
        {/* Status messages */}
        {error && (
          <div className="glass-panel rounded-xl p-3 border border-red-200 bg-red-50/50 text-xs text-red-600 text-center">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="glass-panel rounded-xl p-3 border border-emerald-200 bg-emerald-50/50 text-xs text-emerald-600 text-center">
            {successMsg}
          </div>
        )}

        {isEditing ? (
          /* ====== EDIT MODE ====== */
          <>
            {/* Basic Info */}
            <EditSection title="Basic Info" icon="person">
              <FormField label="顯示名稱">
                <input
                  type="text"
                  value={editDisplayName}
                  onChange={(e) => setEditDisplayName(e.target.value)}
                  placeholder="你的名字"
                  className={inputClass}
                />
              </FormField>
            </EditSection>

            {/* Birth Data */}
            <EditSection title="Birth Data" icon="calendar_month">
              <FormField label="出生日期">
                <input
                  type="date"
                  value={editBirthDate}
                  onChange={(e) => setEditBirthDate(e.target.value)}
                  className={inputClass}
                />
              </FormField>
              <FormField label="出生時間精度">
                <select value={editBirthTime} onChange={(e) => setEditBirthTime(e.target.value)} className={selectClass}>
                  {BIRTH_TIME_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </FormField>
              {editBirthTime === "precise" && (
                <FormField label="精確出生時間">
                  <input
                    type="time"
                    value={editBirthTimeExact}
                    onChange={(e) => setEditBirthTimeExact(e.target.value)}
                    className={inputClass}
                  />
                </FormField>
              )}
              <FormField label="出生城市">
                <select value={editBirthCity} onChange={(e) => setEditBirthCity(e.target.value)} className={selectClass}>
                  <option value="">選擇城市</option>
                  {TAIWAN_CITIES.map((city) => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </FormField>
            </EditSection>

            {/* RPV Test */}
            <EditSection title="RPV Test" icon="psychology">
              <FormField label="衝突時傾向">
                <div className="flex gap-3">
                  {RPV_OPTIONS.conflict.map((opt) => (
                    <OptionPill
                      key={opt.value}
                      selected={editRpvConflict === opt.value}
                      onClick={() => setEditRpvConflict(opt.value)}
                      icon={opt.icon}
                      label={opt.label}
                    />
                  ))}
                </div>
              </FormField>
              <FormField label="權力傾向">
                <div className="flex gap-3">
                  {RPV_OPTIONS.power.map((opt) => (
                    <OptionPill
                      key={opt.value}
                      selected={editRpvPower === opt.value}
                      onClick={() => setEditRpvPower(opt.value)}
                      icon={opt.icon}
                      label={opt.label}
                    />
                  ))}
                </div>
              </FormField>
              <FormField label="能量傾向">
                <div className="flex gap-3">
                  {RPV_OPTIONS.energy.map((opt) => (
                    <OptionPill
                      key={opt.value}
                      selected={editRpvEnergy === opt.value}
                      onClick={() => setEditRpvEnergy(opt.value)}
                      icon={opt.icon}
                      label={opt.label}
                    />
                  ))}
                </div>
              </FormField>
            </EditSection>

            {/* Photos */}
            <PhotoEditSection photos={profile.photos} onUpload={handlePhotoUpload} uploading={uploading} />

            {/* Save button */}
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="w-full py-3.5 rounded-xl text-sm font-medium text-white tracking-wider uppercase shadow-[0_4px_14px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)] transition-all duration-200 disabled:opacity-50"
              style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
            >
              {saving ? "儲存中..." : "儲存變更"}
            </button>
          </>
        ) : (
          /* ====== VIEW MODE ====== */
          <>
            <ArchetypeCard name={profile.archetype_name} desc={profile.archetype_desc} />
            <BaseStatsSection stats={baseStats} />
            <DataTierCard tier={profile.data_tier} />
            <AstroSummaryCard items={astroItems} tier={profile.data_tier} />
            <PrivacyNote />
          </>
        )}
      </main>
    </div>
  );
}
