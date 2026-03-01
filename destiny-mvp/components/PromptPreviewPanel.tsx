"use client";

import { useState } from "react";

// ── types ──────────────────────────────────────────────────────────────────
interface LlmReport {
  title?: string;
  one_liner?: string;
  sparks?: string[];
  landmines?: string[];
  advice?: string;
  core?: string;
}

interface PromptPreviewPanelProps {
  reportJson: Record<string, unknown>;
  nameA: string;
  nameB: string;
}

// ── styles ──────────────────────────────────────────────────────────────────
const glass: React.CSSProperties = {
  background: "rgba(255,255,255,0.3)",
  backdropFilter: "blur(12px)",
  WebkitBackdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.5)",
  borderRadius: 16,
  boxShadow: "0 8px 32px rgba(217,134,149,0.08)",
};

const sectionHead: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: "0.12em",
  color: "#8c7089",
  textTransform: "uppercase",
  marginBottom: 8,
};

const pill = (color: string): React.CSSProperties => ({
  display: "inline-block",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 11,
  background: `${color}18`,
  color,
  border: `1px solid ${color}44`,
  margin: "2px 3px 2px 0",
});

// ── helper: render one algorithm section ────────────────────────────────────
function DataRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "6px 0",
        borderBottom: "1px solid rgba(255,255,255,0.4)",
        alignItems: "flex-start",
      }}
    >
      <span
        style={{
          minWidth: 160,
          fontSize: 11,
          color: "#8c7089",
          fontWeight: 600,
          paddingTop: 1,
        }}
      >
        {label}
      </span>
      <span style={{ fontSize: 12, color: "#5c4059", flex: 1 }}>{value}</span>
    </div>
  );
}

// ── main component ───────────────────────────────────────────────────────────
export function PromptPreviewPanel({
  reportJson: r,
  nameA,
  nameB,
}: PromptPreviewPanelProps) {
  const [open, setOpen] = useState(false);
  const [promptText, setPromptText] = useState("");
  const [effectiveMode, setEffectiveMode] = useState("");
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  const [promptError, setPromptError] = useState("");

  // LLM call state
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<"anthropic" | "gemini">("anthropic");
  const [generatingReport, setGeneratingReport] = useState(false);
  const [llmReport, setLlmReport] = useState<LlmReport | null>(null);
  const [llmError, setLlmError] = useState("");

  async function loadPrompt() {
    setLoadingPrompt(true);
    setPromptError("");
    try {
      const res = await fetch("/api/preview-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          match_data: r,
          person_a_name: nameA,
          person_b_name: nameB,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setPromptText(data.prompt);
      setEffectiveMode(data.effective_mode);
    } catch (e) {
      setPromptError(e instanceof Error ? e.message : "error");
    } finally {
      setLoadingPrompt(false);
    }
  }

  async function generateReport() {
    setGeneratingReport(true);
    setLlmError("");
    setLlmReport(null);
    try {
      const res = await fetch("/api/generate-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          match_data: r,
          person_a_name: nameA,
          person_b_name: nameB,
          provider,
          api_key: apiKey,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setLlmReport(data as LlmReport);
    } catch (e) {
      setLlmError(e instanceof Error ? e.message : "error");
    } finally {
      setGeneratingReport(false);
    }
  }

  // Extract fields from reportJson
  const psychTags = (r.psychological_tags as string[]) ?? [];
  const psychTriggers = (r.psychological_triggers as string[]) ?? [];
  const resonanceBadges = (r.resonance_badges as string[]) ?? [];
  const tracks = (r.tracks as Record<string, number>) ?? {};
  const power = (r.power as Record<string, unknown>) ?? {};

  return (
    <div style={{ marginTop: 40 }}>
      {/* Toggle header */}
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "8px 0",
          color: "#8c7089",
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: "0.08em",
        }}
      >
        <span
          style={{
            transform: open ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            display: "inline-block",
          }}
        >
          ▶
        </span>
        開發者工具 — 算法數據 &amp; Prompt 預覽
      </button>

      {open ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 20, marginTop: 12 }}>

          {/* ── Section 1: Algorithm Data ── */}
          <div style={{ ...glass, padding: "20px 24px" }}>
            <p style={sectionHead}>§1 算法輸出數據</p>

            <DataRow label="Quadrant（四象限）" value={String(r.quadrant ?? "—")} />
            <DataRow label="Primary Track（主軌）" value={String(r.primary_track ?? "—")} />
            <DataRow label="Spiciness Level" value={String(r.spiciness_level ?? "—")} />
            <DataRow
              label="High Voltage ⚡"
              value={r.high_voltage ? "✅ YES — 修羅場觸發" : "❌ NO"}
            />
            <DataRow
              label="Karmic Tension（業力張力）"
              value={`${Number(r.karmic_tension ?? 0).toFixed(1)}`}
            />

            <DataRow
              label="四軌分數"
              value={
                <span>
                  朋友 <b>{Math.round(tracks.friend ?? 0)}</b> ·{" "}
                  激情 <b>{Math.round(tracks.passion ?? 0)}</b> ·{" "}
                  伴侶 <b>{Math.round(tracks.partner ?? 0)}</b> ·{" "}
                  靈魂 <b>{Math.round(tracks.soul ?? 0)}</b>
                </span>
              }
            />

            <DataRow
              label="Power（RPV 動力）"
              value={`${nameA}=${power.viewer_role ?? "?"} · ${nameB}=${power.target_role ?? "?"} · RPV=${power.rpv ?? 0} · FrameBreak=${power.frame_break ?? false}`}
            />

            <DataRow
              label="Psychological Tags（陰影標籤）"
              value={
                psychTags.length > 0 ? (
                  <span>
                    {psychTags.map((t) => (
                      <span key={t} style={pill("#b86e7d")}>{t}</span>
                    ))}
                  </span>
                ) : (
                  <span style={{ color: "#aaa" }}>無</span>
                )
              }
            />

            <DataRow
              label="Psychological Triggers（心理觸發）"
              value={
                psychTriggers.length > 0 ? (
                  <span>
                    {psychTriggers.map((t) => (
                      <span key={t} style={pill("#7c3aed")}>{t}</span>
                    ))}
                  </span>
                ) : (
                  <span style={{ color: "#aaa" }}>無</span>
                )
              }
            />

            <DataRow
              label="Resonance Badges（命理認證）"
              value={
                resonanceBadges.length > 0 ? (
                  <span>
                    {resonanceBadges.map((b) => (
                      <span key={b} style={pill("#d97706")}>{b}</span>
                    ))}
                  </span>
                ) : (
                  <span style={{ color: "#aaa" }}>無</span>
                )
              }
            />
          </div>

          {/* ── Section 2: Prompt Preview ── */}
          <div style={{ ...glass, padding: "20px 24px" }}>
            <p style={sectionHead}>§2 LLM Prompt 預覽</p>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 12 }}>
              這是實際會送給 LLM 的 prompt。載入後可直接在文字框中修改後再送出。
            </p>

            {promptText === "" ? (
              <button
                onClick={loadPrompt}
                disabled={loadingPrompt}
                style={{
                  background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
                  color: "#fff",
                  border: "none",
                  padding: "8px 20px",
                  borderRadius: 999,
                  fontSize: 12,
                  cursor: loadingPrompt ? "not-allowed" : "pointer",
                  opacity: loadingPrompt ? 0.6 : 1,
                }}
              >
                {loadingPrompt ? "⟳ 載入中..." : "載入 Prompt"}
              </button>
            ) : null}

            {promptError ? (
              <p style={{ color: "#c0392b", fontSize: 12 }}>✕ {promptError}</p>
            ) : null}

            {promptText ? (
              <>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    marginBottom: 8,
                  }}
                >
                  <span
                    style={{
                      ...pill("#059669"),
                      fontSize: 11,
                    }}
                  >
                    Mode: {effectiveMode}
                  </span>
                  <span style={{ fontSize: 11, color: "#8c7089" }}>
                    {promptText.length} 字元
                  </span>
                  <button
                    onClick={loadPrompt}
                    style={{
                      background: "none",
                      border: "1px solid rgba(217,134,149,0.3)",
                      color: "#d98695",
                      padding: "2px 10px",
                      borderRadius: 999,
                      fontSize: 11,
                      cursor: "pointer",
                    }}
                  >
                    重新載入
                  </button>
                </div>
                <textarea
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  rows={18}
                  style={{
                    width: "100%",
                    background: "rgba(255,255,255,0.6)",
                    border: "1px solid rgba(255,255,255,0.8)",
                    borderRadius: 10,
                    padding: "10px 14px",
                    fontSize: 11,
                    fontFamily: "'Courier New', monospace",
                    color: "#5c4059",
                    lineHeight: 1.6,
                    resize: "vertical",
                    outline: "none",
                  }}
                />
              </>
            ) : null}
          </div>

          {/* ── Section 3: Generate LLM Report ── */}
          <div style={{ ...glass, padding: "20px 24px" }}>
            <p style={sectionHead}>§3 生成 LLM 深度報告</p>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 16 }}>
              填入 API Key 後點「生成報告」。使用 §2 中（已修改的）prompt 數據。
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 160px", gap: 10, marginBottom: 12 }}>
              <div>
                <label
                  style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#8c7089", marginBottom: 4 }}
                >
                  API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={provider === "anthropic" ? "sk-ant-..." : "AIza..."}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "rgba(255,255,255,0.5)",
                    border: "1px solid rgba(255,255,255,0.6)",
                    borderRadius: 10,
                    fontSize: 12,
                    color: "#5c4059",
                    outline: "none",
                  }}
                />
              </div>
              <div>
                <label
                  style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#8c7089", marginBottom: 4 }}
                >
                  Provider
                </label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value as "anthropic" | "gemini")}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "rgba(255,255,255,0.5)",
                    border: "1px solid rgba(255,255,255,0.6)",
                    borderRadius: 10,
                    fontSize: 12,
                    color: "#5c4059",
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>
            </div>

            <button
              onClick={generateReport}
              disabled={generatingReport || !apiKey}
              style={{
                background:
                  generatingReport || !apiKey
                    ? "rgba(217,134,149,0.3)"
                    : "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
                color: "#fff",
                border: "none",
                padding: "10px 28px",
                borderRadius: 999,
                fontSize: 13,
                fontWeight: 600,
                cursor: generatingReport || !apiKey ? "not-allowed" : "pointer",
                boxShadow:
                  generatingReport || !apiKey
                    ? "none"
                    : "0 4px 14px rgba(217,134,149,0.3)",
              }}
            >
              {generatingReport ? "⟳ LLM 生成中..." : "✦ 生成深度報告"}
            </button>

            {llmError ? (
              <p style={{ color: "#c0392b", fontSize: 12, marginTop: 10 }}>✕ {llmError}</p>
            ) : null}

            {/* LLM result */}
            {llmReport ? (
              <div
                style={{
                  marginTop: 20,
                  background: "rgba(255,255,255,0.5)",
                  border: "1px solid rgba(217,134,149,0.2)",
                  borderRadius: 12,
                  padding: "18px 20px",
                }}
              >
                {llmReport.title ? (
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: "#5c4059", marginBottom: 6 }}>
                    {llmReport.title}
                  </h3>
                ) : null}
                {llmReport.one_liner ? (
                  <p
                    style={{
                      fontSize: 13,
                      color: "#8c7089",
                      fontStyle: "italic",
                      marginBottom: 16,
                      paddingBottom: 12,
                      borderBottom: "1px solid rgba(217,134,149,0.15)",
                    }}
                  >
                    {llmReport.one_liner}
                  </p>
                ) : null}

                {llmReport.sparks && llmReport.sparks.length > 0 ? (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ ...sectionHead, marginBottom: 6 }}>閃光點</p>
                    {llmReport.sparks.map((s, i) => (
                      <p key={i} style={{ fontSize: 12, color: "#5c4059", marginBottom: 4 }}>{s}</p>
                    ))}
                  </div>
                ) : null}

                {llmReport.landmines && llmReport.landmines.length > 0 ? (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ ...sectionHead, marginBottom: 6 }}>雷區</p>
                    {llmReport.landmines.map((l, i) => (
                      <p key={i} style={{ fontSize: 12, color: "#5c4059", marginBottom: 4 }}>{l}</p>
                    ))}
                  </div>
                ) : null}

                {llmReport.advice ? (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ ...sectionHead, marginBottom: 6 }}>相處建議</p>
                    <p style={{ fontSize: 12, color: "#5c4059", lineHeight: 1.7 }}>{llmReport.advice}</p>
                  </div>
                ) : null}

                {llmReport.core ? (
                  <p
                    style={{
                      fontSize: 13,
                      color: "#b86e7d",
                      fontStyle: "italic",
                      textAlign: "center",
                      padding: "12px 0 0",
                      borderTop: "1px solid rgba(217,134,149,0.15)",
                    }}
                  >
                    ✦ {llmReport.core}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
