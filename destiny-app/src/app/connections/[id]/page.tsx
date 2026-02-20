"use client";

import Link from "next/link";
import { useEffect, useRef, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { useParams } from "next/navigation";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: string;
  sender_id: string;
  content: string;
  created_at: string;
  is_self: boolean;
}

interface OtherUser {
  id: string;
  archetype_name: string | null;
  display_name: string | null;
}

interface ConnectionDetail {
  id: string;
  status: string;
  sync_level: number;
  message_count: number;
  last_activity: string;
  tags: string[];
  other_user: OtherUser;
  blurred_photo_url: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getNextLevelTarget(syncLevel: number): number {
  return syncLevel === 1 ? 10 : 50;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function AmbientBlobs() {
  return (
    <>
      <div className="absolute top-[-12%] right-[-8%] w-[45%] h-[45%] rounded-full bg-[#f7c5a8] opacity-20 blur-[90px] pointer-events-none" aria-hidden="true" />
      <div className="absolute bottom-[10%] left-[-8%] w-[40%] h-[40%] rounded-full bg-[#a8e6cf] opacity-15 blur-[80px] pointer-events-none" aria-hidden="true" />
    </>
  );
}

function BlurredAvatar({ photoUrl, size = "md" }: { photoUrl: string | null; size?: "sm" | "md" }) {
  const sizeClass = size === "sm" ? "w-9 h-9" : "w-11 h-11";
  return (
    <div className={`${sizeClass} rounded-full shrink-0 relative overflow-hidden`} style={{ border: "1.5px solid rgba(255,255,255,0.7)" }} aria-hidden="true">
      {photoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photoUrl} alt="" className="w-full h-full object-cover" style={{ filter: "blur(8px)", transform: "scale(1.1)" }} />
      ) : (
        <>
          <div className="absolute inset-0 bg-gradient-to-br from-[#d98695] via-[#f7c5a8] to-[#fcecf0] opacity-70" />
          <div className="absolute inset-1.5 rounded-full bg-gradient-to-br from-rose-300 to-pink-400 blur-lg opacity-80" />
          <div className="absolute inset-0 backdrop-blur-sm" />
        </>
      )}
    </div>
  );
}

function SyncMeter({ level, count }: { level: number; count: number }) {
  const target = getNextLevelTarget(level);
  const pct = Math.min((count / target) * 100, 100);
  const barColor = level === 1 ? "#d98695" : level === 2 ? "#f7c5a8" : "#a8e6cf";
  return (
    <div className="flex items-center gap-2" aria-label={`Sync level ${level}, ${count} of ${target}`}>
      <span className="text-[10px] font-medium whitespace-nowrap" style={{ color: barColor }}>
        Lv.{level} · {count}/{target}
      </span>
      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(92,64,89,0.1)" }} role="presentation">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${barColor}77, ${barColor})` }} />
      </div>
    </div>
  );
}

function TopBar({ connection }: { connection: ConnectionDetail }) {
  return (
    <header className="relative z-20 glass-panel border-b border-white/40 px-4 py-3 flex items-center gap-3" role="banner">
      <Link href="/connections" className="w-9 h-9 rounded-full flex items-center justify-center text-[#8c7089] hover:text-[#d98695] hover:bg-white/40 transition-all duration-200 shrink-0" aria-label="Back to connections">
        <span className="material-symbols-outlined text-xl" aria-hidden="true">arrow_back</span>
      </Link>
      <BlurredAvatar photoUrl={connection.blurred_photo_url} />
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap gap-1.5 mb-1">
          {connection.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full font-medium text-[#b86e7d]" style={{ background: "rgba(217,134,149,0.1)", border: "1px solid rgba(217,134,149,0.2)" }}>
              {tag}
            </span>
          ))}
          {connection.tags.length === 0 && (
            <span className="text-[10px] text-[#8c7089] italic">{connection.other_user.archetype_name ?? "Connection"}</span>
          )}
        </div>
        <SyncMeter level={connection.sync_level} count={connection.message_count} />
      </div>
    </header>
  );
}

function BlurredPhotoSection({ photoUrl, syncLevel }: { photoUrl: string | null; syncLevel: number }) {
  if (syncLevel >= 2) return null;
  return (
    <div className="relative mx-4 mt-4 rounded-2xl overflow-hidden" style={{ height: 120, background: "linear-gradient(135deg, rgba(217,134,149,0.08), rgba(247,197,168,0.08))", border: "1px solid rgba(255,255,255,0.5)" }}>
      {photoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={photoUrl} alt="" className="w-full h-full object-cover" style={{ filter: "blur(20px)", transform: "scale(1.1)" }} />
      ) : (
        <div className="w-full h-full bg-gradient-to-br from-[#d98695]/20 via-[#f7c5a8]/20 to-[#a8e6cf]/20" />
      )}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5">
        <span className="material-symbols-outlined text-2xl text-white/70" aria-hidden="true">lock</span>
        <p className="text-xs text-white/80 font-medium">Unlocks at Lv.2</p>
        <p className="text-[10px] text-white/50">Keep chatting to reveal</p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const time = new Date(message.created_at).toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" });
  if (message.is_self) {
    return (
      <div className="flex justify-end" role="listitem">
        <div className="max-w-[72%] space-y-1">
          <div className="px-4 py-2.5 rounded-2xl rounded-br-md text-sm text-white leading-relaxed" style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)", boxShadow: "0 4px 12px rgba(217,134,149,0.25)" }}>
            {message.content}
          </div>
          <p className="text-[10px] text-[#8c7089] text-right pr-1">{time}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-end gap-2" role="listitem">
      <div className="w-7 h-7 rounded-full shrink-0 relative overflow-hidden" aria-hidden="true">
        <div className="absolute inset-0 bg-gradient-to-br from-[#d98695] to-[#f7c5a8] opacity-50" />
        <div className="absolute inset-1 rounded-full bg-gradient-to-br from-rose-200 to-pink-300 blur-sm opacity-70" />
      </div>
      <div className="max-w-[72%] space-y-1">
        <div className="px-4 py-2.5 rounded-2xl rounded-bl-md text-sm text-[#5c4059] leading-relaxed" style={{ background: "rgba(255,255,255,0.7)", border: "1px solid rgba(217,134,149,0.12)" }}>
          {message.content}
        </div>
        <p className="text-[10px] text-[#8c7089] pl-1">{time}</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export default function ChatPage() {
  const { id: connectionId } = useParams<{ id: string }>();
  const [connection, setConnection] = useState<ConnectionDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch initial data
  useEffect(() => {
    fetch(`/api/connections/${connectionId}/messages`)
      .then((r) => r.json())
      .then((json) => {
        if (json.connection) setConnection(json.connection);
        if (json.messages) setMessages(json.messages);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [connectionId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Supabase Realtime — subscribe to new messages for this connection
  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel(`messages:${connectionId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `connection_id=eq.${connectionId}`,
        },
        (payload) => {
          const newMsg = payload.new as Omit<Message, "is_self">;
          // Avoid duplicates (optimistic updates already added self messages)
          setMessages((prev) => {
            if (prev.some((m) => m.id === newMsg.id)) return prev;
            return [...prev, { ...newMsg, is_self: false }];
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [connectionId]);

  const handleSend = useCallback(async () => {
    const content = inputText.trim();
    if (!content || sending) return;

    setInputText("");
    setSending(true);

    // Optimistic update
    const tempId = `temp-${Date.now()}`;
    const optimistic: Message = {
      id: tempId,
      sender_id: "self",
      content,
      created_at: new Date().toISOString(),
      is_self: true,
    };
    setMessages((prev) => [...prev, optimistic]);
    if (connection) {
      setConnection((c) => c ? { ...c, message_count: c.message_count + 1 } : c);
    }

    try {
      const res = await fetch(`/api/connections/${connectionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      const json = await res.json();
      if (json.message) {
        // Replace temp message with real one
        setMessages((prev) => prev.map((m) => m.id === tempId ? { ...json.message, is_self: true } : m));
      }
    } catch (err) {
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      console.error("Failed to send message", err);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [connectionId, inputText, sending, connection]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-[#d98695] border-t-transparent animate-spin" aria-label="Loading" />
      </div>
    );
  }

  if (!connection) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-sm text-[#d98695]">Connection not found</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col relative overflow-hidden selection:bg-[#d98695] selection:text-white">
      <AmbientBlobs />

      {/* Top bar */}
      <TopBar connection={connection} />

      {/* Blurred photo (Lv.1 only) */}
      <BlurredPhotoSection photoUrl={connection.blurred_photo_url} syncLevel={connection.sync_level} />

      {/* Message list */}
      <main
        className="relative z-10 flex-1 overflow-y-auto px-4 py-4"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-[#8c7089] font-light italic">開始對話吧...</p>
          </div>
        ) : (
          <ul className="space-y-3 max-w-lg mx-auto" aria-label="Messages">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <li ref={bottomRef} aria-hidden="true" />
          </ul>
        )}
      </main>

      {/* Input bar */}
      <footer className="relative z-20 glass-panel border-t border-white/40 px-4 py-3" role="contentinfo">
        <div className="flex items-center gap-3 max-w-lg mx-auto">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Say something..."
            className="flex-1 px-4 py-2.5 rounded-full text-sm text-[#5c4059] placeholder:text-[#8c7089] outline-none focus:ring-1 focus:ring-[#d98695]/40 transition-all"
            style={{ background: "rgba(255,255,255,0.6)", border: "1px solid rgba(217,134,149,0.2)" }}
            aria-label="Message input"
            disabled={sending}
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || sending}
            className="w-10 h-10 rounded-full flex items-center justify-center text-white transition-all duration-200 shrink-0 disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_4px_12px_rgba(217,134,149,0.4)]"
            style={{ background: "linear-gradient(135deg, #d98695, #b86e7d)" }}
            aria-label="Send message"
          >
            <span className="material-symbols-outlined text-lg" aria-hidden="true">send</span>
          </button>
        </div>
      </footer>
    </div>
  );
}
