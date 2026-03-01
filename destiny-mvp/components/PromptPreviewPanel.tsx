"use client";

import { useState } from "react";
import { translateShadowTag, translatePsychTrigger } from "@/lib/shadowTagsZh";

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

  // Pre-built prompts from enriched DTO (only present in new records)
  const prebuiltPrompts = (r.prompts as Record<string, string> | undefined) ?? null;
  const PROMPT_LABELS: Record<string, string> = {
    synastry: "合盤洞察 (Synastry)",
    ideal_a:  `${nameA} 理想伴侶 (Ideal A)`,
    ideal_b:  `${nameB} 理想伴侶 (Ideal B)`,
    profile_a: `${nameA} 靈魂面具 (Profile A)`,
    profile_b: `${nameB} 靈魂面具 (Profile B)`,
  };
  const PROMPT_KEYS = ["synastry", "ideal_a", "ideal_b", "profile_a", "profile_b"];
  const availablePromptKeys = PROMPT_KEYS.filter((k) => prebuiltPrompts?.[k]);
  const [activePromptKey, setActivePromptKey] = useState<string>("");

  // Extract fields from reportJson
  const psychTagsRaw = (r.psychological_tags as string[]) ?? [];
  const psychTriggersRaw = (r.psychological_triggers as string[]) ?? [];
  const resonanceBadges = (r.resonance_badges as string[]) ?? [];
  const tracks = (r.tracks as Record<string, number>) ?? {};
  const power = (r.power as Record<string, unknown>) ?? {};
  // Individual chart data (available for matches made after the echo fix)
  const chartA = (r.user_a_chart as Record<string, string>) ?? {};
  const chartB = (r.user_b_chart as Record<string, string>) ?? {};

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

          {/* ── Section 0: Pre-built Prompts (enriched DTO only) ── */}
          <div style={{ ...glass, padding: "20px 24px" }}>
            <p style={sectionHead}>§0 預建 Prompt（新版報告限定）</p>
            {availablePromptKeys.length > 0 ? (
              <>
                <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 12 }}>
                  這些是 Pipeline 預算好存在報告中的 Prompt，可直接複製送給 LLM。
                </p>
                {/* Tab buttons */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                  {availablePromptKeys.map((k) => (
                    <button
                      key={k}
                      onClick={() => setActivePromptKey(activePromptKey === k ? "" : k)}
                      style={{
                        padding: "4px 12px",
                        borderRadius: 999,
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: "pointer",
                        border: activePromptKey === k
                          ? "1px solid #b86e7d"
                          : "1px solid rgba(200,160,170,0.4)",
                        background: activePromptKey === k
                          ? "rgba(184,110,125,0.15)"
                          : "transparent",
                        color: activePromptKey === k ? "#b86e7d" : "#8c7089",
                        transition: "all 0.15s",
                      }}
                    >
                      {PROMPT_LABELS[k] ?? k}
                    </button>
                  ))}
                </div>
                {activePromptKey && prebuiltPrompts?.[activePromptKey] ? (
                  <div>
                    <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 4 }}>
                      <span style={{ fontSize: 11, color: "#8c7089" }}>
                        {prebuiltPrompts[activePromptKey].length} 字元
                      </span>
                    </div>
                    <textarea
                      readOnly
                      value={prebuiltPrompts[activePromptKey]}
                      rows={14}
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
                  </div>
                ) : null}
              </>
            ) : (
              <p style={{ fontSize: 12, color: "#aaa" }}>
                此為舊版報告，不含預建 Prompt。重新跑一次合盤即可獲得。
              </p>
            )}
          </div>

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
              label="暗影標籤"
              value={
                psychTagsRaw.length > 0 ? (
                  <span>
                    {psychTagsRaw.map((t) => (
                      <span key={t} style={pill("#b86e7d")} title={t}>
                        {translateShadowTag(t)}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span style={{ color: "#aaa" }}>無</span>
                )
              }
            />

            <DataRow
              label="心理觸發"
              value={
                psychTriggersRaw.length > 0 ? (
                  <span>
                    {psychTriggersRaw.map((t) => (
                      <span key={t} style={pill("#7c3aed")} title={t}>
                        {translatePsychTrigger(t)}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span style={{ color: "#aaa" }}>無</span>
                )
              }
            />

            <DataRow
              label="命理認證"
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

            {(Object.keys(chartA).length > 0 || Object.keys(chartB).length > 0) ? (
              <>
                <DataRow
                  label={`${nameA} 命盤`}
                  value={
                    <span style={{ fontSize: 11, lineHeight: 1.7 }}>
                      ☀ {chartA.sun_sign || "—"} · 月 {chartA.moon_sign || "—"} · 升 {chartA.ascendant_sign || "—"}<br />
                      ♀ {chartA.venus_sign || "—"} · ♂ {chartA.mars_sign || "—"} · ♄ {chartA.saturn_sign || "—"}<br />
                      八字: {chartA.bazi_element || "—"} · 依戀: {chartA.attachment_style || "—"}
                    </span>
                  }
                />
                <DataRow
                  label={`${nameB} 命盤`}
                  value={
                    <span style={{ fontSize: 11, lineHeight: 1.7 }}>
                      ☀ {chartB.sun_sign || "—"} · 月 {chartB.moon_sign || "—"} · 升 {chartB.ascendant_sign || "—"}<br />
                      ♀ {chartB.venus_sign || "—"} · ♂ {chartB.mars_sign || "—"} · ♄ {chartB.saturn_sign || "—"}<br />
                      八字: {chartB.bazi_element || "—"} · 依戀: {chartB.attachment_style || "—"}
                    </span>
                  }
                />
              </>
            ) : (
              <DataRow
                label="個人命盤"
                value={<span style={{ color: "#aaa", fontSize: 11 }}>重新跑一次匹配後可見（舊紀錄不含此資料）</span>}
              />
            )}
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
