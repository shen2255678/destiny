"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { RankingCard } from "@/components/RankingCard";
import { RankingDetailModal } from "@/components/RankingDetailModal";

interface SoulCard {
  id: string;
  display_name: string;
  natal_cache: Record<string, unknown> | null;
}

export interface RankingItem {
  cache_id: string;
  rank: number;
  harmony: number;
  lust: number;
  soul: number;
  primary_track: string;
  quadrant: string | null;
  labels: string[];
  tracks: Record<string, number>;
}

// ── Shared styles ────────────────────────────────────────────

const glassCard: React.CSSProperties = {
  background: "rgba(255,255,255,0.3)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.6)",
  borderRadius: 20,
  padding: "20px 24px",
};

const PAGE_SIZE = 20;

export function RankingClient({ yinCards }: { yinCards: SoulCard[] }) {
  const [selectedCardId, setSelectedCardId] = useState<string>(
    yinCards[0]?.id ?? ""
  );
  const [rankings, setRankings] = useState<RankingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [computedAt, setComputedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [selectedItem, setSelectedItem] = useState<RankingItem | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const loadingMore = useRef(false);

  const fetchRankings = useCallback(
    async (cardId: string, offset: number, append: boolean) => {
      if (!cardId) return;
      if (!append) setLoading(true);
      loadingMore.current = true;

      try {
        const res = await fetch(
          `/api/ranking?card_id=${cardId}&offset=${offset}&limit=${PAGE_SIZE}`
        );
        if (!res.ok) return;
        const data = await res.json();

        if (append) {
          setRankings((prev) => [...prev, ...data.rankings]);
        } else {
          setRankings(data.rankings);
        }
        setTotal(data.total);
        setComputedAt(data.computed_at);
        setHasMore(offset + PAGE_SIZE < data.total);
      } finally {
        setLoading(false);
        loadingMore.current = false;
      }
    },
    []
  );

  // Load when card changes
  useEffect(() => {
    if (selectedCardId) {
      setRankings([]);
      setTotal(0);
      fetchRankings(selectedCardId, 0, false);
    }
  }, [selectedCardId, fetchRankings]);

  // Infinite scroll
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore.current) {
          fetchRankings(selectedCardId, rankings.length, true);
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, selectedCardId, rankings.length, fetchRankings]);

  // ── Empty state: user hasn't activated 命緣模式 ──
  if (yinCards.length === 0) {
    return (
      <div
        style={{
          maxWidth: 600,
          margin: "80px auto",
          padding: "0 20px",
          textAlign: "center",
        }}
      >
        <div style={glassCard}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>☽</div>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: "#5c4059",
              marginBottom: 8,
            }}
          >
            尚未開啟命緣模式
          </h2>
          <p style={{ fontSize: 13, color: "#8c7089", lineHeight: 1.8, marginBottom: 20 }}>
            請前往「我的命盤」，將命盤模式切換為
            <strong style={{ color: "#b86e7d" }}>「☽ 命緣模式」</strong>，
            即可加入靈魂排行，探索與你最有共鳴的靈魂。
          </p>
          <a
            href="/me"
            style={{
              display: "inline-block",
              padding: "10px 28px",
              borderRadius: 999,
              background: "linear-gradient(135deg, #d98695, #b86e7d)",
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              textDecoration: "none",
              letterSpacing: "0.04em",
            }}
          >
            前往我的命盤
          </a>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "80px 20px 40px" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 32, color: "#d98695", marginBottom: 4 }}
        >
          leaderboard
        </span>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: "#5c4059",
            margin: "4px 0",
          }}
        >
          命運排行榜
        </h1>
        <p style={{ fontSize: 13, color: "#8c7089" }}>
          你的靈魂與誰共振最深？
        </p>
      </div>

      {/* Card selector */}
      <div style={{ ...glassCard, marginBottom: 20, padding: "14px 20px" }}>
        <label
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: "#b86e7d",
            letterSpacing: "0.06em",
            display: "block",
            marginBottom: 8,
          }}
        >
          選擇你的命盤
        </label>
        <select
          value={selectedCardId}
          onChange={(e) => setSelectedCardId(e.target.value)}
          style={{
            width: "100%",
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid rgba(217,134,149,0.3)",
            background: "rgba(255,255,255,0.5)",
            fontSize: 14,
            color: "#5c4059",
            outline: "none",
          }}
        >
          {yinCards.map((c) => (
            <option key={c.id} value={c.id}>
              {c.display_name}
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: "center", padding: "40px 0" }}>
          <div
            style={{
              width: 32,
              height: 32,
              border: "3px solid rgba(217,134,149,0.2)",
              borderTop: "3px solid #d98695",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
              margin: "0 auto 12px",
            }}
          />
          <p style={{ fontSize: 13, color: "#8c7089" }}>
            正在計算你的命運排行...
          </p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Rankings list */}
      {!loading && rankings.length === 0 && (
        <div
          style={{
            ...glassCard,
            textAlign: "center",
            padding: "32px 24px",
            color: "#8c7089",
            fontSize: 13,
          }}
        >
          尚無排名資料。系統正在計算中，請稍後再試。
        </div>
      )}

      {!loading &&
        rankings.map((item) => (
          <RankingCard
            key={item.cache_id}
            item={item}
            onClick={() => setSelectedItem(item)}
          />
        ))}

      {/* Computed at */}
      {!loading && computedAt && rankings.length > 0 && (
        <p
          style={{
            textAlign: "center",
            fontSize: 11,
            color: "#a08a9d",
            marginTop: 8,
          }}
        >
          資料更新於{" "}
          {new Date(computedAt).toLocaleString("zh-TW", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      )}

      {/* Infinite scroll sentinel */}
      <div ref={sentinelRef} style={{ height: 1 }} />

      {/* Detail modal */}
      {selectedItem && (
        <RankingDetailModal
          key={selectedItem.cache_id}
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}
