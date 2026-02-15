import Link from "next/link";

// ============================================================
// DESTINY Landing Page — "We don't match faces, we match Source Codes."
// Next.js 14 App Router · Tailwind CSS v4 · Server Component
// ============================================================

// ---- Inline style helpers (used for gradient text since Tailwind
//      v4 does not ship a `bg-clip-text` utility by default) ------
const gradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #d98695 0%, #f7c5a8 50%, #a8e6cf 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const heroGradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #b86e7d 0%, #d98695 40%, #f7c5a8 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const tealGradientText: React.CSSProperties = {
  background: "linear-gradient(135deg, #a8e6cf 0%, #d98695 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

// ---- Avatar data for social proof ----------------------------
const avatars = [
  { initials: "S", bg: "bg-primary/80" },
  { initials: "M", bg: "bg-accent-teal/80" },
  { initials: "R", bg: "bg-accent-peach/80" },
  { initials: "A", bg: "bg-[#e6b3cc]/80" },
  { initials: "J", bg: "bg-[#b86e7d]/80" },
];

// ---- Trinity card data ---------------------------------------
const trinityCards = [
  {
    icon: "auto_awesome",
    title: "Cosmic Alignment",
    subtitle: "Vedic Astrology",
    description:
      "Your birth chart encodes the gravitational signature of your soul. D1 Rasi charts reveal who you are. D9 Navamsa charts reveal who you become in love.",
    accent: "from-[#f7c5a8]/30 to-[#d98695]/20",
    iconColor: "text-[#d98695]",
    tags: ["Rasi Chart", "Navamsa", "Dasha Periods"],
    tagStyle: "bg-[#f7c5a8]/30 text-[#b86e7d]",
    glow: "shadow-[0_0_30px_rgba(247,197,168,0.3)]",
  },
  {
    icon: "psychology",
    title: "Attachment Style",
    subtitle: "Depth Psychology",
    description:
      "How you bonded as a child shapes how you love as an adult. We decode Secure, Anxious, Avoidant, and Disorganised patterns to find your relational harmony.",
    accent: "from-[#a8e6cf]/30 to-[#9be3d5]/20",
    iconColor: "text-[#3d8b7a]",
    tags: ["Secure", "Anxious", "Avoidant"],
    tagStyle: "bg-[#a8e6cf]/40 text-[#2e6b5a]",
    glow: "shadow-[0_0_30px_rgba(168,230,207,0.3)]",
  },
  {
    icon: "balance",
    title: "Power Balance",
    subtitle: "Dynamic Architecture",
    description:
      "Every relationship has an energetic polarity. We map your dominance expression and submission depth so you meet someone whose power signature completes yours.",
    accent: "from-[#e6b3cc]/30 to-[#d98695]/20",
    iconColor: "text-[#8b4a6e]",
    tags: ["Dominant", "Submissive", "Switch"],
    tagStyle: "bg-[#e6b3cc]/40 text-[#6b3558]",
    glow: "shadow-[0_0_30px_rgba(230,179,204,0.3)]",
  },
];

// ---- Testimonial data -----------------------------------------
const testimonials = [
  {
    quote:
      "I've used every dating app. DESTINY was the first time I felt like a person, not a photo. My match messaged me first — her tags described me perfectly before we even spoke.",
    name: "Sophia L.",
    role: "Pisces Sun · Secure Attachment",
    initials: "SL",
    bg: "from-[#d98695]/20 to-[#f7c5a8]/20",
    avatarBg: "bg-primary/70",
    stars: 5,
  },
  {
    quote:
      "The algorithm matched me with someone whose power dynamic was the exact complement to mine. Three months in — we're still discovering each other.",
    name: "Marcus T.",
    role: "Scorpio Rising · Anxious-Secure",
    initials: "MT",
    bg: "from-[#a8e6cf]/20 to-[#9be3d5]/20",
    avatarBg: "bg-[#3d8b7a]/70",
    stars: 5,
  },
  {
    quote:
      "The progressive unlock system made me actually care before I saw her face. When the photo finally cleared — it matched the soul I already loved.",
    name: "Rin K.",
    role: "Capricorn Moon · Switch Dynamic",
    initials: "RK",
    bg: "from-[#e6b3cc]/20 to-[#d98695]/20",
    avatarBg: "bg-[#8b4a6e]/70",
    stars: 5,
  },
];

// ==============================================================
// PAGE COMPONENT
// ==============================================================
export default function Home() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      {/* ======================================================
          NAV
      ====================================================== */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-white/40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <span
              className="material-symbols-outlined text-2xl text-primary animate-soft-pulse"
              style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
            >
              spa
            </span>
            <span className="font-display text-xl font-semibold tracking-wide text-text-main group-hover:text-primary transition-colors duration-300">
              SourceCode
            </span>
          </Link>

          {/* Nav links — hidden on mobile */}
          <div className="hidden md:flex items-center gap-8">
            {[
              { label: "Manifesto", href: "#manifesto" },
              { label: "The Alchemy", href: "#alchemy" },
              { label: "Stories", href: "#stories" },
            ].map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-sm font-medium text-text-light hover:text-primary transition-colors duration-300 relative group"
              >
                {item.label}
                <span className="absolute -bottom-0.5 left-0 w-0 h-px bg-primary group-hover:w-full transition-all duration-300" />
              </Link>
            ))}
          </div>

          {/* Login CTA */}
          <Link
            href="/login"
            className="px-5 py-2 rounded-full glass-panel border border-primary/30 text-primary text-sm font-medium
                       hover:bg-primary hover:text-white transition-all duration-300 hover:shadow-[0_4px_20px_rgba(217,134,149,0.4)]"
          >
            Login
          </Link>
        </div>
      </nav>

      {/* ======================================================
          HERO
      ====================================================== */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 px-6 overflow-hidden">
        {/* Decorative blobs */}
        <div
          className="absolute top-20 left-[10%] w-64 h-64 rounded-full opacity-20 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, #d98695 0%, transparent 70%)",
            filter: "blur(40px)",
          }}
          aria-hidden="true"
        />
        <div
          className="absolute bottom-32 right-[8%] w-80 h-80 rounded-full opacity-15 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, #a8e6cf 0%, transparent 70%)",
            filter: "blur(50px)",
          }}
          aria-hidden="true"
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, #f7c5a8 0%, transparent 65%)",
            filter: "blur(60px)",
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 max-w-4xl mx-auto text-center">
          {/* Eyebrow label */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-primary/25 mb-8">
            <span
              className="material-symbols-outlined text-base text-primary"
              style={{ fontVariationSettings: "'FILL' 1, 'wght' 300" }}
            >
              auto_awesome
            </span>
            <span className="text-xs font-medium tracking-widest uppercase text-text-light">
              Precision Matchmaking · Est. 2026
            </span>
          </div>

          {/* Main headline */}
          <h1 className="text-5xl md:text-7xl font-display font-light leading-[1.1] tracking-tight mb-6">
            <span className="block text-text-main text-glow">
              We don&rsquo;t match
            </span>
            <span className="block" style={heroGradientText}>
              faces,
            </span>
            <span className="block text-text-main text-glow">
              we match{" "}
              <em
                className="not-italic font-semibold"
                style={heroGradientText}
              >
                Source Codes.
              </em>
            </span>
          </h1>

          {/* Sub-headline */}
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-text-light leading-relaxed mb-10 font-light">
            The world&apos;s first platform combining{" "}
            <span className="text-[#d98695] font-medium">Vedic Astrology</span>
            ,{" "}
            <span className="text-[#3d8b7a] font-medium">
              Attachment Psychology
            </span>
            , and{" "}
            <span className="text-[#8b4a6e] font-medium">
              Power Dynamics
            </span>{" "}
            into a single compatibility score — delivered in 3 daily curated
            matches.
          </p>

          {/* CTA + Secondary */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
            <Link
              href="/onboarding"
              className="group relative px-8 py-4 rounded-full font-medium text-white overflow-hidden
                         shadow-[0_8px_30px_rgba(217,134,149,0.45)] hover:shadow-[0_12px_40px_rgba(217,134,149,0.65)]
                         transition-all duration-300 hover:-translate-y-0.5"
              style={{
                background:
                  "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
              }}
            >
              <span className="relative z-10 flex items-center gap-2">
                <span
                  className="material-symbols-outlined text-xl"
                  style={{ fontVariationSettings: "'FILL' 1, 'wght' 300" }}
                >
                  fingerprint
                </span>
                Decode Your Soul
              </span>
              {/* Shimmer overlay */}
              <span
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{
                  background:
                    "linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%)",
                }}
                aria-hidden="true"
              />
            </Link>

            <Link
              href="#alchemy"
              className="px-8 py-4 rounded-full font-medium text-text-main glass-panel border border-primary/25
                         hover:border-primary/50 hover:text-primary transition-all duration-300 hover:-translate-y-0.5"
            >
              How It Works
            </Link>
          </div>

          {/* Social proof */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            {/* Avatar stack */}
            <div className="flex -space-x-3" role="img" aria-label="Member avatars">
              {avatars.map((avatar, i) => (
                <div
                  key={i}
                  className={`w-9 h-9 rounded-full ${avatar.bg} border-2 border-white/80
                              flex items-center justify-center text-xs font-semibold text-white
                              shadow-sm`}
                  aria-hidden="true"
                >
                  {avatar.initials}
                </div>
              ))}
            </div>
            <div className="text-left">
              <div className="flex items-center gap-1" aria-label="5 star rating">
                {[...Array(5)].map((_, i) => (
                  <span
                    key={i}
                    className="material-symbols-outlined text-sm text-[#f7c5a8]"
                    style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                    aria-hidden="true"
                  >
                    star
                  </span>
                ))}
              </div>
              <p className="text-xs text-text-light mt-0.5">
                <strong className="text-text-main">4,200+</strong> souls
                matched in beta
              </p>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div
          className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-float opacity-50"
          aria-hidden="true"
        >
          <span className="material-symbols-outlined text-2xl text-text-light">
            keyboard_arrow_down
          </span>
        </div>
      </section>

      {/* ======================================================
          MANIFESTO DIVIDER
      ====================================================== */}
      <section
        id="manifesto"
        className="py-24 px-6 relative overflow-hidden"
        aria-label="Manifesto"
      >
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-2xl md:text-3xl font-display font-light text-text-main leading-relaxed text-glow">
            &ldquo;Swipe culture reduced love to a thumbnail. We built a
            different kind of mirror — one that reflects your{" "}
            <span style={gradientText} className="font-medium">
              gravitational signature
            </span>
            , not your jawline.&rdquo;
          </p>
          <p className="mt-6 text-text-light text-sm tracking-widest uppercase">
            — DESTINY Manifesto
          </p>
        </div>
      </section>

      {/* ======================================================
          TRINITY SECTION  (#alchemy)
      ====================================================== */}
      <section
        id="alchemy"
        className="py-24 px-6 relative"
        aria-labelledby="alchemy-heading"
      >
        <div className="max-w-6xl mx-auto">
          {/* Section header */}
          <div className="text-center mb-16">
            <span className="inline-block px-3 py-1 rounded-full glass-panel border border-primary/20 text-xs tracking-widest uppercase text-text-light mb-4">
              The Alchemy
            </span>
            <h2
              id="alchemy-heading"
              className="text-4xl md:text-5xl font-display font-light text-text-main text-glow"
            >
              Three{" "}
              <span style={gradientText} className="font-semibold">
                invisible forces
              </span>
              <br />
              that govern who you love
            </h2>
          </div>

          {/* Cards grid */}
          <div className="grid md:grid-cols-3 gap-6">
            {trinityCards.map((card, i) => (
              <article
                key={i}
                className={`breathing-card glass-panel rounded-3xl p-8 relative overflow-hidden
                            bg-gradient-to-br ${card.accent} ${card.glow} transition-all duration-300`}
                aria-label={`${card.title} — ${card.subtitle}`}
              >
                {/* Background orb */}
                <div
                  className="absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-20 pointer-events-none"
                  style={{
                    background: `radial-gradient(circle, currentColor 0%, transparent 70%)`,
                    filter: "blur(20px)",
                  }}
                  aria-hidden="true"
                />

                {/* Icon */}
                <div className="mb-6">
                  <span
                    className={`material-symbols-outlined text-5xl ${card.iconColor}`}
                    style={{
                      fontVariationSettings: "'FILL' 0, 'wght' 200",
                    }}
                    aria-hidden="true"
                  >
                    {card.icon}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-xl font-semibold text-text-main mb-1">
                  {card.title}
                </h3>
                <p className="text-xs font-medium tracking-widest uppercase text-text-light mb-4">
                  {card.subtitle}
                </p>

                {/* Description */}
                <p className="text-text-light text-sm leading-relaxed mb-6">
                  {card.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-2" role="list" aria-label="Modes">
                  {card.tags.map((tag) => (
                    <span
                      key={tag}
                      role="listitem"
                      className={`px-3 py-1 rounded-full text-xs font-medium ${card.tagStyle}`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>

          {/* Mystery callout */}
          <div className="mt-12 glass-panel rounded-3xl p-8 text-center border border-white/50">
            <span
              className="material-symbols-outlined text-4xl text-primary/50 mb-3 block"
              style={{ fontVariationSettings: "'FILL' 0, 'wght' 100" }}
              aria-hidden="true"
            >
              lock
            </span>
            <p className="text-text-main text-lg md:text-xl font-display font-light">
              The algorithm is a{" "}
              <span style={gradientText} className="font-semibold">Black Box</span>.
            </p>
            <p className="mt-3 text-sm text-text-light max-w-md mx-auto leading-relaxed">
              We don&apos;t reveal how it works — only that it does. 3 curated
              matches delivered daily at 9 PM. No searching, no swiping — only receiving.
            </p>
          </div>
        </div>
      </section>

      {/* ======================================================
          FEATURE SECTION — "See beyond the veil"
      ====================================================== */}
      <section
        className="py-24 px-6 relative overflow-hidden"
        aria-labelledby="feature-heading"
      >
        {/* Background accent */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at 70% 50%, rgba(168,230,207,0.12) 0%, transparent 60%)",
          }}
          aria-hidden="true"
        />

        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          {/* Text column */}
          <div>
            <span className="inline-block px-3 py-1 rounded-full glass-panel border border-primary/20 text-xs tracking-widest uppercase text-text-light mb-6">
              Progressive Reveal
            </span>
            <h2
              id="feature-heading"
              className="text-4xl md:text-5xl font-display font-light text-text-main leading-tight mb-6 text-glow"
            >
              See beyond{" "}
              <span style={tealGradientText} className="font-semibold">
                the veil
              </span>
              <br />
              of superficiality
            </h2>
            <p className="text-text-light leading-relaxed mb-8">
              Photos stay Gaussian-blurred until you&apos;ve built a real
              connection through conversation. Because who you are after 50
              messages is the real you.
            </p>

            {/* Unlock tiers */}
            <div className="space-y-4" role="list" aria-label="Unlock levels">
              {[
                {
                  level: "Lv.1",
                  label: "Text Only",
                  desc: "0–10 exchanges · Your words are enough",
                  icon: "chat_bubble",
                  color: "text-[#d98695]",
                  barColor: "bg-[#d98695]",
                  width: "w-1/3",
                },
                {
                  level: "Lv.2",
                  label: "Voice + 50% Photo",
                  desc: "10–50 exchanges · Hear their soul",
                  icon: "mic",
                  color: "text-[#8b4a6e]",
                  barColor: "bg-[#e6b3cc]",
                  width: "w-2/3",
                },
                {
                  level: "Lv.3",
                  label: "Full Reveal",
                  desc: "50+ exchanges or 3 min call · Contact sharing unlocked",
                  icon: "visibility",
                  color: "text-[#3d8b7a]",
                  barColor: "bg-[#a8e6cf]",
                  width: "w-full",
                },
              ].map((tier) => (
                <div
                  key={tier.level}
                  role="listitem"
                  className="glass-panel rounded-2xl p-4 border border-white/50 hover:border-primary/30 transition-colors duration-300"
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={`material-symbols-outlined text-xl mt-0.5 ${tier.color}`}
                      style={{
                        fontVariationSettings: "'FILL' 0, 'wght' 300",
                      }}
                      aria-hidden="true"
                    >
                      {tier.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2 mb-1">
                        <span className={`text-xs font-bold tracking-widest ${tier.color}`}>
                          {tier.level}
                        </span>
                        <span className="text-sm font-medium text-text-main">
                          {tier.label}
                        </span>
                      </div>
                      <p className="text-xs text-text-light mb-2">{tier.desc}</p>
                      {/* Progress bar */}
                      <div className="h-1 rounded-full bg-white/40 overflow-hidden" aria-hidden="true">
                        <div
                          className={`h-full rounded-full ${tier.barColor} ${tier.width} opacity-70`}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Phone mockup column */}
          <div className="flex justify-center" aria-hidden="true">
            <div className="animate-float">
              {/* Phone shell */}
              <div
                className="relative w-64 rounded-[2.5rem] p-2 shadow-[0_30px_80px_rgba(217,134,149,0.35)]"
                style={{
                  background:
                    "linear-gradient(160deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.2) 100%)",
                  border: "1.5px solid rgba(255,255,255,0.7)",
                  backdropFilter: "blur(10px)",
                }}
              >
                {/* Notch */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-5 bg-[rgba(240,230,235,0.8)] rounded-b-2xl z-10" />

                {/* Screen */}
                <div
                  className="rounded-[2rem] overflow-hidden"
                  style={{ aspectRatio: "9/19" }}
                >
                  <div
                    className="h-full p-4 flex flex-col gap-3"
                    style={{
                      background:
                        "linear-gradient(160deg, #fdfbfb 0%, #fcecf0 60%, #fdf2e9 100%)",
                    }}
                  >
                    {/* App top bar */}
                    <div className="flex items-center justify-between pt-4">
                      <span className="text-xs font-semibold text-text-main">Today&apos;s Match</span>
                      <span className="text-xs text-text-light">3 of 3</span>
                    </div>

                    {/* Blurred photo placeholder */}
                    <div
                      className="rounded-2xl overflow-hidden relative"
                      style={{ aspectRatio: "1/1" }}
                    >
                      <div
                        className="w-full h-full"
                        style={{
                          background:
                            "linear-gradient(135deg, #e6b3cc 0%, #d98695 40%, #f7c5a8 100%)",
                          filter: "blur(8px)",
                          transform: "scale(1.05)",
                        }}
                      />
                      {/* Blur label */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span
                          className="material-symbols-outlined text-3xl text-white/80"
                          style={{ fontVariationSettings: "'FILL' 0, 'wght' 200" }}
                        >
                          blur_on
                        </span>
                        <span className="text-white/70 text-xs mt-1 font-medium">
                          Lv.1 · 3 exchanges
                        </span>
                      </div>
                    </div>

                    {/* Match tags */}
                    <div className="glass-panel rounded-xl p-3 border border-white/60">
                      <p className="text-[10px] text-text-light mb-2 uppercase tracking-wider">
                        Chameleon Tags
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {["Grounding", "Tender", "Wilful"].map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 rounded-full text-[9px] font-medium bg-primary/15 text-primary border border-primary/20"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Radar scores */}
                    <div className="glass-panel rounded-xl p-3 border border-white/60">
                      <p className="text-[10px] text-text-light mb-2 uppercase tracking-wider">
                        Compatibility Radar
                      </p>
                      <div className="space-y-1.5">
                        {[
                          { label: "Passion", value: 92, color: "#d98695" },
                          { label: "Stability", value: 78, color: "#a8e6cf" },
                          { label: "Communication", value: 88, color: "#f7c5a8" },
                        ].map((dim) => (
                          <div key={dim.label} className="flex items-center gap-2">
                            <span className="text-[9px] text-text-light w-20">{dim.label}</span>
                            <div className="flex-1 h-1 rounded-full bg-white/50">
                              <div
                                className="h-full rounded-full"
                                style={{ width: `${dim.value}%`, backgroundColor: dim.color }}
                              />
                            </div>
                            <span className="text-[9px] font-medium" style={{ color: dim.color }}>
                              {dim.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2 mt-auto">
                      <button
                        className="flex-1 py-2.5 rounded-xl glass-panel border border-white/60 text-xs text-text-light font-medium"
                        tabIndex={-1}
                        aria-label="Pass"
                      >
                        Pass
                      </button>
                      <button
                        className="flex-1 py-2.5 rounded-xl text-xs text-white font-medium shadow-md"
                        style={{
                          background:
                            "linear-gradient(135deg, #d98695, #b86e7d)",
                        }}
                        tabIndex={-1}
                        aria-label="Accept"
                      >
                        Accept
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating badge */}
              <div
                className="absolute -right-4 top-24 glass-panel rounded-2xl px-3 py-2 border border-white/60
                            shadow-[0_8px_20px_rgba(217,134,149,0.2)] max-w-[140px]"
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className="material-symbols-outlined text-base text-[#3d8b7a]"
                    style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                  >
                    verified
                  </span>
                  <span className="text-[10px] font-medium text-text-main leading-tight">
                    Dual Accept
                    <br />
                    Required
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ======================================================
          TESTIMONIALS  (#stories)
      ====================================================== */}
      <section
        id="stories"
        className="py-24 px-6"
        aria-labelledby="stories-heading"
      >
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <span className="inline-block px-3 py-1 rounded-full glass-panel border border-primary/20 text-xs tracking-widest uppercase text-text-light mb-4">
              Stories
            </span>
            <h2
              id="stories-heading"
              className="text-4xl md:text-5xl font-display font-light text-text-main text-glow"
            >
              Souls who found their{" "}
              <span style={gradientText} className="font-semibold">
                resonance
              </span>
            </h2>
          </div>

          {/* Testimonial cards */}
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <article
                key={i}
                className={`breathing-card glass-panel rounded-3xl p-8 bg-gradient-to-br ${t.bg}
                            border border-white/50 hover:border-primary/25 transition-all duration-300`}
                aria-label={`Testimonial from ${t.name}`}
              >
                {/* Stars */}
                <div className="flex gap-1 mb-5" role="img" aria-label="5 stars">
                  {[...Array(t.stars)].map((_, si) => (
                    <span
                      key={si}
                      className="material-symbols-outlined text-base text-[#f7c5a8]"
                      style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                      aria-hidden="true"
                    >
                      star
                    </span>
                  ))}
                </div>

                {/* Quote */}
                <blockquote className="text-text-light text-sm leading-relaxed mb-6 italic">
                  &ldquo;{t.quote}&rdquo;
                </blockquote>

                {/* Author */}
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-full ${t.avatarBg} flex items-center justify-center
                                text-white text-xs font-bold shadow-sm flex-shrink-0`}
                    aria-hidden="true"
                  >
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-main">{t.name}</p>
                    <p className="text-xs text-text-light">{t.role}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ======================================================
          FINAL CTA BANNER
      ====================================================== */}
      <section className="py-24 px-6" aria-labelledby="cta-heading">
        <div className="max-w-3xl mx-auto text-center glass-panel rounded-[2.5rem] p-16 border border-white/50
                        shadow-[0_20px_60px_rgba(217,134,149,0.2)]">
          <span
            className="material-symbols-outlined text-6xl text-primary/60 mb-6 block animate-soft-pulse"
            style={{ fontVariationSettings: "'FILL' 0, 'wght' 100" }}
            aria-hidden="true"
          >
            hub
          </span>
          <h2
            id="cta-heading"
            className="text-4xl md:text-5xl font-display font-light text-text-main text-glow mb-4"
          >
            Your soul has a{" "}
            <span style={heroGradientText} className="font-semibold">
              frequency.
            </span>
          </h2>
          <p className="text-text-light mb-10 max-w-md mx-auto leading-relaxed">
            Stop swiping. Start resonating. Upload your birth chart, answer 3
            questions, upload 2 photos — and let the universe do the rest.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-full text-white font-medium
                       shadow-[0_8px_30px_rgba(217,134,149,0.5)] hover:shadow-[0_12px_50px_rgba(217,134,149,0.7)]
                       transition-all duration-300 hover:-translate-y-1 text-lg"
            style={{
              background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            }}
          >
            <span
              className="material-symbols-outlined text-xl"
              style={{ fontVariationSettings: "'FILL' 1, 'wght' 300" }}
              aria-hidden="true"
            >
              fingerprint
            </span>
            Begin Your Reading
          </Link>
          <p className="mt-4 text-xs text-text-light">
            Free to join · No credit card · 3 daily matches
          </p>
        </div>
      </section>

      {/* ======================================================
          FOOTER
      ====================================================== */}
      <footer className="border-t border-white/40 glass-panel" role="contentinfo">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-12">
            {/* Brand column */}
            <div className="col-span-2 md:col-span-1">
              <Link href="/" className="flex items-center gap-2 mb-4 group" aria-label="DESTINY home">
                <span
                  className="material-symbols-outlined text-2xl text-primary"
                  style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                  aria-hidden="true"
                >
                  spa
                </span>
                <span className="font-display text-lg font-semibold text-text-main">
                  SourceCode
                </span>
              </Link>
              <p className="text-xs text-text-light leading-relaxed max-w-[180px]">
                Precision matchmaking for souls who are tired of shallow
                connections.
              </p>
            </div>

            {/* Platform links */}
            <nav aria-label="Platform navigation">
              <p className="text-xs font-semibold uppercase tracking-widest text-text-main mb-4">
                Platform
              </p>
              <ul className="space-y-2.5">
                {["Onboarding", "How It Works", "Pricing", "FAQ"].map(
                  (item) => (
                    <li key={item}>
                      <Link
                        href="#"
                        className="text-sm text-text-light hover:text-primary transition-colors duration-200"
                      >
                        {item}
                      </Link>
                    </li>
                  )
                )}
              </ul>
            </nav>

            {/* Resources links */}
            <nav aria-label="Resources navigation">
              <p className="text-xs font-semibold uppercase tracking-widest text-text-main mb-4">
                Resources
              </p>
              <ul className="space-y-2.5">
                {[
                  "Manifesto",
                  "Vedic Astrology Guide",
                  "Attachment Research",
                  "Privacy Policy",
                ].map((item) => (
                  <li key={item}>
                    <Link
                      href="#"
                      className="text-sm text-text-light hover:text-primary transition-colors duration-200"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            {/* Social + newsletter */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-text-main mb-4">
                Connect
              </p>
              {/* Social icons */}
              <div className="flex gap-3 mb-6" role="list" aria-label="Social media links">
                {[
                  { icon: "alternate_email", label: "Email" },
                  { icon: "language", label: "Website" },
                  { icon: "rss_feed", label: "Blog" },
                ].map((social) => (
                  <Link
                    key={social.label}
                    href="#"
                    role="listitem"
                    aria-label={social.label}
                    className="w-9 h-9 rounded-full glass-panel border border-white/60 flex items-center justify-center
                               text-text-light hover:text-primary hover:border-primary/40 transition-all duration-200"
                  >
                    <span
                      className="material-symbols-outlined text-base"
                      style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}
                      aria-hidden="true"
                    >
                      {social.icon}
                    </span>
                  </Link>
                ))}
              </div>
              {/* Mini newsletter */}
              <p className="text-xs text-text-light mb-2">
                Soul dispatches, monthly.
              </p>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="your@email.com"
                  aria-label="Email address for newsletter"
                  className="flex-1 min-w-0 px-3 py-2 rounded-xl glass-panel border border-white/50
                             text-xs text-text-main placeholder:text-text-light/60 outline-none
                             focus:border-primary/40 transition-colors duration-200 bg-transparent"
                />
                <button
                  type="button"
                  aria-label="Subscribe to newsletter"
                  className="px-3 py-2 rounded-xl text-white text-xs font-medium flex-shrink-0
                             shadow-[0_4px_15px_rgba(217,134,149,0.35)] hover:shadow-[0_6px_20px_rgba(217,134,149,0.5)]
                             transition-all duration-200"
                  style={{
                    background: "linear-gradient(135deg, #d98695, #b86e7d)",
                  }}
                >
                  Join
                </button>
              </div>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="pt-8 border-t border-white/30 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-text-light">
              &copy; 2026 DESTINY · All rights reserved
            </p>
            <p className="text-xs text-text-light flex items-center gap-1.5">
              Made with{" "}
              <span
                className="material-symbols-outlined text-sm text-primary"
                style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}
                aria-hidden="true"
              >
                favorite
              </span>{" "}
              and Vedic charts
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
