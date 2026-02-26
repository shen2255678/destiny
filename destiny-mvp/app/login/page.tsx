"use client";

import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  async function handleGoogle() {
    const supabase = createClient();
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${location.origin}/auth/callback`,
      },
    });
  }

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4 py-12"
      style={{
        background:
          "linear-gradient(135deg, #fdfbfb 0%, #fcecf0 40%, #fdf2e9 100%)",
      }}
    >
      <article className="glass-panel w-full max-w-md rounded-3xl px-8 py-10 sm:px-10 sm:py-12">
        {/* Logo */}
        <header className="flex flex-col items-center mb-8">
          <div
            className="flex items-center justify-center w-14 h-14 rounded-2xl shadow-md mb-3"
            style={{
              background: "linear-gradient(135deg, #d98695, #b86e7d)",
            }}
          >
            <span
              className="material-symbols-outlined text-white"
              style={{ fontSize: "28px" }}
            >
              auto_awesome
            </span>
          </div>
          <span
            className="text-2xl font-bold tracking-[0.18em] uppercase"
            style={{ color: "#5c4059" }}
          >
            DESTINY
          </span>
          <p
            className="mt-2 text-sm text-center leading-relaxed"
            style={{ color: "#8c7089" }}
          >
            We don&apos;t match faces.
            <br />
            We match Source Codes.
          </p>
        </header>

        {/* Google OAuth Button */}
        <button
          type="button"
          onClick={handleGoogle}
          className="w-full flex items-center justify-center gap-3 py-3 rounded-full text-sm font-medium transition-all duration-200 hover:shadow-md active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d98695]/40"
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            color: "#ffffff",
            boxShadow: "0 4px 14px rgba(217, 134, 149, 0.35)",
          }}
        >
          {/* Google G SVG */}
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M17.64 9.2045C17.64 8.5663 17.5827 7.9527 17.4764 7.3636H9V10.845H13.8436C13.635 11.97 13.0009 12.9231 12.0477 13.5613V15.8195H14.9564C16.6582 14.2527 17.64 11.9454 17.64 9.2045Z" fill="#4285F4"/>
            <path d="M9 18C11.43 18 13.4673 17.1941 14.9564 15.8195L12.0477 13.5613C11.2418 14.1013 10.2109 14.4204 9 14.4204C6.65591 14.4204 4.67182 12.8372 3.96409 10.71H0.957275V13.0418C2.43818 15.9831 5.48182 18 9 18Z" fill="#34A853"/>
            <path d="M3.96409 10.71C3.78409 10.17 3.68182 9.5931 3.68182 9C3.68182 8.4068 3.78409 7.83 3.96409 7.29V4.9581H0.957275C0.347727 6.1731 0 7.5477 0 9C0 10.4522 0.347727 11.8268 0.957275 13.0418L3.96409 10.71Z" fill="#FBBC05"/>
            <path d="M9 3.5795C10.3213 3.5795 11.5077 4.0336 12.4405 4.9254L15.0218 2.3440C13.4632 0.8918 11.4259 0 9 0C5.48182 0 2.43818 2.0168 0.957275 4.9581L3.96409 7.29C4.67182 5.1627 6.65591 3.5795 9 3.5795Z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <p className="mt-6 text-center text-xs" style={{ color: "#8c7089" }}>
          登入即表示同意服務條款與隱私政策
        </p>
      </article>
    </main>
  );
}
