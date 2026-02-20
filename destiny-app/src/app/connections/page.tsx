"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ConnectionStatus = "icebreaker" | "active" | "expiring";

interface OtherUser {
  id: string;
  archetype_name: string | null;
  display_name: string | null;
}

interface Connection {
  id: string;
  tags: string[];
  sync_level: number;
  message_count: number;
  last_activity: string;
  status: string;
  other_user: OtherUser;
  blurred_photo_url: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "Yesterday" : `${days}d ago`;
}

function getMessageTarget(syncLevel: number): number {
  if (syncLevel === 1) return 10;
  if (syncLevel === 2) return 50;
  return 50;
}

function getDisplayStatus(conn: Connection): ConnectionStatus {
  const hoursSince = (Date.now() - new Date(conn.last_activity).getTime()) / 3_600_000;
  if (hoursSince > 20) return "expiring";
  return conn.status as ConnectionStatus;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AmbientBlobs() {
  return (
    <>
      <div className="absolute top-[-10%] left-[-8%] w-[50%] h-[50%] rounded-full bg-[#d98695] opacity-15 blur-[100px] pointer-events-none" aria-hidden="true" />
      <div className="absolute bottom-[-5%] right-[-5%] w-[40%] h-[40%] rounded-full bg-[#a8e6cf] opacity-15 blur-[90px] pointer-events-none" aria-hidden="true" />
    </>
  );
}

function TopHeader() {
  return (
    <header className="relative z-20 w-full px-4 md:px-6 py-5" role="banner">
      <div className="w-full max-w-lg md:max-w-3xl lg:max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/daily"
            className="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/60 transition-all duration-200 shrink-0"
            aria-label="Back to Daily Feed"
          >
            <span className="material-symbols-outlined text-xl" aria-hidden="true">arrow_back</span>
          </Link>
          <div>
            <p className="text-[10px] uppercase tracking-[0.35em] text-[#8c7089] font-medium">Your Active</p>
            <h1 className="text-xl font-light text-[#5c4059] tracking-wide">Connections</h1>
          </div>
        </div>
      </div>
    </header>
  );
}

function BlurredAvatar({ photoUrl }: { photoUrl: string | null }) {
  if (photoUrl) {
    return (
      <div className="w-14 h-14 rounded-full shrink-0 relative overflow-hidden" style={{ border: "1.5px solid rgba(255,255,255,0.7)" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={photoUrl} alt="" className="w-full h-full object-cover" style={{ filter: "blur(8px)", transform: "scale(1.1)" }} />
      </div>
    );
  }
  return (
    <div className="w-14 h-14 rounded-full shrink-0 relative overflow-hidden" style={{ border: "1.5px solid rgba(255,255,255,0.7)" }} aria-hidden="true">
      <div className="absolute inset-0 bg-gradient-to-br from-[#d98695] via-[#f7c5a8] to-[#fcecf0] opacity-60" />
      <div className="absolute inset-2 rounded-full bg-gradient-to-br from-rose-200 to-pink-300 blur-md opacity-80" />
      <div className="absolute inset-0 backdrop-blur-sm" />
    </div>
  );
}

function StatusBadge({ status }: { status: ConnectionStatus }) {
  if (status === "expiring") {
    return (
      <div className="flex items-center gap-1.5" aria-label="Expiring soon">
        <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse shadow-[0_0_4px_rgba(251,146,60,0.7)]" />
        <span className="text-[10px] text-orange-500 font-medium uppercase tracking-wider">Expiring soon</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5" aria-label="Active">
      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_rgba(52,211,153,0.7)]" />
      <span className="text-[10px] text-emerald-600 font-medium uppercase tracking-wider">Active</span>
    </div>
  );
}

function SyncProgress({ level, count, target }: { level: number; count: number; target: number }) {
  const pct = Math.min((count / target) * 100, 100);
  const barColor = level === 1 ? "#d98695" : level === 2 ? "#f7c5a8" : "#a8e6cf";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-[#8c7089] font-medium">Lv.{level} · {count} message{count !== 1 ? "s" : ""}</span>
        <span className="text-[10px] text-[#8c7089]">{count}/{target}</span>
      </div>
      <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(92,64,89,0.08)" }} role="progressbar" aria-valuenow={count} aria-valuemin={0} aria-valuemax={target}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${barColor}88, ${barColor})` }} />
      </div>
    </div>
  );
}

function ConnectionCard({ connection }: { connection: Connection }) {
  const displayStatus = getDisplayStatus(connection);
  const target = getMessageTarget(connection.sync_level);

  return (
    <Link href={`/connections/${connection.id}`} className="block group" aria-label={`Open connection — ${connection.tags.join(", ")}`}>
      <article className="glass-panel rounded-2xl p-4 transition-all duration-300 hover:bg-white/50 hover:shadow-[0_12px_30px_-8px_rgba(217,134,149,0.2)] hover:-translate-y-0.5 cursor-pointer">
        <div className="flex items-start gap-4">
          <BlurredAvatar photoUrl={connection.blurred_photo_url} />
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-wrap gap-1.5" role="list" aria-label="Tags">
                {connection.tags.map((tag) => (
                  <span key={tag} className="text-[10px] px-2.5 py-0.5 rounded-full font-medium text-[#b86e7d] tracking-wide" style={{ background: "rgba(217,134,149,0.1)", border: "1px solid rgba(217,134,149,0.2)" }} role="listitem">
                    {tag}
                  </span>
                ))}
                {connection.tags.length === 0 && (
                  <span className="text-[10px] text-[#8c7089] italic">{connection.other_user.archetype_name ?? "Mysterious"}</span>
                )}
              </div>
              <span className="text-[10px] text-[#8c7089] shrink-0 mt-0.5">{formatRelativeTime(connection.last_activity)}</span>
            </div>
            <SyncProgress level={connection.sync_level} count={connection.message_count} target={target} />
            <div className="flex items-center justify-between gap-2 pt-0.5">
              <p className="text-xs text-[#8c7089] truncate font-light italic">
                {connection.message_count === 0 ? "Start the conversation..." : `Lv.${connection.sync_level} connection`}
              </p>
              <StatusBadge status={displayStatus} />
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}

function EmptyState() {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-16" role="status" aria-live="polite">
      <div className="glass-panel rounded-3xl p-10 max-w-xs w-full text-center space-y-5">
        <div className="w-16 h-16 mx-auto rounded-full flex items-center justify-center" style={{ background: "linear-gradient(135deg, rgba(217,134,149,0.12), rgba(247,197,168,0.12))", border: "1.5px solid rgba(217,134,149,0.2)" }} aria-hidden="true">
          <span className="material-symbols-outlined text-2xl" style={{ color: "#d98695" }}>hub</span>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium text-[#5c4059]">No connections yet</p>
          <p className="text-sm text-[#8c7089] leading-relaxed font-light">還沒有連結。等待今日的命運配對吧。</p>
        </div>
        <Link href="/daily" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-medium text-white tracking-wider uppercase shadow-[0_4px_14px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)] transition-all duration-200" style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}>
          <span className="material-symbols-outlined text-sm" aria-hidden="true">auto_awesome</span>
          View Today&apos;s Matches
        </Link>
      </div>
    </div>
  );
}

function SectionLabel({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-3 px-1">
      <span className="text-[10px] uppercase tracking-[0.3em] text-[#8c7089] font-medium">{count} active connection{count !== 1 ? "s" : ""}</span>
      <div className="flex-1 h-px" style={{ background: "linear-gradient(90deg, rgba(217,134,149,0.3), transparent)" }} aria-hidden="true" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/connections")
      .then((r) => r.json())
      .then((json) => {
        if (json.error) setError(json.error);
        else setConnections(json.connections ?? []);
      })
      .catch(() => setError("Failed to load connections"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col relative selection:bg-[#d98695] selection:text-white">
      <AmbientBlobs />
      <TopHeader />
      <main className="relative z-10 flex-1 w-full max-w-lg md:max-w-3xl lg:max-w-5xl mx-auto px-4 md:px-6 pb-10 flex flex-col" role="main" aria-label="Active connections">
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="w-8 h-8 rounded-full border-2 border-[#d98695] border-t-transparent animate-spin" aria-label="Loading" />
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-[#d98695]">{error}</p>
          </div>
        ) : connections.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-4">
            <SectionLabel count={connections.length} />
            <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4" role="list" aria-label="Connection list">
              {connections.map((conn) => (
                <li key={conn.id}>
                  <ConnectionCard connection={conn} />
                </li>
              ))}
            </ul>
            <aside className="glass-panel rounded-xl p-3.5 flex items-start gap-2.5 mt-2" role="note">
              <span className="material-symbols-outlined text-sm text-[#d98695] shrink-0 mt-0.5" aria-hidden="true">timer</span>
              <p className="text-[11px] text-[#8c7089] leading-relaxed font-light">Connections with 24 hours of inactivity are automatically closed. Keep the conversation alive.</p>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
