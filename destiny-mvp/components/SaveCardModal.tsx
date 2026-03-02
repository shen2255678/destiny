"use client";

import React, { useState } from "react";
import { ProfileIconPicker } from "./ProfileIconPicker";

interface Props {
  person: "A" | "B";
  defaultName?: string;
  onConfirm: (label: string, avatarIcon: string) => Promise<void>;
  onClose: () => void;
}

const overlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(30,10,35,0.55)",
  backdropFilter: "blur(4px)",
  zIndex: 1000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px",
};

const modal: React.CSSProperties = {
  background: "rgba(255,255,255,0.92)",
  backdropFilter: "blur(16px)",
  borderRadius: 24,
  padding: "28px 24px",
  width: "100%",
  maxWidth: 400,
  boxShadow: "0 20px 60px rgba(92,64,89,0.25)",
};

export function SaveCardModal({ person, defaultName = "", onConfirm, onClose }: Props) {
  const [step, setStep] = useState<1 | 2>(1);
  const [icon, setIcon] = useState("✦");
  const [label, setLabel] = useState(defaultName);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleConfirm() {
    if (!label.trim()) { setError("請輸入命盤名稱"); return; }
    setSaving(true);
    setError("");
    try {
      await onConfirm(label.trim(), icon);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "儲存失敗，請再試一次");
      setSaving(false);
    }
  }

  return (
    <div style={overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={modal}>
        {/* Step indicator */}
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 20 }}>
          {([1, 2] as const).map((s) => (
            <div
              key={s}
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: step === s ? "#d98695" : "rgba(140,112,137,0.3)",
                transition: "background 0.2s",
              }}
            />
          ))}
        </div>

        {step === 1 ? (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#5c4059", marginBottom: 4 }}>
              選擇命盤圖示
            </h2>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 16 }}>
              為「{person === "A" ? "命盤 A" : "命盤 B"}」挑選一個象徵符號
            </p>
            <ProfileIconPicker value={icon} onChange={setIcon} />
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setStep(2)}
                style={{
                  padding: "10px 24px",
                  borderRadius: 999,
                  background: "linear-gradient(135deg, #d98695, #b86e7d)",
                  color: "#fff",
                  border: "none",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                下一步 →
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#5c4059", marginBottom: 4 }}>
              為命盤命名
            </h2>
            <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 20 }}>
              取一個你記得住的名字
            </p>

            {/* Selected icon preview */}
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 56,
                  height: 56,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, rgba(217,134,149,0.2), rgba(124,92,138,0.2))",
                  fontSize: 28,
                  border: "2px solid rgba(217,134,149,0.4)",
                }}
              >
                {icon}
              </div>
            </div>

            <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 6 }}>
              命盤名稱
            </label>
            <input
              value={label}
              onChange={(e) => { setLabel(e.target.value); setError(""); }}
              placeholder="例：小羊的星盤"
              maxLength={50}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: 12,
                border: error ? "1px solid #c0392b" : "1px solid rgba(140,112,137,0.3)",
                background: "rgba(255,255,255,0.6)",
                fontSize: 14,
                color: "#5c4059",
                outline: "none",
                boxSizing: "border-box",
              }}
              onKeyDown={(e) => { if (e.key === "Enter") handleConfirm(); }}
            />
            {error && (
              <p style={{ color: "#c0392b", fontSize: 12, marginTop: 4 }}>{error}</p>
            )}

            <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
              <button
                type="button"
                onClick={() => setStep(1)}
                disabled={saving}
                style={{
                  flex: 1,
                  padding: "10px 0",
                  borderRadius: 999,
                  background: "transparent",
                  border: "1px solid rgba(140,112,137,0.35)",
                  color: "#8c7089",
                  fontSize: 13,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                ← 上一步
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={saving}
                style={{
                  flex: 2,
                  padding: "10px 0",
                  borderRadius: 999,
                  background: saving ? "rgba(217,134,149,0.4)" : "linear-gradient(135deg, #d98695, #b86e7d)",
                  color: "#fff",
                  border: "none",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: saving ? "not-allowed" : "pointer",
                }}
              >
                {saving ? "儲存中..." : "建立命盤 ✓"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
