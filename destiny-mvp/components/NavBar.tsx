"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { motion, AnimatePresence } from "framer-motion";

const SIDEBAR_EXPANDED = 200;
const SIDEBAR_COLLAPSED = 56;
const MOBILE_BP = 768;

const NAV_ITEMS = [
  { label: "解析大廳", path: "/lounge", icon: "auto_awesome" },
  { label: "命運排行", path: "/ranking", icon: "leaderboard" },
  { label: "我的命盤", path: "/me", icon: "person" },
];

// Shared spring config for all sidebar animations
const SPRING = { type: "spring" as const, stiffness: 400, damping: 30 };

export function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BP - 1}px)`);
    const onChange = (e: MediaQueryListEvent | MediaQueryList) =>
      setIsMobile(e.matches);
    onChange(mq);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (pathname.startsWith("/login") || pathname.startsWith("/auth")) {
    return null;
  }

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  const glassStyle: React.CSSProperties = {
    background: "rgba(255,255,255,0.3)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    borderRight: "1px solid rgba(255,255,255,0.5)",
    boxShadow: "2px 0 16px rgba(217,134,149,0.08)",
  };

  // Desktop sidebar
  if (!isMobile) {
    return (
      <motion.aside
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
        animate={{ width: expanded ? SIDEBAR_EXPANDED : SIDEBAR_COLLAPSED }}
        transition={SPRING}
        style={{
          ...glassStyle,
          position: "fixed",
          top: 0,
          left: 0,
          height: "100vh",
          zIndex: 50,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            padding: "24px 0",
          }}
        >
          {/* Logo */}
          <Link
            href="/lounge"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              textDecoration: "none",
              height: 24,
              marginBottom: 32,
              paddingLeft: 18,
              overflow: "hidden",
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 20, color: "#d98695", flexShrink: 0 }}
            >
              auto_awesome
            </span>
            <motion.span
              animate={{ opacity: expanded ? 1 : 0, x: expanded ? 0 : -8 }}
              transition={{ ...SPRING, opacity: { duration: 0.15 } }}
              style={{
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: "0.2em",
                color: "#5c4059",
                whiteSpace: "nowrap",
                pointerEvents: expanded ? "auto" : "none",
              }}
            >
              DESTINY
            </motion.span>
          </Link>

          {/* Nav links */}
          <nav
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 4,
              flex: 1,
            }}
          >
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  title={item.label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    height: 40,
                    paddingLeft: 18,
                    textDecoration: "none",
                    fontSize: 13,
                    fontWeight: active ? 600 : 400,
                    color: active ? "#5c4059" : "#8c7089",
                    background: active
                      ? "rgba(217,134,149,0.12)"
                      : "transparent",
                    borderLeft: active
                      ? "3px solid #d98695"
                      : "3px solid transparent",
                    overflow: "hidden",
                    whiteSpace: "nowrap",
                  }}
                >
                  <span
                    className="material-symbols-outlined"
                    style={{
                      fontSize: 18,
                      color: active ? "#d98695" : "#8c7089",
                      flexShrink: 0,
                    }}
                  >
                    {item.icon}
                  </span>
                  <motion.span
                    animate={{
                      opacity: expanded ? 1 : 0,
                      x: expanded ? 0 : -8,
                    }}
                    transition={{ ...SPRING, opacity: { duration: 0.15 } }}
                    style={{
                      pointerEvents: expanded ? "auto" : "none",
                    }}
                  >
                    {item.label}
                  </motion.span>
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <div style={{ padding: "0 10px" }}>
            <button
              onClick={handleLogout}
              title="登出"
              style={{
                width: "100%",
                height: 36,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                background: "rgba(255,255,255,0.4)",
                border: "1px solid rgba(255,255,255,0.6)",
                borderRadius: 999,
                padding: 0,
                fontSize: 12,
                color: "#8c7089",
                cursor: "pointer",
                backdropFilter: "blur(4px)",
                overflow: "hidden",
                whiteSpace: "nowrap",
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 16, flexShrink: 0 }}
              >
                logout
              </span>
              <motion.span
                animate={{
                  opacity: expanded ? 1 : 0,
                  width: expanded ? "auto" : 0,
                }}
                transition={{ ...SPRING, opacity: { duration: 0.15 } }}
                style={{ overflow: "hidden" }}
              >
                登出
              </motion.span>
            </button>
          </div>
        </div>
      </motion.aside>
    );
  }

  // Mobile: hamburger + slide-out sidebar
  return (
    <>
      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Open menu"
        style={{
          position: "fixed",
          top: 12,
          left: 12,
          zIndex: 60,
          width: 40,
          height: 40,
          borderRadius: 12,
          border: "1px solid rgba(255,255,255,0.6)",
          background: "rgba(255,255,255,0.4)",
          backdropFilter: "blur(8px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(217,134,149,0.1)",
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 22, color: "#5c4059" }}
        >
          menu
        </span>
      </button>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setMobileOpen(false)}
              style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,0.3)",
                zIndex: 70,
              }}
            />

            <motion.aside
              initial={{ x: -SIDEBAR_EXPANDED }}
              animate={{ x: 0 }}
              exit={{ x: -SIDEBAR_EXPANDED }}
              transition={SPRING}
              style={{
                ...glassStyle,
                position: "fixed",
                top: 0,
                left: 0,
                width: SIDEBAR_EXPANDED,
                height: "100vh",
                zIndex: 80,
              }}
            >
              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Close menu"
                style={{
                  position: "absolute",
                  top: 12,
                  right: 12,
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  border: "none",
                  background: "transparent",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 20, color: "#5c4059" }}
                >
                  close
                </span>
              </button>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  height: "100%",
                  padding: "24px 0",
                }}
              >
                <Link
                  href="/lounge"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    textDecoration: "none",
                    padding: "0 20px",
                    marginBottom: 32,
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

                <nav
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                    flex: 1,
                  }}
                >
                  {NAV_ITEMS.map((item) => {
                    const active = pathname === item.path;
                    return (
                      <Link
                        key={item.path}
                        href={item.path}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          padding: "10px 20px",
                          textDecoration: "none",
                          fontSize: 13,
                          fontWeight: active ? 600 : 400,
                          color: active ? "#5c4059" : "#8c7089",
                          background: active
                            ? "rgba(217,134,149,0.12)"
                            : "transparent",
                          borderLeft: active
                            ? "3px solid #d98695"
                            : "3px solid transparent",
                        }}
                      >
                        <span
                          className="material-symbols-outlined"
                          style={{
                            fontSize: 18,
                            color: active ? "#d98695" : "#8c7089",
                          }}
                        >
                          {item.icon}
                        </span>
                        {item.label}
                      </Link>
                    );
                  })}
                </nav>

                <div style={{ padding: "0 16px" }}>
                  <button
                    onClick={handleLogout}
                    style={{
                      width: "100%",
                      background: "rgba(255,255,255,0.4)",
                      border: "1px solid rgba(255,255,255,0.6)",
                      borderRadius: 999,
                      padding: "8px 0",
                      fontSize: 12,
                      color: "#8c7089",
                      cursor: "pointer",
                      backdropFilter: "blur(4px)",
                    }}
                  >
                    登出
                  </button>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

export { SIDEBAR_COLLAPSED, SIDEBAR_EXPANDED, MOBILE_BP };
