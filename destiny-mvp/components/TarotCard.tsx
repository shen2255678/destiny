// Import this component via next/dynamic to avoid SSR issues:
// const TarotCard = dynamic(() => import('@/components/TarotCard').then(m => m.TarotCard), { ssr: false })

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ---------------------------------------------------------------------------
// TypeScript interfaces
// ---------------------------------------------------------------------------

export interface TarotCardFront {
  archetype: string
  resonance: string[]
  vibeScore: number   // 0–100
  chemScore: number   // 0–100
}

export interface TarotCardBack {
  shadow: string[]
  toxicTraps: string[]
  reportText: string
}

export interface TarotCardProps {
  front: TarotCardFront
  back: TarotCardBack
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Animated score bar that grows from 0 → value on mount */
function ScoreBar({
  value,
  color,
  label,
}: {
  value: number
  color: string
  label: string
}) {
  return (
    <div style={{ marginBottom: '10px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '4px',
          fontSize: '11px',
          color: '#8b6370',
          fontWeight: 500,
          letterSpacing: '0.04em',
        }}
      >
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div
        style={{
          height: '6px',
          borderRadius: '3px',
          background: 'rgba(0,0,0,0.08)',
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.35 }}
          style={{
            height: '100%',
            borderRadius: '3px',
            background: color,
          }}
        />
      </div>
    </div>
  )
}

/** Small pill tag */
function PillTag({
  label,
  bg,
  color,
  border,
}: {
  label: string
  bg: string
  color: string
  border: string
}) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '3px 10px',
        borderRadius: '999px',
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.03em',
        background: bg,
        color: color,
        border: `1px solid ${border}`,
        margin: '3px 3px 3px 0',
      }}
    >
      {label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Card faces
// ---------------------------------------------------------------------------

function FrontFace({ front }: { front: TarotCardFront }) {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: '20px',
        // Pink/rose glassmorphism
        background: 'rgba(255, 255, 255, 0.35)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: '1px solid rgba(255,255,255,0.6)',
        boxShadow:
          '0 8px 32px rgba(217,134,149,0.18), inset 0 1px 0 rgba(255,255,255,0.7)',
        backfaceVisibility: 'hidden',
        WebkitBackfaceVisibility: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        padding: '28px 24px 20px',
        overflow: 'hidden',
      }}
    >
      {/* Decorative top glow */}
      <div
        style={{
          position: 'absolute',
          top: '-40px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '160px',
          height: '80px',
          borderRadius: '50%',
          background: 'rgba(217,134,149,0.22)',
          filter: 'blur(24px)',
          pointerEvents: 'none',
        }}
      />

      {/* ARCHETYPE label */}
      <div style={{ marginBottom: '6px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.18em',
            color: '#c0828e',
            textTransform: 'uppercase',
          }}
        >
          ARCHETYPE
        </span>
      </div>
      <div
        style={{
          fontSize: '26px',
          fontWeight: 800,
          color: '#b86e7d',
          letterSpacing: '-0.01em',
          lineHeight: 1.15,
          marginBottom: '16px',
          textShadow: '0 1px 8px rgba(184,110,125,0.18)',
        }}
      >
        {front.archetype}
      </div>

      {/* Divider */}
      <div
        style={{
          height: '1px',
          background:
            'linear-gradient(90deg, transparent, rgba(217,134,149,0.4), transparent)',
          marginBottom: '14px',
        }}
      />

      {/* Resonance tags */}
      <div style={{ marginBottom: '6px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: '#c0828e',
            textTransform: 'uppercase',
          }}
        >
          共鳴頻率
        </span>
      </div>
      <div style={{ marginBottom: '18px', flexWrap: 'wrap', display: 'flex' }}>
        {front.resonance.map((tag) => (
          <PillTag
            key={tag}
            label={tag}
            bg="rgba(217,134,149,0.14)"
            color="#b86e7d"
            border="rgba(217,134,149,0.35)"
          />
        ))}
      </div>

      {/* Score bars */}
      <div style={{ marginBottom: '8px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: '#c0828e',
            textTransform: 'uppercase',
          }}
        >
          相容評分
        </span>
      </div>
      <ScoreBar value={front.vibeScore} color="#d98695" label="Vibe Score" />
      <ScoreBar
        value={front.chemScore}
        color="#a8e6cf"
        label="Chemistry Score"
      />

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Bottom hint */}
      <div
        style={{
          textAlign: 'center',
          fontSize: '11px',
          color: '#c4a0aa',
          letterSpacing: '0.06em',
          paddingTop: '8px',
        }}
      >
        點擊翻面 ↓
      </div>
    </div>
  )
}

function BackFace({ back }: { back: TarotCardBack }) {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: '20px',
        // Deep mystical dark
        background: 'linear-gradient(145deg, #1c0533 0%, #0f0a1e 100%)',
        border: '1px solid #7c3aed',
        boxShadow:
          '0 8px 40px rgba(124,58,237,0.30), inset 0 1px 0 rgba(124,58,237,0.25)',
        backfaceVisibility: 'hidden',
        WebkitBackfaceVisibility: 'hidden',
        transform: 'rotateY(180deg)',
        display: 'flex',
        flexDirection: 'column',
        padding: '26px 22px 20px',
        overflow: 'hidden',
      }}
    >
      {/* Decorative purple glow top-right */}
      <div
        style={{
          position: 'absolute',
          top: '-20px',
          right: '-20px',
          width: '120px',
          height: '120px',
          borderRadius: '50%',
          background: 'rgba(124,58,237,0.20)',
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />

      {/* Header */}
      <div style={{ marginBottom: '14px' }}>
        <div
          style={{
            fontSize: '11px',
            fontWeight: 800,
            letterSpacing: '0.18em',
            color: '#c084fc',
            textTransform: 'uppercase',
            marginBottom: '2px',
          }}
        >
          Shadow Dynamics
        </div>
        <div
          style={{
            height: '1px',
            background:
              'linear-gradient(90deg, #7c3aed, transparent)',
          }}
        />
      </div>

      {/* Shadow tags */}
      <div style={{ marginBottom: '4px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: '#a78bfa',
            textTransform: 'uppercase',
          }}
        >
          暗影標籤
        </span>
      </div>
      <div style={{ marginBottom: '14px', display: 'flex', flexWrap: 'wrap' }}>
        {back.shadow.map((tag) => (
          <PillTag
            key={tag}
            label={tag}
            bg="rgba(124,58,237,0.18)"
            color="#c084fc"
            border="rgba(124,58,237,0.50)"
          />
        ))}
      </div>

      {/* Toxic trap tags */}
      <div style={{ marginBottom: '4px' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.14em',
            color: '#f87171',
            textTransform: 'uppercase',
          }}
        >
          毒性陷阱
        </span>
      </div>
      <div style={{ marginBottom: '16px', display: 'flex', flexWrap: 'wrap' }}>
        {back.toxicTraps.map((tag) => (
          <PillTag
            key={tag}
            label={tag}
            bg="rgba(239,68,68,0.12)"
            color="#f87171"
            border="rgba(239,68,68,0.40)"
          />
        ))}
      </div>

      {/* Report panel */}
      <div
        style={{
          flex: 1,
          background: 'rgba(0,0,0,0.35)',
          borderRadius: '10px',
          borderLeft: '3px solid #7c3aed',
          padding: '12px 12px',
          overflowY: 'auto',
          marginBottom: '10px',
        }}
      >
        <p
          style={{
            fontSize: '12px',
            lineHeight: 1.7,
            color: '#d4b8f0',
            margin: 0,
          }}
        >
          {back.reportText}
        </p>
      </div>

      {/* Bottom hint */}
      <div
        style={{
          textAlign: 'center',
          fontSize: '11px',
          color: '#7c5fa0',
          letterSpacing: '0.06em',
        }}
      >
        ↑ 點擊翻面
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * TarotCard — 3D flip card with a light glassmorphism front and a dark
 * mystical back.  Click anywhere on the card to toggle.
 *
 * Usage example:
 * ```tsx
 * import dynamic from 'next/dynamic'
 * const TarotCard = dynamic(
 *   () => import('@/components/TarotCard').then(m => m.TarotCard),
 *   { ssr: false }
 * )
 *
 * <TarotCard
 *   front={{
 *     archetype: '靈魂探索者',
 *     resonance: ['深度連結', '感性共鳴', '靈性成長'],
 *     vibeScore: 88,
 *     chemScore: 76,
 *   }}
 *   back={{
 *     shadow: ['迴避依戀', '情感壓抑'],
 *     toxicTraps: ['過度付出', '邊界模糊'],
 *     reportText: '你們的吸引力建立在靈魂層次的深度共鳴之上，但需要注意迴避型依戀模式帶來的情感壁壘。',
 *   }}
 * />
 * ```
 */
export function TarotCard({ front, back }: TarotCardProps) {
  const [isFlipped, setIsFlipped] = useState(false)

  return (
    // Perspective wrapper — required for 3D to render correctly
    <div
      style={{
        width: '300px',
        height: '460px',
        perspective: '1200px',
        cursor: 'pointer',
      }}
      onClick={() => setIsFlipped((prev) => !prev)}
      role="button"
      aria-label={isFlipped ? '顯示正面' : '顯示背面'}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          setIsFlipped((prev) => !prev)
        }
      }}
    >
      {/* Animated inner card — hosts both faces via preserve-3d */}
      <motion.div
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.65, ease: [0.4, 0.0, 0.2, 1] }}
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d',
        }}
      >
        <FrontFace front={front} />
        <BackFace back={back} />
      </motion.div>
    </div>
  )
}

export default TarotCard
