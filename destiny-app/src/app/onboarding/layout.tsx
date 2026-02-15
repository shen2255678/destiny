// ============================================================
// DESTINY — Onboarding Layout
// "Soul Checkup" (靈魂體檢) shared shell
// Next.js 14 App Router · Tailwind CSS v4 · Server Component
// Active step highlighting is delegated to <StepIndicator>
// ============================================================

import Link from "next/link";
import StepIndicator from "./StepIndicator";

// ------------------------------------------------------------------
// Inline style helpers
// ------------------------------------------------------------------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 50%, #a8e6cf 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

// ------------------------------------------------------------------
// Layout
// ------------------------------------------------------------------
export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ============================================================
          TOP CHROME — logo + progress stepper
      ============================================================ */}
      <header className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-white/40">
        <div className="max-w-2xl mx-auto px-6 py-4">
          {/* Row 1: logo + eyebrow tag */}
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/"
              className="flex items-center gap-2 group"
              aria-label="DESTINY — return to home"
            >
              <span
                className="material-symbols-outlined text-xl text-primary animate-soft-pulse"
                style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                aria-hidden="true"
              >
                spa
              </span>
              <span className="font-sans text-base font-semibold tracking-widest text-[#5c4059] group-hover:text-primary transition-colors duration-300">
                DESTINY
              </span>
            </Link>

            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-panel
                         border border-primary/20 text-[10px] font-medium tracking-widest
                         uppercase text-[#8c7089]"
            >
              <span
                className="material-symbols-outlined text-xs text-primary"
                style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                aria-hidden="true"
              >
                favorite
              </span>
              靈魂體檢
            </span>
          </div>

          {/* Row 2: client step indicator (reads pathname, highlights active step) */}
          <StepIndicator />
        </div>
      </header>

      {/* ============================================================
          MAIN — page content, padded below the fixed header
      ============================================================ */}
      <main
        className="flex-1 flex flex-col pt-[128px] pb-16 px-6"
        id="main-content"
      >
        {/* Decorative background blobs */}
        <div
          className="fixed top-32 left-[5%] w-48 h-48 rounded-full opacity-15 pointer-events-none"
          style={{
            background: "radial-gradient(circle, #d98695 0%, transparent 70%)",
            filter: "blur(40px)",
          }}
          aria-hidden="true"
        />
        <div
          className="fixed bottom-20 right-[5%] w-56 h-56 rounded-full opacity-10 pointer-events-none"
          style={{
            background: "radial-gradient(circle, #a8e6cf 0%, transparent 70%)",
            filter: "blur(50px)",
          }}
          aria-hidden="true"
        />
        <div
          className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full opacity-[0.06] pointer-events-none"
          style={{
            background: "radial-gradient(circle, #f7c5a8 0%, transparent 65%)",
            filter: "blur(60px)",
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 max-w-2xl mx-auto w-full flex-1">
          {children}
        </div>
      </main>

      {/* ============================================================
          FOOTER — minimal legal note
      ============================================================ */}
      <footer className="py-4 text-center" role="contentinfo">
        <p className="text-[10px] text-[#8c7089]/60 tracking-wide">
          Your data is encrypted and never sold.&nbsp;·&nbsp;
          <span style={gradientText} className="font-medium">
            DESTINY
          </span>
          &nbsp;&copy; 2026
        </p>
      </footer>
    </div>
  );
}
