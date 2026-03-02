"use client";

import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { SIDEBAR_COLLAPSED, MOBILE_BP } from "@/components/NavBar";

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BP - 1}px)`);
    const onChange = (e: MediaQueryListEvent | MediaQueryList) =>
      setIsMobile(e.matches);
    onChange(mq);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const hideSidebar =
    pathname.startsWith("/login") || pathname.startsWith("/auth");

  return (
    <main
      style={{
        marginLeft: hideSidebar || isMobile ? 0 : SIDEBAR_COLLAPSED,
        minHeight: "100vh",
        transition: "margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      {children}
    </main>
  );
}
