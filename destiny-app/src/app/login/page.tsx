"use client";

/**
 * DESTINY — Login Page
 *
 * Usage: Rendered at /login
 * Glassmorphism healing light theme.
 * Form does not submit anywhere — UI only (preventDefault).
 *
 * Design tokens from globals.css:
 *   --primary: #d98695  --primary-dark: #b86e7d
 *   --text-main: #5c4059  --text-light: #8c7089
 *   .glass-panel — backdrop-blur + rgba white bg
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await login(email, password);

    if (result.error) {
      setError(result.error.message);
      setLoading(false);
      return;
    }

    router.push("/daily");
  }

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4 py-12"
      style={{
        background:
          "linear-gradient(135deg, #fdfbfb 0%, #fcecf0 40%, #fdf2e9 100%)",
      }}
    >
      {/* Back to home — top-left */}
      <div className="absolute top-6 left-6">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm font-medium transition-opacity hover:opacity-70"
          style={{ color: "#8c7089" }}
          aria-label="Back to home"
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "18px" }}
            aria-hidden="true"
          >
            arrow_back
          </span>
          Home
        </Link>
      </div>

      {/* Card */}
      <article
        className="glass-panel w-full max-w-md rounded-3xl px-8 py-10 sm:px-10 sm:py-12"
        aria-label="Login form"
      >
        {/* Logo */}
        <header className="flex flex-col items-center mb-8">
          <Link
            href="/"
            className="flex flex-col items-center gap-2 group"
            aria-label="DESTINY — go to home"
          >
            <div
              className="flex items-center justify-center w-14 h-14 rounded-2xl shadow-md transition-transform group-hover:scale-105"
              style={{
                background: "linear-gradient(135deg, #d98695, #b86e7d)",
              }}
              aria-hidden="true"
            >
              <span
                className="material-symbols-outlined text-white"
                style={{ fontSize: "28px" }}
              >
                spa
              </span>
            </div>
            <span
              className="text-2xl font-bold tracking-[0.18em] uppercase"
              style={{ color: "#5c4059", fontFamily: "var(--font-sans)" }}
            >
              DESTINY
            </span>
          </Link>

          <h1
            className="mt-4 text-base font-medium"
            style={{ color: "#8c7089" }}
          >
            Welcome back, soul.
          </h1>
        </header>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="email"
              className="text-sm font-medium"
              style={{ color: "#5c4059" }}
            >
              Email
            </label>
            <div className="relative">
              <span
                className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ fontSize: "18px", color: "#8c7089" }}
                aria-hidden="true"
              >
                mail
              </span>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl py-3 pl-10 pr-4 text-sm outline-none transition-all
                           bg-white/30 backdrop-blur-sm
                           border border-white/50
                           focus:border-[#d98695]/40 focus:bg-white/50 focus:ring-2 focus:ring-[#d98695]/20
                           placeholder:text-[#8c7089]/60"
                style={{ color: "#5c4059" }}
                aria-label="Email address"
              />
            </div>
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="password"
              className="text-sm font-medium"
              style={{ color: "#5c4059" }}
            >
              Password
            </label>
            <div className="relative">
              <span
                className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ fontSize: "18px", color: "#8c7089" }}
                aria-hidden="true"
              >
                lock
              </span>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl py-3 pl-10 pr-11 text-sm outline-none transition-all
                           bg-white/30 backdrop-blur-sm
                           border border-white/50
                           focus:border-[#d98695]/40 focus:bg-white/50 focus:ring-2 focus:ring-[#d98695]/20
                           placeholder:text-[#8c7089]/60"
                style={{ color: "#5c4059" }}
                aria-label="Password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 p-0.5 rounded transition-opacity hover:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/50"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: "18px", color: "#8c7089" }}
                  aria-hidden="true"
                >
                  {showPassword ? "visibility_off" : "visibility"}
                </span>
              </button>
            </div>
          </div>

          {/* Forgot password */}
          <div className="flex justify-end -mt-1">
            <Link
              href="/forgot-password"
              className="text-xs font-medium transition-opacity hover:opacity-70"
              style={{ color: "#d98695" }}
            >
              Forgot password?
            </Link>
          </div>

          {/* Error message */}
          {error && (
            <p
              className="text-xs text-center py-2 px-3 rounded-lg bg-red-50/80"
              style={{ color: "#e74c3c" }}
              role="alert"
            >
              {error}
            </p>
          )}

          {/* Login button */}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 w-full rounded-full py-3 text-sm font-semibold text-white
                       shadow-md transition-all duration-200
                       hover:shadow-lg hover:brightness-105 active:scale-[0.98]
                       focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/60
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
            style={{
              background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            }}
            aria-label="Login to your account"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        {/* Divider */}
        <div
          className="flex items-center gap-3 my-6"
          role="separator"
          aria-hidden="true"
        >
          <div
            className="flex-1 h-px"
            style={{ background: "rgba(92,64,89,0.12)" }}
          />
          <span className="text-xs font-medium" style={{ color: "#8c7089" }}>
            or
          </span>
          <div
            className="flex-1 h-px"
            style={{ background: "rgba(92,64,89,0.12)" }}
          />
        </div>

        {/* Google button */}
        <button
          type="button"
          onClick={() => {
            // TODO: wire up Google OAuth
          }}
          className="w-full flex items-center justify-center gap-2.5
                     glass-panel rounded-full py-3 text-sm font-medium
                     border border-white/50 transition-all duration-200
                     hover:bg-white/50 hover:shadow-md active:scale-[0.98]
                     focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/40"
          style={{ color: "#5c4059" }}
          aria-label="Continue with Google"
        >
          {/* Google 'G' SVG mark */}
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M17.64 9.2045C17.64 8.5663 17.5827 7.9527 17.4764 7.3636H9V10.845H13.8436C13.635 11.97 13.0009 12.9231 12.0477 13.5613V15.8195H14.9564C16.6582 14.2527 17.64 11.9454 17.64 9.2045Z"
              fill="#4285F4"
            />
            <path
              d="M9 18C11.43 18 13.4673 17.1941 14.9564 15.8195L12.0477 13.5613C11.2418 14.1013 10.2109 14.4204 9 14.4204C6.65591 14.4204 4.67182 12.8372 3.96409 10.71H0.957275V13.0418C2.43818 15.9831 5.48182 18 9 18Z"
              fill="#34A853"
            />
            <path
              d="M3.96409 10.71C3.78409 10.17 3.68182 9.5931 3.68182 9C3.68182 8.4068 3.78409 7.83 3.96409 7.29V4.9581H0.957275C0.347727 6.1731 0 7.5477 0 9C0 10.4522 0.347727 11.8268 0.957275 13.0418L3.96409 10.71Z"
              fill="#FBBC05"
            />
            <path
              d="M9 3.5795C10.3213 3.5795 11.5077 4.0336 12.4405 4.9254L15.0218 2.3440C13.4632 0.8918 11.4259 0 9 0C5.48182 0 2.43818 2.0168 0.957275 4.9581L3.96409 7.29C4.67182 5.1627 6.65591 3.5795 9 3.5795Z"
              fill="#EA4335"
            />
          </svg>
          Continue with Google
        </button>

        {/* Register link */}
        <p
          className="mt-7 text-center text-sm"
          style={{ color: "#8c7089" }}
        >
          New here?{" "}
          <Link
            href="/register"
            className="font-semibold transition-opacity hover:opacity-70"
            style={{ color: "#d98695" }}
          >
            Create your soul profile
          </Link>
        </p>
      </article>
    </main>
  );
}
