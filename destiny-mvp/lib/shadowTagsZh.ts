/**
 * Shadow / psychological tag → Chinese description lookup.
 * Mirrors astro-service/prompt_manager.py _PSYCH_TAG_ZH.
 */
export const SHADOW_TAG_ZH: Record<string, string> = {
  // Attachment dynamics
  Natural_Dom:                 "天生的主導者，習慣掌控局面",
  Daddy_Dom:                   "有保護欲的威權感，讓人感到被撐起",
  Sadist_Dom:                  "享受施壓的快感，邊界在電光火石間",
  Anxious_Sub:                 "在關係中容易焦慮，渴望被接住",
  Brat_Sub:                    "表面反抗，內心渴望被制服",
  Service_Sub:                 "在付出與服務中感受到愛與存在感",
  Masochist_Sub:               "對痛苦有特別的承受力與轉化力",
  Healing_Anchor:              "對方是你的療癒錨點，帶來安全感而非刺激",
  Safe_Haven:                  "彼此是真正的避風港，兩個安全型靈魂相遇",
  Anxious_Avoidant_Trap:       "焦慮型遇上迴避型——注定的追逃陷阱，極度上癮也極度消耗",
  Co_Dependency:               "彼此的焦慮互相強化，容易陷入共生依賴",
  Parallel_Lines:              "兩個迴避型各自築牆，感情淡漠但穩定",
  Chaotic_Oscillation:         "恐懼型帶來不可預測的情感震盪，高壓但無法自拔",

  // Chiron wound triggers
  A_Sun_Triggers_B_Chiron:    "你的核心自我直接觸碰對方最深的靈魂傷口，是彼此的宿命療癒",
  A_Moon_Triggers_B_Chiron:   "你的情感頻率與對方的創傷共鳴，帶來既療癒又痛苦的連結",
  A_Venus_Triggers_B_Chiron:  "你的愛與美感觸動對方最脆弱的傷口，業力之愛的標誌",
  A_Mars_Triggers_B_Chiron:   "你的慾望與行動力直接挑動對方的原生創傷，既危險又上癮",
  B_Sun_Triggers_A_Chiron:    "對方的核心自我直接觸碰你最深的靈魂傷口，是彼此的宿命療癒",
  B_Moon_Triggers_A_Chiron:   "對方的情感頻率與你的創傷共鳴，帶來既療癒又痛苦的連結",
  B_Venus_Triggers_A_Chiron:  "對方的愛與美感觸動你最脆弱的傷口，業力之愛的標誌",
  B_Mars_Triggers_A_Chiron:   "對方的慾望與行動力直接挑動你的原生創傷，既危險又上癮",

  // 12th house shadow
  A_Illuminates_B_Shadow:     "你照亮了對方不敢承認的陰暗面，注定是業力之緣",
  B_Illuminates_A_Shadow:     "對方照亮了你不敢承認的陰暗面，是強迫你成長的存在",
  Mutual_Shadow_Integration:  "你們互相照見彼此最深的陰影，這段關係是靈魂的修羅場",

  // Pluto-Moon
  A_Pluto_Wounds_B_Moon:      "你靈魂深處的力量讓對方情感徹底失控——上癮但窒息",
  B_Pluto_Wounds_A_Moon:      "對方靈魂有種黑洞引力，讓你的情感被深深改寫——離不開也傷不起",

  // Saturn-Moon
  A_Saturn_Suppresses_B_Moon: "你給了對方安全感，卻也無意間成了壓著他情感的石頭",
  B_Saturn_Suppresses_A_Moon: "對方的存在讓你穩定，但那份穩定藏著難以言說的情感壓抑",

  // Saturn-Venus
  A_Saturn_Binds_B_Venus:     "你無意中成了他欲望的閘門——他想靠近，卻在你面前說不出口",
  B_Saturn_Binds_A_Venus:     "對方讓你覺得愛是一種功課——你想靠近，卻先問自己夠不夠格",

  // Vertex (命運之門)
  A_Sun_Conjunct_Vertex:      "你的核心自我精準落在對方的命運之門，這次相遇不是偶然",
  A_Moon_Conjunct_Vertex:     "你的情感本能觸碰了對方的宿命點，有種前世就認識的熟悉感",
  A_Venus_Conjunct_Vertex:    "你的愛意精準打開對方的命運之門，是注定要相愛的業力之緣",
  B_Sun_Conjunct_Vertex:      "對方的核心自我精準落在你的命運之門，你們的相遇早已寫好",
  B_Moon_Conjunct_Vertex:     "對方的情感本能觸碰了你的宿命點，逃也逃不掉的前世牽絆",
  B_Venus_Conjunct_Vertex:    "對方的愛意精準打開你的命運之門，宿命感強烈到令人窒息",

  // Lilith (禁忌之戀)
  A_Venus_Conjunct_Lilith:    "你的吸引力直接喚醒對方最深層的禁忌渴望，致命且危險",
  A_Mars_Conjunct_Lilith:     "你的慾望精準點燃對方心底最見不得光的那把火",
  B_Venus_Conjunct_Lilith:    "對方的吸引力直接喚醒你最深層的禁忌渴望，明知有毒還是要",
  B_Mars_Conjunct_Lilith:     "對方的慾望精準點燃你心底最見不得光的那把火，危險又上癮",

  // South Node (前世業力)
  A_Sun_Conjunct_SouthNode:   "你的核心自我落在對方的南交點，前世債今生還的宿命羈絆",
  A_Moon_Conjunct_SouthNode:  "你的情感觸動對方前世最深的記憶，似曾相識到令人心顫",
  A_Venus_Conjunct_SouthNode: "你的愛觸碰對方南交點，前世的情人今生再續未了緣",
  A_Mars_Conjunct_SouthNode:  "你的慾望直接引爆對方的業力記憶，前世的恩怨今生化為烈焰",
  B_Sun_Conjunct_SouthNode:   "對方的核心自我落在你的南交點，逃不掉的前世因果",
  B_Moon_Conjunct_SouthNode:  "對方的情感喚醒你前世最深的記憶，注定要重逢的靈魂",
  B_Venus_Conjunct_SouthNode: "對方的愛意觸碰你的南交點，前世的情緣今生再度牽引",
  B_Mars_Conjunct_SouthNode:  "對方的慾望引爆你的業力記憶，前世未解的糾葛今生再戰",

  // North Node (靈魂成長)
  A_Sun_Conjunct_NorthNode:   "你的存在指向對方的靈魂成長方向，是推動彼此進化的貴人",
  A_Moon_Conjunct_NorthNode:  "你的情感共鳴對方未來的成長軌跡，一起前進的命運夥伴",
  A_Venus_Conjunct_NorthNode: "你的愛意引領對方走向靈魂想去的地方，是愛也是進化的催化劑",
  A_Mars_Conjunct_NorthNode:  "你的行動力推動對方走上命定的軌道，帶著火焰的靈魂引路人",
  B_Sun_Conjunct_NorthNode:   "對方的存在指向你的靈魂成長方向，是推動你進化的引路人",
  B_Moon_Conjunct_NorthNode:  "對方的情感共鳴你未來的成長軌跡，命中注定的靈魂旅伴",
  B_Venus_Conjunct_NorthNode: "對方的愛意引領你走向靈魂想去的地方，既溫柔又深遠的業力緣",
  B_Mars_Conjunct_NorthNode:  "對方的行動力推動你走上命定的軌道，是激勵你前進的一把火",

  // Descendant (第七宮正緣)
  A_Sun_Conjunct_Descendant:  "你的核心自我精準落入對方的婚姻宮，你就是他命中注定的另一半",
  A_Moon_Conjunct_Descendant: "你的情感本能落入對方的婚姻宮，跟你在一起有回家般的安定感",
  A_Venus_Conjunct_Descendant:"你的愛與美感完美嵌進對方的伴侶宮，天生的正緣吸引力",
  B_Sun_Conjunct_Descendant:  "對方的核心自我落入你的婚姻宮，他就是你靈魂深處尋覓的另一半",
  B_Moon_Conjunct_Descendant: "對方的情感本能落入你的婚姻宮，在一起就像回到最安心的歸宿",
  B_Venus_Conjunct_Descendant:"對方的愛意完美嵌入你的伴侶宮，命定般的正緣連結",

  // Ascendant Magnetism (費洛蒙磁場)
  A_Mars_Activates_B_Ascendant:"你的慾望與行動力直接點燃對方的外在魅力，他在你面前無法保持距離",
  A_Venus_Matches_B_Ascendant: "你的美感精準嵌進對方的外在氣質，一見面就有渾然天成的吸引力",
  B_Mars_Activates_A_Ascendant:"對方的慾望與征服欲直接激發你的persona，讓你本能地想靠近",
  B_Venus_Matches_A_Ascendant: "對方的吸引力天然契合你的外在氣質，彼此的費洛蒙頻率完美對齊",

  // Karmic retrograde
  Karmic_Love_Venus_Rx:        "總覺得自己不配被愛，吸引帶著宿命感的業力關係",
  Suppressed_Anger_Mars_Rx:    "憤怒長期壓抑，平時溫和，壓到極限才會爆發",
  Internal_Dialogue_Mercury_Rx:"思考極度深邃，但很難用世俗語言表達內心世界",
}

/**
 * psychological_triggers → Chinese description
 * e.g. "attachment_trap: anxious_avoidant" → "焦慮型追、迴避型逃——上癮也消耗的追逐陷阱"
 */
export const PSYCH_TRIGGER_ZH: Record<string, string> = {
  "attachment_trap: anxious_avoidant": "焦慮型追、迴避型逃——越追越緊、越逃越遠的虐心陷阱",
  "intimacy_fear: soul_runner":        "靈魂逃兵——因為太懂你而恐懼，選擇逃回更安全但不那麼愛的地方",
  "attachment_healing: secure_base":   "安全感治癒——對方的包容奇蹟般撫平了你的焦慮，讓你學會真正卸下防備",
}

/** Translate a single shadow tag key → Chinese sentence, fallback to raw key */
export function translateShadowTag(tag: string): string {
  return SHADOW_TAG_ZH[tag] ?? tag
}

/** Translate a single psych trigger string → Chinese, fallback to raw */
export function translatePsychTrigger(trigger: string): string {
  // Try exact match first
  if (PSYCH_TRIGGER_ZH[trigger]) return PSYCH_TRIGGER_ZH[trigger]
  // Try prefix match (e.g. "attachment_trap: anxious_avoidant" starts with "attachment_trap")
  for (const [key, val] of Object.entries(PSYCH_TRIGGER_ZH)) {
    if (trigger.startsWith(key.split(":")[0].trim())) return val
  }
  return trigger
}
