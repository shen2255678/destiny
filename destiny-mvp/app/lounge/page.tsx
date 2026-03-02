"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { BirthInput, type BirthData } from "@/components/BirthInput";
import { createClient } from "@/lib/supabase/client";

const YinYangCollision = dynamic(
  () => import("@/components/YinYangCollision"),
  { ssr: false }
);

const DEFAULT_A: BirthData = {
  name: "Person A",
  birth_date: "1990-03-15",
  birth_time: "14:30",
  lat: 25.033,
  lng: 121.565,
  data_tier: 1,
  gender: "M",
};

const DEFAULT_B: BirthData = {
  name: "Person B",
  birth_date: "1992-08-22",
  birth_time: "09:15",
  lat: 25.033,
  lng: 121.565,
  data_tier: 1,
  gender: "F",
};


interface SavedProfile {
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
  lat: number;
  lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang: string;
  natal_cache: Record<string, unknown> | null;
}

function ProfilePicker({
  profiles,
  onSelect,
}: {
  profiles: SavedProfile[];
  onSelect: (p: SavedProfile) => void;
}) {
  if (profiles.length === 0) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <select
        defaultValue=""
        onChange={(e) => {
          const p = profiles.find((x) => x.id === e.target.value);
          if (p) onSelect(p);
        }}
        style={{
          width: "100%", padding: "6px 10px", borderRadius: 10,
          border: "1px solid rgba(255,255,255,0.6)",
          background: "rgba(255,255,255,0.5)",
          fontSize: 12, color: "#5c4059", cursor: "pointer",
        }}
      >
        <option value="">── 從已儲存命盤選取 ──</option>
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>{p.display_name}</option>
        ))}
      </select>
    </div>
  );
}

export default function LoungePage() {
  const router = useRouter();
  const [a, setA] = useState<BirthData>(DEFAULT_A);
  const [b, setB] = useState<BirthData>(DEFAULT_B);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [apiDone, setApiDone] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<SavedProfile[]>([]);
  const [saving, setSaving] = useState<null | "A" | "B">(null);
  const [saveLabel, setSaveLabel] = useState("");
  const [saveStatus, setSaveStatus] = useState("");

  useEffect(() => {
    fetch("/api/profiles")
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setProfiles(data); })
      .catch(() => {});
  }, []);

  async function runMatch() {
    setLoading(true);
    setError("");
    setStatus("⟳ 解析命盤與命運共振中...");

    try {
      // Single enriched call: charts + ZWDS + match + profiles + prompts
      const enrichedRes = await fetch("/api/compute-enriched", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          person_a: {
            birth_date: a.birth_date,
            birth_time: a.birth_time || null,
            gender: a.gender,
            lat: a.lat,
            lng: a.lng,
          },
          person_b: {
            birth_date: b.birth_date,
            birth_time: b.birth_time || null,
            gender: b.gender,
            lat: b.lat,
            lng: b.lng,
          },
        }),
      });

      const dto = (await enrichedRes.json()) as Record<string, unknown>;
      if (dto.error) throw new Error(dto.error as string);
      if (!enrichedRes.ok) throw new Error(`astro-service ${enrichedRes.status}`);

      setStatus("⟳ 儲存報告...");

      // Extract scores from enriched DTO
      const scores = (dto.scores as Record<string, unknown>) ?? {};
      const lust = Math.round((scores.lust as number) ?? 50);
      const soul = Math.round((scores.soul as number) ?? 50);
      const harmony = Math.round((scores.harmony as number) ?? (lust + soul) / 2);
      const tracks = (scores.tracks as Record<string, unknown>) ?? {};
      const tagsZh = (dto.tags_zh as Record<string, unknown>) ?? {};
      const labels = (tagsZh.labels as string[]) ?? (dto.labels as string[]) ?? [];

      // Save to Supabase
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();

      const { data: match, error: dbErr } = await supabase
        .from("mvp_matches")
        .insert({
          user_id: user!.id,
          name_a: a.name,
          name_b: b.name,
          harmony_score: harmony,
          lust_score: lust,
          soul_score: soul,
          tracks,
          labels,
          report_json: dto,
        })
        .select("id")
        .single();

      if (dbErr) throw new Error(dbErr.message);

      setReportId(match.id);
      setApiDone(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error occurred");
      setLoading(false);
      setApiDone(false);
      setReportId(null);
      setStatus("");
    }
  }

  return (
    <main
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "32px 24px",
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 700,
            letterSpacing: "0.1em",
            color: "#5c4059",
            marginBottom: 6,
          }}
        >
          ✦ 命運解析大廳
        </h1>
        <p style={{ color: "#8c7089", fontSize: 13 }}>
          輸入雙方生辰資料，解析靈魂共振與命運交集
        </p>
      </header>

      {/* Two-column input grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
          marginBottom: 28,
        }}
      >
        {/* Person A */}
        <div>
          <ProfilePicker
            profiles={profiles}
            onSelect={(p) => {
              setA({
                name: p.display_name,
                birth_date: p.birth_date,
                birth_time: p.birth_time?.slice(0, 5) ?? "",
                lat: p.lat,
                lng: p.lng,
                data_tier: p.data_tier,
                gender: p.gender,
              });
            }}
          />
          <BirthInput
            label="A"
            value={a}
            onChange={setA}
          />
          <div style={{ marginTop: 8, textAlign: "right" }}>
            {saving === "A" ? (
              <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "flex-end" }}>
                <input
                  value={saveLabel}
                  onChange={(e) => setSaveLabel(e.target.value)}
                  placeholder="幫這個命盤取個名字"
                  style={{
                    padding: "5px 10px", borderRadius: 8,
                    border: "1px solid rgba(255,255,255,0.6)",
                    background: "rgba(255,255,255,0.5)",
                    fontSize: 12, color: "#5c4059", width: 160,
                  }}
                />
                <button
                  onClick={async () => {
                    setSaveStatus("儲存中...");
                    const res = await fetch("/api/profiles", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        label: saveLabel || a.name,
                        birth_date: a.birth_date,
                        birth_time: a.birth_time || undefined,
                        lat: a.lat, lng: a.lng,
                        data_tier: a.data_tier, gender: a.gender,
                      }),
                    });
                    if (res.status === 403) { setSaveStatus("❌ 免費方案限 1 張，升級解鎖更多"); setSaving(null); return; }
                    if (!res.ok) { setSaveStatus("❌ 儲存失敗"); setSaving(null); return; }
                    const saved = await res.json() as SavedProfile;
                    setProfiles((prev) => [saved, ...prev]);
                    setSaving(null); setSaveLabel(""); setSaveStatus("✓ 已儲存");
                    setTimeout(() => setSaveStatus(""), 3000);
                  }}
                  style={{ padding: "5px 12px", borderRadius: 8, background: "#d98695", color: "#fff", border: "none", fontSize: 12, cursor: "pointer" }}
                >確認</button>
                <button
                  onClick={() => { setSaving(null); setSaveLabel(""); }}
                  style={{ padding: "5px 10px", borderRadius: 8, background: "transparent", border: "1px solid rgba(200,160,170,0.4)", fontSize: 12, color: "#8c7089", cursor: "pointer" }}
                >取消</button>
              </div>
            ) : (
              <button
                onClick={() => { setSaving("A"); setSaveLabel(""); }}
                style={{ fontSize: 11, color: "#8c7089", background: "transparent", border: "none", cursor: "pointer", padding: "4px 0" }}
              >💾 儲存此命盤</button>
            )}
          </div>
        </div>

        {/* Person B */}
        <div>
          <ProfilePicker
            profiles={profiles}
            onSelect={(p) => {
              setB({
                name: p.display_name,
                birth_date: p.birth_date,
                birth_time: p.birth_time?.slice(0, 5) ?? "",
                lat: p.lat,
                lng: p.lng,
                data_tier: p.data_tier,
                gender: p.gender,
              });
            }}
          />
          <BirthInput
            label="B"
            value={b}
            onChange={setB}
          />
          <div style={{ marginTop: 8, textAlign: "right" }}>
            {saving === "B" ? (
              <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "flex-end" }}>
                <input
                  value={saveLabel}
                  onChange={(e) => setSaveLabel(e.target.value)}
                  placeholder="幫這個命盤取個名字"
                  style={{
                    padding: "5px 10px", borderRadius: 8,
                    border: "1px solid rgba(255,255,255,0.6)",
                    background: "rgba(255,255,255,0.5)",
                    fontSize: 12, color: "#5c4059", width: 160,
                  }}
                />
                <button
                  onClick={async () => {
                    setSaveStatus("儲存中...");
                    const res = await fetch("/api/profiles", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        label: saveLabel || b.name,
                        birth_date: b.birth_date,
                        birth_time: b.birth_time || undefined,
                        lat: b.lat, lng: b.lng,
                        data_tier: b.data_tier, gender: b.gender,
                      }),
                    });
                    if (res.status === 403) { setSaveStatus("❌ 免費方案限 1 張，升級解鎖更多"); setSaving(null); return; }
                    if (!res.ok) { setSaveStatus("❌ 儲存失敗"); setSaving(null); return; }
                    const saved = await res.json() as SavedProfile;
                    setProfiles((prev) => [saved, ...prev]);
                    setSaving(null); setSaveLabel(""); setSaveStatus("✓ 已儲存");
                    setTimeout(() => setSaveStatus(""), 3000);
                  }}
                  style={{ padding: "5px 12px", borderRadius: 8, background: "#d98695", color: "#fff", border: "none", fontSize: 12, cursor: "pointer" }}
                >確認</button>
                <button
                  onClick={() => { setSaving(null); setSaveLabel(""); }}
                  style={{ padding: "5px 10px", borderRadius: 8, background: "transparent", border: "1px solid rgba(200,160,170,0.4)", fontSize: 12, color: "#8c7089", cursor: "pointer" }}
                >取消</button>
              </div>
            ) : (
              <button
                onClick={() => { setSaving("B"); setSaveLabel(""); }}
                style={{ fontSize: 11, color: "#8c7089", background: "transparent", border: "none", cursor: "pointer", padding: "4px 0" }}
              >💾 儲存此命盤</button>
            )}
          </div>
        </div>
      </div>

      {saveStatus && (
        <p style={{ fontSize: 12, color: saveStatus.startsWith("✓") ? "#34d399" : "#c0392b", marginBottom: 8 }}>
          {saveStatus}
        </p>
      )}

      {/* Error display */}
      {error ? (
        <div
          style={{
            background: "rgba(231,76,60,0.08)",
            border: "1px solid rgba(231,76,60,0.25)",
            borderRadius: 12,
            padding: "10px 16px",
            marginBottom: 20,
            color: "#c0392b",
            fontSize: 13,
          }}
        >
          ✕ {error}
        </div>
      ) : null}

      {/* Submit button */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <button
          onClick={runMatch}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(217,134,149,0.4)"
              : "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            color: "#ffffff",
            border: "none",
            padding: "12px 32px",
            borderRadius: 999,
            fontSize: 14,
            fontWeight: 600,
            letterSpacing: "0.05em",
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: loading
              ? "none"
              : "0 4px 14px rgba(217,134,149,0.35)",
            transition: "all 0.2s",
          }}
        >
          {loading ? (status || "⟳ 運算中...") : "✦ 解析命運"}
        </button>

        {loading ? (
          <span style={{ color: "#8c7089", fontSize: 12 }}>
            星盤運算約需 5-10 秒，請稍候…
          </span>
        ) : null}
      </div>

      <YinYangCollision
        active={loading}
        resolved={apiDone}
        onExitComplete={() => {
          if (reportId) {
            router.push(`/report/${reportId}`);
          }
          setLoading(false);
          setApiDone(false);
          setReportId(null);
        }}
      />
    </main>
  );
}
