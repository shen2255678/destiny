"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function NavBar() {
  const router = useRouter();
  const pathname = usePathname();

  // Hide nav on public pages
  if (pathname.startsWith("/login") || pathname.startsWith("/auth")) {
    return null;
  }

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <nav
      style={{
        background: "rgba(255,255,255,0.3)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.5)",
        padding: "12px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "sticky",
        top: 0,
        zIndex: 50,
        boxShadow: "0 2px 16px rgba(217,134,149,0.08)",
      }}
    >
      <Link
        href="/lounge"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          textDecoration: "none",
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 20, color: "#d98695" }}
        >
          auto_awesome
        </span>
        <span
          style={{
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: "0.2em",
            color: "#5c4059",
          }}
        >
          DESTINY
        </span>
      </Link>

      <button
        onClick={handleLogout}
        style={{
          background: "rgba(255,255,255,0.4)",
          border: "1px solid rgba(255,255,255,0.6)",
          borderRadius: 999,
          padding: "6px 16px",
          fontSize: 12,
          color: "#8c7089",
          cursor: "pointer",
          backdropFilter: "blur(4px)",
          transition: "all 0.2s",
        }}
      >
        登出
      </button>
    </nav>
  );
}
