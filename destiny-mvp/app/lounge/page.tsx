"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BirthInput, type BirthData } from "@/components/BirthInput";
import { createClient } from "@/lib/supabase/client";

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

// Default RPV values — can be extended to a full form later
const DEFAULT_RPV = {
  rpv_conflict: "argue",
  rpv_power: "follow",
  rpv_energy: "home",
};

export default function LoungePage() {
  const router = useRouter();
  const [a, setA] = useState<BirthData>(DEFAULT_A);
  const [b, setB] = useState<BirthData>(DEFAULT_B);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function runMatch() {
    setLoading((prev) => !prev || true);
    setError("");
    setStatus("⟳ 運算星盤中...");

    try {
      // --- Step 1: Calculate charts in parallel (async-parallel best practice) ---
      const buildChartPayload = (p: BirthData) => ({
        birth_date: p.birth_date,
        birth_time: p.birth_time || null,
        lat: p.lat,
        lng: p.lng,
        data_tier: p.data_tier,
      });

      const [resA, resB] = await Promise.all([
        fetch("/api/calculate-chart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildChartPayload(a)),
        }),
        fetch("/api/calculate-chart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildChartPayload(b)),
        }),
      ]);

      const [chartA, chartB] = await Promise.all([
        resA.json() as Promise<Record<string, unknown>>,
        resB.json() as Promise<Record<string, unknown>>,
      ]);

      if (chartA.error || chartB.error) {
        throw new Error(
          (chartA.error as string) ?? (chartB.error as string)
        );
      }

      setStatus("⟳ 解析命運共振...");

      // --- Step 2: Compute synastry match ---
      const matchRes = await fetch("/api/compute-match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_a: {
            ...chartA,
            gender: a.gender,
            data_tier: a.data_tier,
            ...DEFAULT_RPV,
          },
          user_b: {
            ...chartB,
            gender: b.gender,
            data_tier: b.data_tier,
            ...DEFAULT_RPV,
          },
        }),
      });

      const matchData = (await matchRes.json()) as Record<string, unknown>;
      if (matchData.error) throw new Error(matchData.error as string);

      setStatus("⟳ 儲存報告...");

      // --- Step 3: Save to Supabase ---
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      const lust = Math.round((matchData.lust_score as number) ?? 50);
      const soul = Math.round((matchData.soul_score as number) ?? 50);

      const { data: match, error: dbErr } = await supabase
        .from("mvp_matches")
        .insert({
          user_id: user!.id,
          name_a: a.name,
          name_b: b.name,
          harmony_score: Math.round((lust + soul) / 2),
          lust_score: lust,
          soul_score: soul,
          tracks: (matchData.tracks as Record<string, unknown>) ?? {},
          labels: (matchData.labels as string[]) ?? [],
          report_json: matchData,
        })
        .select("id")
        .single();

      if (dbErr) throw new Error(dbErr.message);

      router.push(`/report/${match.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error occurred");
      setLoading((prev) => prev && false);
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
        <BirthInput label="A" value={a} onChange={setA} />
        <BirthInput label="B" value={b} onChange={setB} />
      </div>

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
    </main>
  );
}
