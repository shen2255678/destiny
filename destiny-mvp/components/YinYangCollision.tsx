"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Phase = "entering" | "collided" | "spinning" | "success" | "exiting";

interface YinYangCollisionProps {
  active: boolean;
  resolved: boolean;
  onExitComplete?: () => void;
}

const SIZE = 240;

// Yin-yang paths used by both bare and full versions
const yinYangPaths = (
  <>
    {/* Yin (left/black) half */}
    <path
      d="M120,0 A120,120 0 0,0 120,240 A60,60 0 0,0 120,120 A60,60 0 0,1 120,0 Z"
      fill="#1a1a1a"
    />
    {/* Yang (right/white) half */}
    <path
      d="M120,0 A120,120 0 0,1 120,240 A60,60 0 0,1 120,120 A60,60 0 0,0 120,0 Z"
      fill="#f0f0f0"
    />
    {/* White dot in black fish head (top) */}
    <circle cx="120" cy="60" r="14" fill="#f0f0f0" />
    {/* Black dot in white fish head (bottom) */}
    <circle cx="120" cy="180" r="14" fill="#1a1a1a" />
  </>
);

export default function YinYangCollision({
  active,
  resolved,
  onExitComplete,
}: YinYangCollisionProps) {
  const [phase, setPhase] = useState<Phase>("entering");
  const startTimeRef = useRef<number>(0);

  // Phase state machine
  useEffect(() => {
    if (!active) {
      setPhase("entering");
      return;
    }

    startTimeRef.current = Date.now();

    // entering → collided at 900ms (spring settles by then)
    const t1 = setTimeout(() => setPhase("collided"), 900);
    // collided → spinning at 1400ms
    const t2 = setTimeout(() => setPhase("spinning"), 1400);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [active]);

  // When API resolves, show success (guarantee minimum 3.5s from start)
  useEffect(() => {
    if (!resolved || phase === "success" || phase === "exiting") return;

    const elapsed = Date.now() - startTimeRef.current;
    const delay = Math.max(0, 3500 - elapsed);

    const t = setTimeout(() => setPhase("success"), delay);
    return () => clearTimeout(t);
  }, [resolved, phase]);

  // success → exiting after 1500ms
  useEffect(() => {
    if (phase !== "success") return;
    const t = setTimeout(() => setPhase("exiting"), 1500);
    return () => clearTimeout(t);
  }, [phase]);

  // exiting → fire callback after exit animation
  useEffect(() => {
    if (phase !== "exiting") return;
    const t = setTimeout(() => onExitComplete?.(), 600);
    return () => clearTimeout(t);
  }, [phase, onExitComplete]);

  // Bare yin-yang (no glow) for entering halves
  const bareSvg = (
    <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
      {yinYangPaths}
    </svg>
  );

  // Full symbol with glow ring for post-collision phases
  const fullSymbol = (
    <svg
      width={SIZE}
      height={SIZE}
      viewBox="-10 -10 260 260"
      style={{ overflow: "visible" }}
    >
      <defs>
        <filter id="yy-glow">
          <feGaussianBlur stdDeviation="8" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <circle
        cx="120"
        cy="120"
        r="125"
        fill="none"
        stroke="rgba(192,132,252,0.3)"
        strokeWidth="6"
        filter="url(#yy-glow)"
      />
      {yinYangPaths}
    </svg>
  );

  return (
    <AnimatePresence>
      {active && phase !== "exiting" ? (
        <motion.div
          key="yinyang-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.3 }}
          transition={{ duration: 0.5 }}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background:
              "radial-gradient(ellipse at center, rgba(30,20,35,0.92) 0%, rgba(15,10,20,0.97) 100%)",
            backdropFilter: "blur(8px)",
          }}
        >
          {/* Two halves flying in — uses clip-path on the FULL yin-yang so
              when both halves reach center, the shape is pixel-identical
              to the full symbol. No visual jump on phase transition. */}
          {phase === "entering" && (
            <div
              style={{
                position: "relative",
                width: SIZE,
                height: SIZE,
              }}
            >
              {/* Yin (black) half from left */}
              <motion.div
                initial={{ x: -300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 120,
                  damping: 18,
                }}
                style={{
                  position: "absolute",
                  inset: 0,
                  clipPath: "inset(0 50% 0 0)",
                }}
              >
                {bareSvg}
              </motion.div>
              {/* Yang (white) half from right */}
              <motion.div
                initial={{ x: 300, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 120,
                  damping: 18,
                }}
                style={{
                  position: "absolute",
                  inset: 0,
                  clipPath: "inset(0 0 0 50%)",
                }}
              >
                {bareSvg}
              </motion.div>
            </div>
          )}

          {/* Collision: full symbol appears (same shape, seamless) + flash burst */}
          {phase === "collided" && (
            <div style={{ position: "relative" }}>
              {/* Flash burst */}
              <motion.div
                initial={{ opacity: 1, scale: 0.8 }}
                animate={{ opacity: 0, scale: 2 }}
                transition={{ duration: 0.5 }}
                style={{
                  position: "absolute",
                  width: 300,
                  height: 300,
                  borderRadius: "50%",
                  background:
                    "radial-gradient(circle, rgba(192,132,252,0.5) 0%, transparent 70%)",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  pointerEvents: "none",
                }}
              />
              {fullSymbol}
            </div>
          )}

          {/* Spinning symbol */}
          {phase === "spinning" && (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{
                repeat: Infinity,
                duration: 3,
                ease: "linear",
              }}
            >
              <motion.div
                animate={{
                  filter: [
                    "drop-shadow(0 0 12px rgba(192,132,252,0.4))",
                    "drop-shadow(0 0 24px rgba(192,132,252,0.6))",
                    "drop-shadow(0 0 12px rgba(192,132,252,0.4))",
                  ],
                }}
                transition={{
                  repeat: Infinity,
                  duration: 1.5,
                  ease: "easeInOut",
                }}
              >
                {fullSymbol}
              </motion.div>
            </motion.div>
          )}

          {/* Success: symbol + text */}
          {phase === "success" && (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{
                  repeat: Infinity,
                  duration: 4,
                  ease: "linear",
                }}
                style={{
                  filter: "drop-shadow(0 0 20px rgba(192,132,252,0.5))",
                }}
              >
                {fullSymbol}
              </motion.div>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                style={{
                  marginTop: 32,
                  fontSize: 20,
                  fontWeight: 600,
                  letterSpacing: "0.15em",
                  color: "#e2cfe8",
                  textShadow: "0 0 16px rgba(192,132,252,0.5)",
                }}
              >
                計算成功!
              </motion.p>
            </>
          )}

          {/* Loading hint during spinning */}
          {phase === "spinning" && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: [0.4, 0.8, 0.4] }}
              transition={{ repeat: Infinity, duration: 2 }}
              style={{
                marginTop: 28,
                fontSize: 13,
                color: "#a090a8",
                letterSpacing: "0.08em",
              }}
            >
              解析命盤與命運共振中...
            </motion.p>
          )}
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
