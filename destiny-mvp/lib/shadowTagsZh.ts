/**
 * Shadow / psychological tag → Chinese description lookup.
 *
 * Source of truth: astro-service/prompt_manager.py _PSYCH_TAG_ZH
 * To regenerate: cd astro-service && python export_tags.py
 */
import tagTranslations from "./tagTranslations.json";

export const SHADOW_TAG_ZH: Record<string, string> =
  tagTranslations as Record<string, string>;

/**
 * psychological_triggers → Chinese description
 * e.g. "attachment_trap: anxious_avoidant" → "焦慮型追、迴避型逃——上癮也消耗的追逐陷阱"
 */
export const PSYCH_TRIGGER_ZH: Record<string, string> = {
  "attachment_trap: anxious_avoidant": "焦慮型追、迴避型逃——越追越緊、越逃越遠的虐心陷阱",
  "intimacy_fear: soul_runner":        "靈魂逃兵——因為太懂你而恐懼，選擇逃回更安全但不那麼愛的地方",
  "attachment_healing: secure_base":   "安全感治癒——對方的包容奇蹟般撫平了你的焦慮，讓你學會真正卸下防備",
};

/** Translate a single shadow tag key → Chinese sentence, fallback to raw key */
export function translateShadowTag(tag: string): string {
  return SHADOW_TAG_ZH[tag] ?? tag;
}

/** Translate a single psych trigger string → Chinese, fallback to raw */
export function translatePsychTrigger(trigger: string): string {
  // Try exact match first
  if (PSYCH_TRIGGER_ZH[trigger]) return PSYCH_TRIGGER_ZH[trigger];
  // Try prefix match (e.g. "attachment_trap: anxious_avoidant" starts with "attachment_trap")
  for (const [key, val] of Object.entries(PSYCH_TRIGGER_ZH)) {
    if (trigger.startsWith(key.split(":")[0].trim())) return val;
  }
  return trigger;
}
