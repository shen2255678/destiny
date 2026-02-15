"use client";

/**
 * DESTINY — Register Page
 *
 * Usage: Rendered at /register
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
import { register } from "@/lib/auth";

type Gender = "male" | "female" | "non-binary" | "";

const GENDER_OPTIONS: { value: Exclude<Gender, "">; label: string }[] = [
  { value: "male", label: "男性" },
  { value: "female", label: "女性" },
  { value: "non-binary", label: "非二元" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [gender, setGender] = useState<Gender>("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await register(email, password);

    if (result.error) {
      setError(result.error.message);
      setLoading(false);
      return;
    }

    router.push("/onboarding/birth-data");
  }

  const passwordMismatch =
    confirmPassword.length > 0 && password !== confirmPassword;

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
        aria-label="Registration form"
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
            Begin your soul reading.
          </h1>
        </header>

        {/* Form */}
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="reg-email"
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
                id="reg-email"
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
              htmlFor="reg-password"
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
                id="reg-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
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

          {/* Confirm Password */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="reg-confirm"
              className="text-sm font-medium"
              style={{ color: "#5c4059" }}
            >
              Confirm Password
            </label>
            <div className="relative">
              <span
                className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ fontSize: "18px", color: "#8c7089" }}
                aria-hidden="true"
              >
                lock_reset
              </span>
              <input
                id="reg-confirm"
                type={showConfirm ? "text" : "password"}
                autoComplete="new-password"
                required
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                aria-invalid={passwordMismatch}
                aria-describedby={
                  passwordMismatch ? "confirm-error" : undefined
                }
                className={[
                  "w-full rounded-xl py-3 pl-10 pr-11 text-sm outline-none transition-all",
                  "bg-white/30 backdrop-blur-sm",
                  "border",
                  passwordMismatch
                    ? "border-red-400/60 focus:border-red-400/60 focus:ring-2 focus:ring-red-300/20"
                    : "border-white/50 focus:border-[#d98695]/40 focus:ring-2 focus:ring-[#d98695]/20",
                  "focus:bg-white/50 placeholder:text-[#8c7089]/60",
                ].join(" ")}
                style={{ color: "#5c4059" }}
                aria-label="Confirm password"
              />
              <button
                type="button"
                onClick={() => setShowConfirm((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 p-0.5 rounded transition-opacity hover:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/50"
                aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: "18px", color: "#8c7089" }}
                  aria-hidden="true"
                >
                  {showConfirm ? "visibility_off" : "visibility"}
                </span>
              </button>
            </div>
            {passwordMismatch && (
              <p
                id="confirm-error"
                className="text-xs mt-0.5"
                style={{ color: "#e74c3c" }}
                role="alert"
              >
                Passwords do not match.
              </p>
            )}
          </div>

          {/* Gender */}
          <fieldset className="flex flex-col gap-2">
            <legend
              className="text-sm font-medium mb-1"
              style={{ color: "#5c4059" }}
            >
              Gender
            </legend>
            <div
              className="grid grid-cols-3 gap-2"
              role="radiogroup"
              aria-label="Select your gender"
            >
              {GENDER_OPTIONS.map((opt) => {
                const isSelected = gender === opt.value;
                return (
                  <label
                    key={opt.value}
                    className={[
                      "relative flex items-center justify-center rounded-xl py-2.5 px-3 text-sm font-medium cursor-pointer",
                      "border transition-all duration-150 select-none",
                      "focus-within:ring-2 focus-within:ring-[#d98695]/40",
                      isSelected
                        ? "border-[#d98695]/60 bg-[#d98695]/10 text-[#b86e7d]"
                        : "border-white/50 bg-white/30 text-[#8c7089] hover:bg-white/50",
                    ].join(" ")}
                    aria-label={opt.label}
                  >
                    <input
                      type="radio"
                      name="gender"
                      value={opt.value}
                      checked={isSelected}
                      onChange={() => setGender(opt.value)}
                      className="sr-only"
                      required
                    />
                    {opt.label}
                  </label>
                );
              })}
            </div>
          </fieldset>

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

          {/* Create Account button */}
          <button
            type="submit"
            disabled={passwordMismatch || loading}
            className="mt-2 w-full rounded-full py-3 text-sm font-semibold text-white
                       shadow-md transition-all duration-200
                       hover:shadow-lg hover:brightness-105 active:scale-[0.98]
                       focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/60
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
            style={{
              background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            }}
            aria-label="Create your DESTINY account"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        {/* Login link */}
        <p
          className="mt-7 text-center text-sm"
          style={{ color: "#8c7089" }}
        >
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold transition-opacity hover:opacity-70"
            style={{ color: "#d98695" }}
          >
            Sign in
          </Link>
        </p>
      </article>
    </main>
  );
}
