"use client";

// ============================================================
// DESTINY — Onboarding Step Indicator (client component)
// Reads current pathname to highlight the active step
// ============================================================

import { usePathname } from "next/navigation";

const steps = [
  { id: "birth-data",  label: "Birth Data",   href: "/onboarding/birth-data"  },
  { id: "rpv-test",    label: "Soul Test",     href: "/onboarding/rpv-test"    },
  { id: "photos",      label: "Photos",        href: "/onboarding/photos"      },
  { id: "soul-report", label: "Soul Report",   href: "/onboarding/soul-report" },
] as const;

export default function StepIndicator() {
  const pathname = usePathname();

  // Derive current step index from the pathname
  const currentIndex = steps.findIndex((s) => pathname.startsWith(s.href));
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;

  return (
    <nav aria-label="Onboarding progress steps">
      <ol className="flex items-center gap-0" role="list">
        {steps.map((step, index) => {
          const isCompleted = index < activeIndex;
          const isActive = index === activeIndex;
          const isLast = index === steps.length - 1;

          // Visual states
          let circleBg: string;
          let circleBorder: string;
          let circleText: string;
          let labelColor: string;

          if (isCompleted) {
            circleBg = "#d98695";
            circleBorder = "#d98695";
            circleText = "#ffffff";
            labelColor = "#d98695";
          } else if (isActive) {
            circleBg = "rgba(217,134,149,0.12)";
            circleBorder = "#d98695";
            circleText = "#d98695";
            labelColor = "#5c4059";
          } else {
            circleBg = "rgba(255,255,255,0.5)";
            circleBorder = "rgba(217,134,149,0.2)";
            circleText = "#8c7089";
            labelColor = "#8c7089";
          }

          // Connector gradient — filled when preceding step is complete
          const connectorFilled = index < activeIndex;

          return (
            <li
              key={step.id}
              className="flex items-center flex-1 last:flex-none"
              role="listitem"
              aria-current={isActive ? "step" : undefined}
            >
              {/* Step node */}
              <div className="flex flex-col items-center gap-1 flex-shrink-0">
                {/* Circle */}
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center
                             text-[10px] font-semibold border-2 transition-all duration-400"
                  style={{
                    background: circleBg,
                    borderColor: circleBorder,
                    color: circleText,
                    boxShadow: isActive
                      ? "0 0 0 3px rgba(217,134,149,0.2)"
                      : "none",
                  }}
                  aria-hidden="true"
                >
                  {isCompleted ? (
                    <span
                      className="material-symbols-outlined"
                      style={{
                        fontSize: "14px",
                        fontVariationSettings: "'FILL' 1, 'wght' 600",
                      }}
                    >
                      check
                    </span>
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Label */}
                <span
                  className="text-[9px] font-medium tracking-wide whitespace-nowrap hidden sm:block
                             transition-colors duration-300"
                  style={{ color: labelColor }}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className="flex-1 h-px mx-1 mb-4 transition-all duration-500"
                  style={{
                    background: connectorFilled
                      ? "linear-gradient(90deg, #d98695 0%, #f7c5a8 100%)"
                      : "linear-gradient(90deg, rgba(217,134,149,0.2) 0%, rgba(247,197,168,0.15) 100%)",
                  }}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
