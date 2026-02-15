"use client";

/**
 * DESTINY — Connections List Page
 * Route: /connections
 *
 * Displays a user's active connections — people who have mutually accepted a
 * daily match. Each connection card shows:
 *   - A blurred gradient avatar (no real photos at Lv.1)
 *   - Chameleon tags (relational labels unique to this pairing)
 *   - Sync level and message count progress
 *   - Last message preview and timestamp
 *   - Status badge (Active / Expiring soon)
 *
 * Empty state shown when there are no connections yet.
 *
 * Per MVP spec: photos remain blurred until Lv.2 (10+ exchanges). The
 * gradient blobs here simulate what a user would see at Lv.1.
 *
 * Usage:
 *   Navigate to /connections — all data is mocked inline. Cards link to
 *   /connections/[id] for the chat room.
 */

import Link from "next/link";
import { useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ConnectionStatus = "active" | "expiring";

interface ChameleonTag {
  label: string;
}

interface Connection {
  id: string;
  tags: ChameleonTag[];
  syncLevel: number;
  messageCount: number;
  messageTarget: number;
  lastMessage: string;
  timestamp: string;
  status: ConnectionStatus;
  avatarGradient: string;
  avatarBlob: string;
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const MOCK_CONNECTIONS: Connection[] = [
  {
    id: "conn-1",
    tags: [{ label: "Tender" }, { label: "Grounding" }],
    syncLevel: 1,
    messageCount: 3,
    messageTarget: 10,
    lastMessage: "That really resonated with me...",
    timestamp: "2 hours ago",
    status: "active",
    avatarGradient: "from-[#d98695] via-[#f7c5a8] to-[#fcecf0]",
    avatarBlob: "from-rose-200 to-pink-300",
  },
  {
    id: "conn-2",
    tags: [{ label: "Curious" }, { label: "Playful" }],
    syncLevel: 1,
    messageCount: 7,
    messageTarget: 10,
    lastMessage: "...",
    timestamp: "5 hours ago",
    status: "expiring",
    avatarGradient: "from-[#a8e6cf] via-[#f7c5a8] to-[#fdf2e9]",
    avatarBlob: "from-teal-200 to-emerald-300",
  },
  {
    id: "conn-3",
    tags: [{ label: "Steady" }, { label: "Deep" }, { label: "Honest" }],
    syncLevel: 1,
    messageCount: 1,
    messageTarget: 10,
    lastMessage: "Hi, I'm glad we matched.",
    timestamp: "Yesterday",
    status: "active",
    avatarGradient: "from-[#e6b3cc] via-[#d98695] to-[#f7c5a8]",
    avatarBlob: "from-purple-200 to-pink-300",
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
        className="absolute top-[-10%] left-[-8%] w-[50%] h-[50%] rounded-full bg-[#d98695] opacity-15 blur-[100px] pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-[-5%] right-[-5%] w-[40%] h-[40%] rounded-full bg-[#a8e6cf] opacity-15 blur-[90px] pointer-events-none"
        aria-hidden="true"
      />
    </>
  );
}

/** Top header bar */
function TopHeader() {
  return (
    <header
      className="relative z-20 w-full px-5 py-5 flex items-center justify-between"
      role="banner"
    >
      <div>
        <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] font-medium">
          Your Active
        </p>
        <h1 className="text-xl font-light text-[#5c4059] tracking-wide">
          Connections
        </h1>
      </div>

      <button
        className="relative w-10 h-10 rounded-full glass-panel flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200"
        aria-label="Notifications"
      >
        <span className="material-symbols-outlined text-xl" aria-hidden="true">
          notifications
        </span>
        {/* Notification dot */}
        <span
          className="absolute top-2 right-2 w-2 h-2 bg-[#d98695] rounded-full shadow-[0_0_6px_rgba(217,134,149,0.6)]"
          aria-hidden="true"
        />
      </button>
    </header>
  );
}

/** Blurred gradient avatar — simulates Lv.1 photo blur */
function BlurredAvatar({
  gradient,
  blobGradient,
  size = "md",
}: {
  gradient: string;
  blobGradient: string;
  size?: "md" | "lg";
}) {
  const sizeClass = size === "lg" ? "w-16 h-16" : "w-14 h-14";

  return (
    <div
      className={`${sizeClass} rounded-full shrink-0 relative overflow-hidden`}
      style={{ border: "1.5px solid rgba(255,255,255,0.7)" }}
      aria-hidden="true"
    >
      {/* Base gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-60`} />
      {/* Blurred blob on top — mimics portrait blur */}
      <div
        className={`absolute inset-2 rounded-full bg-gradient-to-br ${blobGradient} blur-md opacity-80`}
      />
      {/* Heavy blur overlay */}
      <div className="absolute inset-0 backdrop-blur-sm" />
    </div>
  );
}

/** Status badge — Active or Expiring soon */
function StatusBadge({ status }: { status: ConnectionStatus }) {
  if (status === "active") {
    return (
      <div
        className="flex items-center gap-1.5"
        aria-label="Connection status: Active"
      >
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.7)]" />
        <span className="text-[10px] text-emerald-600 font-medium uppercase tracking-wider">
          Active
        </span>
      </div>
    );
  }

  return (
    <div
      className="flex items-center gap-1.5"
      aria-label="Connection status: Expiring soon"
    >
      <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse shadow-[0_0_4px_rgba(251,146,60,0.7)]" />
      <span className="text-[10px] text-orange-500 font-medium uppercase tracking-wider">
        Expiring soon
      </span>
    </div>
  );
}

/** Sync level progress bar */
function SyncProgress({
  level,
  count,
  target,
}: {
  level: number;
  count: number;
  target: number;
}) {
  const pct = Math.min((count / target) * 100, 100);

  // Color shifts with sync level
  const barColor =
    level === 1
      ? "#d98695"
      : level === 2
      ? "#f7c5a8"
      : "#a8e6cf";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-[#8c7089] font-medium">
          Lv.{level} · {count} message{count !== 1 ? "s" : ""}
        </span>
        <span className="text-[10px] text-[#8c7089]">
          {count}/{target}
        </span>
      </div>
      <div
        className="h-1 rounded-full overflow-hidden"
        style={{ background: "rgba(92,64,89,0.08)" }}
        role="progressbar"
        aria-valuenow={count}
        aria-valuemin={0}
        aria-valuemax={target}
        aria-label={`Sync level ${level}, ${count} of ${target} messages`}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${barColor}88, ${barColor})`,
          }}
        />
      </div>
    </div>
  );
}

/** Individual connection card */
function ConnectionCard({ connection }: { connection: Connection }) {
  return (
    <Link
      href={`/connections/${connection.id}`}
      className="block group"
      aria-label={`Open connection — tags: ${connection.tags.map((t) => t.label).join(", ")}. ${connection.status === "expiring" ? "Expiring soon." : "Active."}`}
    >
      <article className="glass-panel rounded-2xl p-4 transition-all duration-300 hover:bg-white/50 hover:shadow-[0_12px_30px_-8px_rgba(217,134,149,0.2)] hover:-translate-y-0.5 cursor-pointer">
        <div className="flex items-start gap-4">
          {/* Blurred avatar */}
          <BlurredAvatar
            gradient={connection.avatarGradient}
            blobGradient={connection.avatarBlob}
          />

          {/* Content */}
          <div className="flex-1 min-w-0 space-y-2">
            {/* Top row: tags + timestamp */}
            <div className="flex items-start justify-between gap-2">
              {/* Chameleon tags */}
              <div className="flex flex-wrap gap-1.5" role="list" aria-label="Chameleon tags">
                {connection.tags.map((tag) => (
                  <span
                    key={tag.label}
                    className="text-[10px] px-2.5 py-0.5 rounded-full font-medium text-[#b86e7d] tracking-wide"
                    style={{
                      background: "rgba(217,134,149,0.1)",
                      border: "1px solid rgba(217,134,149,0.2)",
                    }}
                    role="listitem"
                  >
                    {tag.label}
                  </span>
                ))}
              </div>

              <span className="text-[10px] text-[#8c7089] shrink-0 mt-0.5">
                {connection.timestamp}
              </span>
            </div>

            {/* Sync progress */}
            <SyncProgress
              level={connection.syncLevel}
              count={connection.messageCount}
              target={connection.messageTarget}
            />

            {/* Last message preview + status */}
            <div className="flex items-center justify-between gap-2 pt-0.5">
              <p className="text-xs text-[#8c7089] truncate font-light italic">
                "{connection.lastMessage}"
              </p>
              <StatusBadge status={connection.status} />
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}

/** Empty state — shown when there are no connections */
function EmptyState() {
  return (
    <div
      className="flex-1 flex items-center justify-center px-4 py-16"
      role="status"
      aria-live="polite"
    >
      <div className="glass-panel rounded-3xl p-10 max-w-xs w-full text-center space-y-5">
        {/* Icon */}
        <div
          className="w-16 h-16 mx-auto rounded-full flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, rgba(217,134,149,0.12), rgba(247,197,168,0.12))",
            border: "1.5px solid rgba(217,134,149,0.2)",
          }}
          aria-hidden="true"
        >
          <span
            className="material-symbols-outlined text-2xl"
            style={{ color: "#d98695" }}
          >
            hub
          </span>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-[#5c4059]">No connections yet</p>
          <p className="text-sm text-[#8c7089] leading-relaxed font-light">
            還沒有連結。等待今日的命運配對吧。
          </p>
        </div>

        <Link
          href="/daily"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-medium text-white tracking-wider uppercase shadow-[0_4px_14px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)] transition-all duration-200"
          style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
          aria-label="Go to daily feed to see today's matches"
        >
          <span className="material-symbols-outlined text-sm" aria-hidden="true">
            auto_awesome
          </span>
          View Today's Matches
        </Link>
      </div>
    </div>
  );
}

/** Section divider with count */
function SectionLabel({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-3 px-1">
      <span className="text-[10px] uppercase tracking-[0.3em] text-[#8c7089] font-medium">
        {count} active connection{count !== 1 ? "s" : ""}
      </span>
      <div
        className="flex-1 h-px"
        style={{
          background: "linear-gradient(90deg, rgba(217,134,149,0.3), transparent)",
        }}
        aria-hidden="true"
      />
      <span
        className="text-[10px] text-[#d98695] font-medium"
        aria-label="Resets daily"
      >
        Resets in 18h
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function ConnectionsPage() {
  /*
   * Toggle SHOW_EMPTY to true to preview the empty state.
   * In production this would be derived from actual connection data.
   */
  const SHOW_EMPTY = false;
  const connections = SHOW_EMPTY ? [] : MOCK_CONNECTIONS;

  const [_connections] = useState(connections);

  return (
    <div className="min-h-screen flex flex-col relative selection:bg-[#d98695] selection:text-white">
      {/* Ambient blobs */}
      <AmbientBlobs />

      {/* Header */}
      <TopHeader />

      {/* Main */}
      <main
        className="relative z-10 flex-1 w-full max-w-lg mx-auto px-4 pb-10 flex flex-col"
        role="main"
        aria-label="Active connections"
      >
        {_connections.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-4">
            {/* Section label */}
            <SectionLabel count={_connections.length} />

            {/* Connection cards */}
            <ul
              className="space-y-3"
              role="list"
              aria-label="Connection list"
            >
              {_connections.map((conn) => (
                <li key={conn.id}>
                  <ConnectionCard connection={conn} />
                </li>
              ))}
            </ul>

            {/* Auto-disconnect reminder */}
            <aside
              className="glass-panel rounded-xl p-3.5 flex items-start gap-2.5 mt-2"
              role="note"
              aria-label="Auto-disconnect policy reminder"
            >
              <span
                className="material-symbols-outlined text-sm text-[#d98695] shrink-0 mt-0.5"
                aria-hidden="true"
              >
                timer
              </span>
              <p className="text-[11px] text-[#8c7089] leading-relaxed font-light">
                Connections with 24 hours of inactivity are automatically closed.
                Keep the conversation alive.
              </p>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
