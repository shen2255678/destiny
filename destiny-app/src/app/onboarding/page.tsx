// ============================================================
// DESTINY — /onboarding root redirect
// Redirects to the first onboarding step: birth-data
// Next.js 14 App Router · Server Component
// ============================================================

import { redirect } from "next/navigation";

export default function OnboardingIndexPage() {
  redirect("/onboarding/birth-data");
}
