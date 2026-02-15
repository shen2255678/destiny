"use client";

/**
 * DESTINY — Chat Room Page
 * Route: /connections/[id]
 *
 * Full-screen chat interface for an active connection. Features:
 *   - Top bar with back navigation, blurred avatar, chameleon tags, sync meter
 *   - Blurred photo section (Lv.1 — Gaussian-blur gradient, no real image)
 *   - Scrollable chat history with alternating self/match message bubbles
 *   - Fixed bottom input bar with send button
 *
 * Sync level progression reference (from MVP spec):
 *   Lv.1  (0–10 messages)   : Text only, heavy photo blur
 *   Lv.2  (10–50 messages)  : 50% photo clarity + voice calling unlocked
 *   Lv.3  (50+ OR 3+ min calls): Full HD photos + contact sharing
 *
 * This file is purely static UI. No actual WebSocket or API calls are made.
 * To simulate Lv.2, change MOCK_SYNC.level to 2 and message counts accordingly;
 * the blurred photo section conditionally renders based on level.
 *
 * Usage:
 *   Navigate to /connections/conn-1 — all data is mocked inline.
 *   The [id] param is consumed for display only (no data fetch).
 */

import Link from "next/link";
import React, { useRef } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: string;
  isSelf: boolean;
  text: string;
  timestamp: string;
}

interface SyncState {
  level: number;
  messageCount: number;
  /** Messages needed to reach next level */
  nextLevelTarget: number;
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_TAGS = ["Tender", "Curious"];

const MOCK_SYNC: SyncState = {
  level: 1,
  messageCount: 3,
  nextLevelTarget: 10,
};

const MOCK_MESSAGES: Message[] = [
  {
    id: "m1",
    isSelf: false,
    text: "Hi. I listened to your voice note — there's something really calm about it.",
    timestamp: "14:02",
  },
  {
    id: "m2",
    isSelf: true,
    text: "That means a lot. I was a bit nervous recording it honestly.",
    timestamp: "14:04",
  },
  {
    id: "m3",
    isSelf: false,
    text: "Nervous is good. It means you cared enough to show up.",
    timestamp: "14:05",
  },
  {
    id: "m4",
    isSelf: true,
    text: "That really resonated with me...",
    timestamp: "14:07",
  },
  {
    id: "m5",
    isSelf: false,
    text: "The system matched us as Complementary. I think I understand why.",
    timestamp: "14:09",
  },
  {
    id: "m6",
    isSelf: true,
    text: "Me too. What made you accept?",
    timestamp: "14:11",
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Ambient decorative blobs */
function AmbientBlobs() {
  return (
    <>
      <div
        className="absolute top-[-12%] right-[-8%] w-[45%] h-[45%] rounded-full bg-[#f7c5a8] opacity-20 blur-[90px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-[10%] left-[-8%] w-[40%] h-[40%] rounded-full bg-[#a8e6cf] opacity-15 blur-[80px] pointer-events-none"
        aria-hidden="true"
      />
    </>
  );
}

/** Blurred gradient avatar circle */
function BlurredAvatar({ size = "md" }: { size?: "sm" | "md" }) {
  const sizeClass = size === "sm" ? "w-9 h-9" : "w-11 h-11";
  return (
    <div
      className={`${sizeClass} rounded-full shrink-0 relative overflow-hidden`}
      style={{ border: "1.5px solid rgba(255,255,255,0.7)" }}
      aria-hidden="true"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[#d98695] via-[#f7c5a8] to-[#fcecf0] opacity-70" />
      <div className="absolute inset-1.5 rounded-full bg-gradient-to-br from-rose-300 to-pink-400 blur-lg opacity-80" />
      <div className="absolute inset-0 backdrop-blur-sm" />
    </div>
  );
}

/** Sync level progress indicator */
function SyncMeter({ sync }: { sync: SyncState }) {
  const pct = Math.min((sync.messageCount / sync.nextLevelTarget) * 100, 100);

  const barColor =
    sync.level === 1
      ? "#d98695"
      : sync.level === 2
      ? "#f7c5a8"
      : "#a8e6cf";

  return (
    <div
      className="flex items-center gap-2"
      aria-label={`Sync level ${sync.level}, ${sync.messageCount} of ${sync.nextLevelTarget} messages toward next level`}
    >
      <span
        className="text-[10px] font-medium whitespace-nowrap"
        style={{ color: barColor }}
      >
        Lv.{sync.level} · {sync.messageCount}/{sync.nextLevelTarget}
      </span>
      {/* Mini progress bar */}
      <div
        className="w-16 h-1.5 rounded-full overflow-hidden"
        style={{ background: "rgba(92,64,89,0.1)" }}
        role="presentation"
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${barColor}77, ${barColor})`,
          }}
        />
      </div>
    </div>
  );
}

/** Top navigation bar */
function TopBar({ sync }: { sync: SyncState }) {
  return (
    <header
      className="relative z-20 glass-panel border-b border-white/40 px-4 py-3 flex items-center gap-3"
      role="banner"
    >
      {/* Back arrow */}
      <Link
        href="/connections"
        className="w-9 h-9 rounded-full flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200 shrink-0"
        aria-label="Back to Connections"
      >
        <span className="material-symbols-outlined text-xl" aria-hidden="true">
          arrow_back
        </span>
      </Link>

      {/* Blurred avatar */}
      <BlurredAvatar size="sm" />

      {/* Tags + sync meter */}
      <div className="flex-1 min-w-0 space-y-1">
        {/* Chameleon tags */}
        <div
          className="flex flex-wrap gap-1.5"
          role="list"
          aria-label="Chameleon tags for this connection"
        >
          {MOCK_TAGS.map((tag) => (
            <span
              key={tag}
              className="text-[10px] px-2 py-0.5 rounded-full font-medium text-[#b86e7d]"
              style={{
                background: "rgba(217,134,149,0.1)",
                border: "1px solid rgba(217,134,149,0.2)",
              }}
              role="listitem"
            >
              {tag}
            </span>
          ))}
        </div>

        {/* Sync meter */}
        <SyncMeter sync={sync} />
      </div>

      {/* Optional voice call button — unlocked at Lv.2+ (grayed out at Lv.1) */}
      <button
        className="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 shrink-0"
        style={{
          background: sync.level >= 2
            ? "linear-gradient(135deg, #d98695, #b86e7d)"
            : "rgba(92,64,89,0.06)",
        }}
        disabled={sync.level < 2}
        aria-label={
          sync.level >= 2
            ? "Start voice call"
            : "Voice call unlocked at Lv.2"
        }
        title={sync.level < 2 ? "Unlocked at Lv.2" : "Voice call"}
      >
        <span
          className="material-symbols-outlined text-sm"
          style={{ color: sync.level >= 2 ? "#fff" : "#8c7089" }}
          aria-hidden="true"
        >
          call
        </span>
      </button>
    </header>
  );
}

/**
 * Blurred photo section — simulates Lv.1 photo blur.
 *
 * At Lv.2+, this section would render a 50%-clear photo (desaturated /
 * partially unblurred gradient). At Lv.3 it would show the full HD photo.
 * For this static UI, we always render the Lv.1 blurred state.
 *
 * To simulate Lv.2: replace the inner gradient blob with a less-blurred
 * version (blur-sm instead of blur-2xl) and update the overlay text.
 */
function BlurredPhotoSection({ sync }: { sync: SyncState }) {
  /* --- Lv.2 would look like:
   *   blur-sm, opacity-60, overlay text: "Lv.2 · 解鎖 50% 照片清晰度"
   * --- Lv.3 would show a real (or mock) image entirely.
   */

  const unlockMessage =
    sync.level === 1
      ? `Lv.1 · 完成 ${sync.nextLevelTarget} 則對話以解鎖 50% 照片`
      : sync.level === 2
      ? "Lv.2 · 完成 50 則對話以解鎖完整照片"
      : "Lv.3 · 照片完整解鎖";

  return (
    <div
      className="relative w-full overflow-hidden"
      style={{ height: "200px" }}
      aria-label={`Photo locked — ${unlockMessage}`}
      role="img"
    >
      {/* Blurred gradient stands in for the real photo */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#fcecf0] via-[#fdf2e9] to-[#f7c5a8] opacity-80" />

      {/* Gaussian-blur portrait blob */}
      <div
        className="absolute inset-4 rounded-full mx-auto"
        style={{ maxWidth: "160px", left: "50%", transform: "translateX(-50%)" }}
        aria-hidden="true"
      >
        <div className="w-full h-full rounded-full bg-gradient-to-br from-[#d98695] to-[#f7c5a8] blur-2xl opacity-60" />
      </div>

      {/* Secondary color blobs for realism */}
      <div
        className="absolute top-4 right-6 w-20 h-20 rounded-full bg-[#a8e6cf] blur-3xl opacity-40"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-4 left-8 w-16 h-16 rounded-full bg-[#e6b3cc] blur-2xl opacity-40"
        aria-hidden="true"
      />

      {/* Frosted overlay */}
      <div className="absolute inset-0 backdrop-blur-xl" aria-hidden="true" />

      {/* Lock icon + unlock progress overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center"
          style={{
            background: "rgba(255,255,255,0.4)",
            backdropFilter: "blur(8px)",
            border: "1.5px solid rgba(255,255,255,0.6)",
          }}
          aria-hidden="true"
        >
          <span
            className="material-symbols-outlined text-xl text-[#d98695]"
          >
            {sync.level >= 3 ? "lock_open" : "lock"}
          </span>
        </div>

        <div className="text-center space-y-1.5 px-6">
          <p
            className="text-xs font-medium text-[#5c4059]"
            style={{ textShadow: "0 1px 4px rgba(255,255,255,0.8)" }}
          >
            {unlockMessage}
          </p>

          {/* Inline unlock progress bar */}
          {sync.level < 3 && (
            <div className="flex items-center gap-2 justify-center">
              <div
                className="h-1 rounded-full overflow-hidden"
                style={{
                  width: "120px",
                  background: "rgba(92,64,89,0.12)",
                }}
                role="progressbar"
                aria-valuenow={sync.messageCount}
                aria-valuemin={0}
                aria-valuemax={sync.nextLevelTarget}
                aria-label={`${sync.messageCount} of ${sync.nextLevelTarget} messages to unlock photo`}
              >
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.min((sync.messageCount / sync.nextLevelTarget) * 100, 100)}%`,
                    background: "linear-gradient(90deg, #d98695aa, #d98695)",
                  }}
                />
              </div>
              <span className="text-[10px] text-[#8c7089]">
                {sync.messageCount}/{sync.nextLevelTarget}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Individual message bubble */
function MessageBubble({ message }: { message: Message }) {
  if (message.isSelf) {
    return (
      <div className="flex justify-end" role="listitem">
        <div className="max-w-[72%] space-y-1">
          <div
            className="px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm text-white leading-relaxed shadow-[0_4px_14px_rgba(217,134,149,0.3)]"
            style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
          >
            {message.text}
          </div>
          <p className="text-[10px] text-[#8c7089] text-right pr-1">
            {message.timestamp}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start gap-2.5" role="listitem">
      {/* Small blurred avatar beside message */}
      <BlurredAvatar size="sm" />

      <div className="max-w-[72%] space-y-1">
        <div
          className="glass-panel px-4 py-2.5 rounded-2xl rounded-tl-sm text-sm text-[#5c4059] leading-relaxed"
        >
          {message.text}
        </div>
        <p className="text-[10px] text-[#8c7089] pl-1">
          {message.timestamp}
        </p>
      </div>
    </div>
  );
}

/** Chat message list */
function ChatArea() {
  const bottomRef = useRef<HTMLDivElement>(null);

  return (
    <div
      className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
      aria-relevant="additions"
    >
      {/* Day separator */}
      <div className="flex items-center gap-3" aria-hidden="true">
        <div
          className="flex-1 h-px"
          style={{ background: "rgba(92,64,89,0.08)" }}
        />
        <span className="text-[10px] text-[#8c7089] tracking-wider">
          Today
        </span>
        <div
          className="flex-1 h-px"
          style={{ background: "rgba(92,64,89,0.08)" }}
        />
      </div>

      {/* Messages */}
      <ul className="space-y-4 list-none" aria-label="Message history">
        {MOCK_MESSAGES.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </ul>

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}

/** Bottom input bar */
function InputBar() {
  return (
    <div
      className="relative z-20 glass-panel border-t border-white/40 px-4 py-3 flex items-end gap-3"
      role="form"
      aria-label="Send a message"
    >
      {/* Text input */}
      <div className="flex-1 relative">
        <input
          type="text"
          placeholder="輸入訊息..."
          className="w-full px-4 py-2.5 rounded-2xl text-sm text-[#5c4059] placeholder-[#8c7089] outline-none transition-all duration-200 resize-none"
          style={{
            background: "rgba(255,255,255,0.5)",
            border: "1px solid rgba(255,255,255,0.7)",
            backdropFilter: "blur(8px)",
          }}
          aria-label="Type a message"
          onFocus={(e) => {
            e.currentTarget.style.boxShadow =
              "0 0 0 2px rgba(217,134,149,0.3)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.boxShadow = "none";
          }}
        />
      </div>

      {/* Send button */}
      <button
        className="w-10 h-10 shrink-0 rounded-full flex items-center justify-center text-white transition-all duration-200 hover:scale-105 active:scale-95 shadow-[0_4px_14px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.55)]"
        style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
        aria-label="Send message"
      >
        <span className="material-symbols-outlined text-lg" aria-hidden="true">
          arrow_upward
        </span>
      </button>
    </div>
  );
}

/** Sync level unlock notification strip */
function UnlockReminder({ sync }: { sync: SyncState }) {
  if (sync.level >= 3) return null;

  const remaining = sync.nextLevelTarget - sync.messageCount;
  const nextUnlock =
    sync.level === 1
      ? "50% 照片清晰度 + 語音通話"
      : "完整 HD 照片 + 聯絡資訊";

  return (
    <div
      className="mx-4 mb-2 px-3.5 py-2 rounded-xl flex items-center gap-2.5"
      style={{
        background: "rgba(217,134,149,0.07)",
        border: "1px solid rgba(217,134,149,0.15)",
      }}
      role="status"
      aria-label={`${remaining} more messages to unlock ${nextUnlock}`}
    >
      <span
        className="material-symbols-outlined text-sm text-[#d98695] shrink-0"
        aria-hidden="true"
      >
        lock_open
      </span>
      <p className="text-[10px] text-[#8c7089] leading-relaxed">
        還差{" "}
        <span className="font-semibold text-[#d98695]">{remaining} 則</span>{" "}
        對話可解鎖 {nextUnlock}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

/**
 * ChatRoomPage receives the connection [id] via params, but since all data is
 * mocked, the id is only used in the aria-label for accessibility context.
 */
export default function ChatRoomPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = React.use(params);
  const sync = MOCK_SYNC;

  return (
    <div
      className="min-h-screen flex flex-col relative selection:bg-[#d98695] selection:text-white"
      style={{ maxHeight: "100dvh", height: "100dvh" }}
    >
      {/* Ambient light blobs */}
      <AmbientBlobs />

      {/* Top bar — fixed at top */}
      <TopBar sync={sync} />

      {/* Main: scrollable chat area takes remaining height */}
      <main
        className="relative z-10 flex-1 flex flex-col overflow-hidden"
        role="main"
        aria-label={`Chat room — connection ${id}`}
      >
        {/* Blurred photo section — Lv.1 locked state */}
        <BlurredPhotoSection sync={sync} />

        {/* Chat messages — flex-1, scrollable */}
        <ChatArea />

        {/* Unlock progress reminder */}
        <UnlockReminder sync={sync} />

        {/* Message input bar */}
        <InputBar />
      </main>
    </div>
  );
}
