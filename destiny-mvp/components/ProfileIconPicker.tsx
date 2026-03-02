"use client";

import React from "react";

export const ICON_SET = [
  // 黃道十二宮
  "♈", "♉", "♊", "♋", "♌", "♍",
  "♎", "♏", "♐", "♑", "♒", "♓",
  // 行星符號
  "☽", "☀", "✦", "☿", "♀", "♂",
  "♃", "♄", "♅", "♆", "⚸", "⚷",
  // 神秘主題
  "⭐", "🌙", "💫", "✨", "🔮", "🌸",
  "🌊", "🌀", "⚡", "🪐", "🌌", "🌟",
] as const;

interface Props {
  value: string;
  onChange: (icon: string) => void;
  disabled?: boolean;
}

export function ProfileIconPicker({ value, onChange, disabled }: Props) {
  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 8,
          marginBottom: 16,
        }}
      >
        {ICON_SET.map((icon) => (
          <button
            key={icon}
            type="button"
            disabled={disabled}
            onClick={() => onChange(icon)}
            style={{
              width: 44,
              height: 44,
              borderRadius: 10,
              border: icon === value
                ? "2px solid #d98695"
                : "2px solid rgba(255,255,255,0.4)",
              background: icon === value
                ? "rgba(217,134,149,0.15)"
                : "rgba(255,255,255,0.25)",
              fontSize: 20,
              cursor: disabled ? "not-allowed" : "pointer",
              transition: "border 0.15s, background 0.15s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              lineHeight: 1,
            }}
          >
            {icon}
          </button>
        ))}
      </div>

      {/* Phase 2 placeholder */}
      <button
        type="button"
        disabled
        style={{
          width: "100%",
          padding: "9px 0",
          borderRadius: 10,
          border: "1px dashed rgba(140,112,137,0.35)",
          background: "transparent",
          color: "#a08a9d",
          fontSize: 12,
          cursor: "not-allowed",
          letterSpacing: "0.03em",
        }}
      >
        📷 上傳自訂圖片 · 即將推出
      </button>
    </div>
  );
}
