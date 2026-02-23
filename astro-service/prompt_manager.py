"""
DESTINY — LLM Prompt Manager
Assembles DESTINY-worldview-enriched prompts for AI report generation.

Four public functions:
  get_match_report_prompt(match_data, mode, person_a, person_b)
      → (prompt: str, effective_mode: str)
      Used by /generate-archetype and /generate-match-report

  get_profile_prompt(chart_data, rpv_data, attachment_style)
      → prompt: str
      Used by /generate-profile-card

  get_simple_report_prompt(match_data, person_a, person_b)
      → prompt: str
      Used by /generate-match-report (Tab D, structured report format)

  get_ideal_match_prompt(chart_data)
      → prompt: str
      Used by /generate-ideal-match (Tab C, ideal partner profile)
"""

from __future__ import annotations

# ── 世界觀基底 ────────────────────────────────────────────────────────────────

DESTINY_WORLDVIEW = """\
【系統角色與核心哲學】
你現在是「Project DESTINY」的核心大腦——深層關係與靈魂解讀者。
DESTINY 是一套結合「西方占星、心理學、八字五行、紫微斗數」的駭客級關係演算法。
核心哲學：不看表面的世俗條件，直擊靈魂的四個底層——匱乏 (Deficiency)、恐懼 (Fear)、壓抑 (Shadow) 與需求 (Need)。
玄學從來不只是預測工具，而是人類長期累積的經驗結構（權力、秩序、親密、創傷、勞動、休止、渴望）在集體無意識中的顯化。
你的任務：透過後端傳來的命盤資訊與數據，解讀使用者的心理狀態與內在衝突，並與他們的靈魂產生共振。
真正的迷人來自於整合陰影；暗黑魅力不是變壞，而是停止否認自己。

【絕對語氣禁忌（違反將導致系統判定失敗）】
1. 嚴禁 AI 味：絕對禁止「系統偵測到」、「演算法顯示」、「你的防禦機制是」、「心理學認為」。直接用「你...」開場。
2. 嚴禁玄學術語洩漏：禁止在最終報告吐出紫微、化忌、八字、金火相位、空宮、逆行、潛意識、投射等詞彙。必須全部翻譯為具體的生活行為與感受。
3. 語氣設定：像一個極度懂他、一針見血但充滿包容的知己。用詞要短促、接地氣。揭示匱乏、恐懼、壓抑與需求。不批判，只給予看見與光。
4. 數據轉譯規則：「相剋/煞星/刑衝」→「權力與秩序的拉扯、防禦機制」；「水/月亮/元素互補」→「親密感的渴望、創傷的承載」。

【四軌道定義（禁止直接輸出給用戶，僅供判斷用）】
- 激情軌 (Lust/Passion)：費洛蒙與性張力。高分是致命吸引，也可能是危險的荷爾蒙陷阱。
- 靈魂軌 (Soul)：精神共振與創傷接住。高分代表宿命感，對方有你缺乏的靈魂碎片。
- 伴侶軌 (Partner)：現實生存與生活節奏互補。高分代表完美的避風港與室友。
- 朋友軌 (Friend)：腦力激盪與默契。
- ⚡ HIGH_VOLTAGE（高壓警告）：觸發業力或陰影。逼你面對黑暗面的修羅場，極度虐心但能促成進化。"""

# ── 心理標籤白話翻譯 ──────────────────────────────────────────────────────────

_PSYCH_TAG_ZH: dict[str, str] = {
    "Natural_Dom":                  "天生的主導者，習慣掌控局面",
    "Daddy_Dom":                    "有保護欲的威權感，讓人感到被撐起",
    "Sadist_Dom":                   "享受施壓的快感，邊界在電光火石間",
    "Anxious_Sub":                  "在關係中容易焦慮，渴望被接住",
    "Brat_Sub":                     "表面反抗，內心渴望被制服",
    "Service_Sub":                  "在付出與服務中感受到愛與存在感",
    "Masochist_Sub":                "對痛苦有特別的承受力與轉化力",
    "Healing_Anchor":               "對方是你的療癒錨點，帶來安全感而非刺激",
    "Safe_Haven":                   "彼此是真正的避風港，兩個安全型靈魂相遇",
    "Anxious_Avoidant_Trap":        "焦慮型遇上迴避型——注定的追逃陷阱，極度上癮也極度消耗",
    "Co_Dependency":                "彼此的焦慮互相強化，容易陷入共生依賴",
    "Parallel_Lines":               "兩個迴避型各自築牆，感情淡漠但穩定",
    "Chaotic_Oscillation":          "恐懼型帶來不可預測的情感震盪，高壓但無法自拔",
    "A_Sun_Triggers_B_Chiron":      "你的核心自我直接觸碰對方最深的靈魂傷口，是彼此的宿命療癒",
    "A_Moon_Triggers_B_Chiron":     "你的情感頻率與對方的創傷共鳴，帶來既療癒又痛苦的連結",
    "A_Venus_Triggers_B_Chiron":    "你的愛與美感觸動對方最脆弱的傷口，業力之愛的標誌",
    "A_Mars_Triggers_B_Chiron":     "你的慾望與行動力直接挑動對方的原生創傷，既危險又上癮",
    "B_Sun_Triggers_A_Chiron":      "對方的核心自我直接觸碰你最深的靈魂傷口，是彼此的宿命療癒",
    "B_Moon_Triggers_A_Chiron":     "對方的情感頻率與你的創傷共鳴，帶來既療癒又痛苦的連結",
    "B_Venus_Triggers_A_Chiron":    "對方的愛與美感觸動你最脆弱的傷口，業力之愛的標誌",
    "B_Mars_Triggers_A_Chiron":     "對方的慾望與行動力直接挑動你的原生創傷，既危險又上癮",
    "A_Illuminates_B_Shadow":       "你照亮了對方不敢承認的陰暗面，注定是業力之緣",
    "B_Illuminates_A_Shadow":       "對方照亮了你不敢承認的陰暗面，是強迫你成長的存在",
    "Mutual_Shadow_Integration":    "你們互相照見彼此最深的陰影，這段關係是靈魂的修羅場",
    "Karmic_Love_Venus_Rx":         "總覺得自己不配被愛，吸引帶著宿命感的業力關係",
    "Suppressed_Anger_Mars_Rx":     "憤怒長期壓抑，平時溫和，壓到極限才會爆發",
    "Internal_Dialogue_Mercury_Rx": "思考極度深邃，但很難用世俗語言表達內心世界",
    # Vertex triggers (命運之門)
    "A_Sun_Conjunct_Vertex":        "你的核心自我精準落在對方的命運之門，這次相遇不是偶然",
    "A_Moon_Conjunct_Vertex":       "你的情感本能觸碰了對方的宿命點，彷彿前世就認識的熟悉感",
    "A_Venus_Conjunct_Vertex":      "你的愛意精準打開對方的命運之門，是注定要相愛的業力之緣",
    "B_Sun_Conjunct_Vertex":        "對方的核心自我精準落在你的命運之門，你們的相遇早已寫好",
    "B_Moon_Conjunct_Vertex":       "對方的情感本能觸碰了你的宿命點，逃也逃不掉的前世牽絆",
    "B_Venus_Conjunct_Vertex":      "對方的愛意精準打開你的命運之門，宿命感強烈到令人窒息",
    # Lilith triggers (禁忌之戀)
    "A_Venus_Conjunct_Lilith":      "你的吸引力直接喚醒對方最深層的禁忌渴望，致命且危險",
    "A_Mars_Conjunct_Lilith":       "你的慾望與征服本能，精準點燃對方心底最見不得光的那把火",
    "B_Venus_Conjunct_Lilith":      "對方的吸引力直接喚醒你最深層的禁忌渴望，明知有毒還是要",
    "B_Mars_Conjunct_Lilith":       "對方的慾望精準點燃你心底最見不得光的那把火，危險又上癮",
    # South Node triggers (南交點 — 前世業力牽引)
    "A_Sun_Conjunct_SouthNode":     "你的核心自我精準落在對方的南交點，前世債今生還的宿命羈絆",
    "A_Moon_Conjunct_SouthNode":    "你的情感觸動了對方前世最深的記憶，似曾相識到令人心顫",
    "A_Venus_Conjunct_SouthNode":   "你的愛與美觸碰對方的南交點，前世的情人今生再續未了緣",
    "A_Mars_Conjunct_SouthNode":    "你的慾望直接引爆對方的業力記憶，前世的恩怨今生化為烈焰",
    "B_Sun_Conjunct_SouthNode":     "對方的核心自我精準落在你的南交點，逃不掉的前世因果",
    "B_Moon_Conjunct_SouthNode":    "對方的情感喚醒你前世最深的記憶，注定要重逢的靈魂",
    "B_Venus_Conjunct_SouthNode":   "對方的愛意觸碰你的南交點，前世的情緣今生再度牽引",
    "B_Mars_Conjunct_SouthNode":    "對方的慾望引爆你的業力記憶，前世未解的糾葛今生再戰",
    # North Node triggers (北交點 — 靈魂成長方向)
    "A_Sun_Conjunct_NorthNode":     "你的核心自我指向對方的靈魂成長方向，是推動彼此進化的貴人",
    "A_Moon_Conjunct_NorthNode":    "你的情感共鳴對方未來的成長軌跡，一起前進的命運夥伴",
    "A_Venus_Conjunct_NorthNode":   "你的愛意引領對方走向靈魂想去的地方，是愛也是進化的催化劑",
    "A_Mars_Conjunct_NorthNode":    "你的行動力推動對方走上命定的軌道，帶著火焰的靈魂引路人",
    "B_Sun_Conjunct_NorthNode":     "對方的核心自我指向你的靈魂成長方向，是推動你進化的引路人",
    "B_Moon_Conjunct_NorthNode":    "對方的情感共鳴你未來的成長軌跡，命中注定的靈魂旅伴",
    "B_Venus_Conjunct_NorthNode":   "對方的愛意引領你走向靈魂想去的地方，既溫柔又深遠的業力緣",
    "B_Mars_Conjunct_NorthNode":    "對方的行動力推動你走上命定的軌道，是激勵你前進的一把火",
    # Descendant triggers (第七宮正緣 — 婚姻伴侶指標)
    "A_Sun_Conjunct_Descendant":    "你的核心自我精準落入對方的婚姻宮，你就是他命中注定的另一半",
    "A_Moon_Conjunct_Descendant":   "你的情感本能落入對方的婚姻宮，跟你在一起有回家般的安定感",
    "A_Venus_Conjunct_Descendant":  "你的愛與美感完美嵌進對方的伴侶宮，天生的正緣吸引力",
    "B_Sun_Conjunct_Descendant":    "對方的核心自我落入你的婚姻宮，他就是你靈魂深處尋覓的另一半",
    "B_Moon_Conjunct_Descendant":   "對方的情感本能落入你的婚姻宮，在一起就像回到最安心的歸宿",
    "B_Venus_Conjunct_Descendant":  "對方的愛意完美嵌入你的伴侶宮，命定般的正緣連結",
    # Sign Axis (星座軸線 — 個人進化課題)
    "Axis_Sign_Aries_Libra":        "白羊↔天秤軸線：學習在獨立自我與合作共贏之間找到平衡",
    "Axis_Sign_Taurus_Scorpio":     "金牛↔天蠍軸線：在物質安穩與靈魂深度轉化之間拉扯",
    "Axis_Sign_Gemini_Sag":         "雙子↔射手軸線：落地溝通與高遠理想之間的靈魂拔河",
    "Axis_Sign_Cancer_Cap":         "巨蟹↔摩羯軸線：柔軟情感與冷酷成就之間的生命抉擇",
    "Axis_Sign_Leo_Aquarius":       "獅子↔水瓶軸線：展現個人熱情與服務群體理想的拉鋸",
    "Axis_Sign_Virgo_Pisces":       "處女↔雙魚軸線：現實秩序與靈性混沌之間的永恆課題",
    # North Node Sign (北交星座 — 靈魂成長方向)
    "North_Node_Sign_Aries":        "北交白羊：此生要學會勇敢做自己，不再為迎合他人而委屈",
    "North_Node_Sign_Taurus":       "北交金牛：此生要建立內在的平靜與自我價值，放下對危機的執念",
    "North_Node_Sign_Gemini":       "北交雙子：此生要學會落地溝通，放下高高在上的哲學與逃避",
    "North_Node_Sign_Cancer":       "北交巨蟹：此生要打開柔軟的心，放下過度追求成就的冷酷面具",
    "North_Node_Sign_Leo":          "北交獅子：此生要勇敢展現自我光芒，不再躲在人群中當旁觀者",
    "North_Node_Sign_Virgo":        "北交處女：此生要腳踏實地建立秩序，放下靈性混沌的逃避傾向",
    "North_Node_Sign_Libra":        "北交天秤：此生要學會合作與雙贏，放下獨斷獨行的慣性",
    "North_Node_Sign_Scorpio":      "北交天蠍：此生要擁抱深度轉化，放下對物質舒適圈的依賴",
    "North_Node_Sign_Sagittarius":  "北交射手：此生要追求更高的智慧與視野，放下瑣碎的資訊焦慮",
    "North_Node_Sign_Capricorn":    "北交摩羯：此生要承擔起責任與使命，放下過度依賴情感的習慣",
    "North_Node_Sign_Aquarius":     "北交水瓶：此生要為群體理想服務，放下對個人光環的執著",
    "North_Node_Sign_Pisces":       "北交雙魚：此生要信任直覺與靈性，放下對完美秩序的過度控制",
    # House Axis (宮位軸線 — Tier 1 限定，靈魂戰場)
    "Axis_House_1_7":               "1↔7宮軸線：自我認同與婚姻伴侶的宿命拉扯",
    "Axis_House_2_8":               "2↔8宮軸線：個人財富與共享資源（含性慾）的深層課題",
    "Axis_House_3_9":               "3↔9宮軸線：日常溝通與哲學信仰之間的靈魂拔河",
    "Axis_House_4_10":              "4↔10宮軸線：家庭根基與事業使命的生命抉擇",
    "Axis_House_5_11":              "5↔11宮軸線：個人創造力與群體理想的平衡課題",
    "Axis_House_6_12":              "6↔12宮軸線：日常服務與靈性修行之間的永恆功課",
}

_ELEMENT_ZH = {
    "Fire":  "火（衝勁/野心）",
    "Earth": "土（安全感/落地）",
    "Air":   "風（思維/溝通）",
    "Water": "水（情感/直覺）",
}


def _translate_psych_tags(tags: list[str]) -> str:
    """Convert English tag names → human-readable Chinese bullet list."""
    if not tags:
        return "無明顯心理觸發"
    lines = []
    for t in tags:
        desc = _PSYCH_TAG_ZH.get(t, t)
        lines.append(f"• {desc}")
    return "\n".join(lines)


def _element_summary(ep: dict | None) -> str:
    """Summarise element_profile dict → concise Chinese string."""
    if not ep:
        return "資料不足"
    deficiency = ep.get("deficiency", [])
    dominant = ep.get("dominant", [])
    parts: list[str] = []
    if deficiency:
        parts.append("靈魂黑洞: " + "、".join(_ELEMENT_ZH.get(e, e) for e in deficiency))
    if dominant:
        parts.append("溢出能量: " + "、".join(_ELEMENT_ZH.get(e, e) for e in dominant))
    return "；".join(parts) if parts else "四元素均衡"


def _profile_context(deficiency: list, dominant: list, sm_tags: list) -> str:
    """Build additional character context hints for the profile prompt."""
    hints: list[str] = []
    if deficiency:
        elem_hints = {
            "Fire":  "壓抑自己的野心與衝勁，不敢爭取",
            "Earth": "缺乏安全感，很難完全放鬆",
            "Air":   "在表達思想時有障礙或過度分析",
            "Water": "迴避深層情感，難以完全敞開",
        }
        for e in deficiency:
            h = elem_hints.get(e)
            if h:
                hints.append(h)
    if dominant:
        elem_hints = {
            "Fire":  "野心強烈、行動力爆棚，但容易燃燒自己",
            "Earth": "極度務實穩重，但可能過於保守",
            "Air":   "思維敏銳、善於溝通，但容易想太多",
            "Water": "情感豐沛、直覺強，但容易被情緒淹沒",
        }
        for e in dominant:
            h = elem_hints.get(e)
            if h:
                hints.append(h)
    if "Natural_Dom" in sm_tags or "Daddy_Dom" in sm_tags:
        hints.append("骨子裡有掌控一切的慾望，但可能對自己這面有些抗拒")
    if "Anxious_Sub" in sm_tags:
        hints.append("在親密關係中容易過度付出，渴望被接住的安全感")
    if not hints:
        return ""
    return "【命盤解讀提示（提供給你的參考，不要直接輸出給用戶）】\n" + "\n".join(f"- {h}" for h in hints)


def _pick_mode(match_data: dict, mode: str) -> str:
    """Resolve 'auto' to a concrete mode based on primary_track + high_voltage."""
    if mode != "auto":
        return mode
    high_voltage = match_data.get("high_voltage", False)
    spiciness = (match_data.get("zwds") or {}).get("spiciness_level", "")
    if high_voltage or spiciness in ("HIGH_VOLTAGE", "SOULMATE"):
        return "abyss"
    primary = match_data.get("primary_track", "")
    if primary in ("soul",):
        return "abyss"
    if primary in ("passion",):
        return "hunt"
    if primary in ("partner",):
        return "nest"
    return "friend"


# ── 軌道專屬指令段 ───────────────────────────────────────────────────────────

_SOUL_INSTRUCTION = """\
【本次任務：靈魂/修羅模式】
這是一份「靈魂手術」級別的關係報告。語氣帶著看透世俗的知己口吻，解析這段關係如何觸碰他們底層的匱乏與創傷。
嚴禁說教；把所有心理標籤翻譯成具體行為。每個段落不可超過 4 句話。"""

_PASSION_INSTRUCTION = """\
【本次任務：激情/狩獵模式】
這是一份「致命吸引力與權力遊戲」的報告。語氣帶著誘惑力與現實的冷酷。
嚴禁說教；把所有 S/M 與依戀標籤，翻譯成兩人在權力與慾望上的具體拉扯。"""

_PARTNER_INSTRUCTION = """\
【本次任務：伴侶/築巢模式】
這是一份「生活合夥人與避風港」的報告。語氣溫暖、務實、令人安心，探討人類對秩序與安全感的歸屬渴望。
重點放在生活節奏互補與長久經營，而非激情。"""

_FRIEND_INSTRUCTION = """\
【本次任務：朋友/默契模式】
這是一份「智力共振與合作潛力」的解析報告。語氣專業、清晰、具備戰略性，探討純粹的思想交流與價值創造。
重點放在溝通模式與思維互補，而非浪漫。"""

_INSTRUCTION_MAP = {
    "abyss":  _SOUL_INSTRUCTION,
    "hunt":   _PASSION_INSTRUCTION,
    "nest":   _PARTNER_INSTRUCTION,
    "friend": _FRIEND_INSTRUCTION,
}

# ── Match Report Prompt (for /generate-archetype, Tab A) ─────────────────────

_MATCH_ARCHETYPE_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "archetype_tags": ["2-4字英文tag1", "tag2", "tag3"],
  "resonance": "一、初見面的致命引力（2-3句，點出他們是肉體費洛蒙吸引、還是前世南交點的熟悉感，不超過60字）",
  "shadow": "二、權力與失控的深淵（2-3句，解析他們在關係中誰掌握絕對話語權，或是什麼踩中了彼此的陰影，不超過60字）",
  "reality_check": ["❌ 絕對會踩爆的死穴1（≤12字）", "❌ 會痛的關卡2", "❌ 會痛的關卡3"],
  "evolution": ["👉 給你們的專屬解藥1（結合業力或現實建議，≤15字）", "👉 破局心法2", "👉 破局心法3"],
  "core": "五、命運箴言（一句話總結這段緣分的終極意義，不超過40字）"
}"""


def get_match_report_prompt(
    match_data: dict,
    mode: str = "auto",
    person_a: str = "A",
    person_b: str = "B",
) -> tuple[str, str]:
    """
    Build a DESTINY-worldview-enriched prompt for pairwise AI analysis (Tab A).

    Returns
    -------
    (prompt, effective_mode)
        prompt        — full string to pass to call_llm()
        effective_mode — the resolved mode ("abyss"/"hunt"/"nest"/"friend")
    """
    effective_mode = _pick_mode(match_data, mode)
    instruction = _INSTRUCTION_MAP.get(effective_mode, _SOUL_INSTRUCTION)

    tracks = match_data.get("tracks", {})
    power  = match_data.get("power", {})
    zwds   = match_data.get("zwds") or {}
    psych_tags   = match_data.get("psychological_tags", [])
    high_voltage = match_data.get("high_voltage", False)
    ep_a = match_data.get("element_profile_a")
    ep_b = match_data.get("element_profile_b")

    elem_context = ""
    if ep_a or ep_b:
        elem_context = (
            f"\n[八字與五行能量場]"
            f"\n{person_a} 能量: {_element_summary(ep_a)}"
            f"\n{person_b} 能量: {_element_summary(ep_b)}"
        )

    prompt = f"""{DESTINY_WORLDVIEW}

{instruction}

【本次任務：雙人宿命深度破防解析 (塔羅牌模式)】
請根據以下數據，寫出一份讓他們看懂彼此靈魂牽絆的報告。
如果出現「高壓警告」或「南/北交點/第7宮」等業力標籤，請在文字中強化「命中注定」與「痛並快樂著」的宿命感。

【輸入數據 — {person_a} × {person_b}】
VibeScore（肉體費洛蒙張力）: {round(match_data.get('lust_score', 0), 1)}/100
ChemistryScore（靈魂共鳴深度）: {round(match_data.get('soul_score', 0), 1)}/100
四軌: 朋友={round(tracks.get('friend', 0), 1)} 激情={round(tracks.get('passion', 0), 1)} 伴侶(正緣)={round(tracks.get('partner', 0), 1)} 靈魂(業力)={round(tracks.get('soul', 0), 1)}
主要連結類型: {match_data.get('primary_track', 'unknown')}
四象限落點: {match_data.get('quadrant', 'unknown')}
權力動態: {person_a}={power.get('viewer_role', 'Equal')}，{person_b}={power.get('target_role', 'Equal')}，RPV={power.get('rpv', 0)}
框架崩潰 (理智斷線): {power.get('frame_break', False)}
高壓警告 ⚡ (修羅場/禁忌感): {high_voltage}
紫微斗數烈度: {zwds.get('spiciness_level', 'N/A')}

【心理與業力分析結果（請將以下標籤轉譯為白話情境，禁止直接輸出原始英文標籤）】
{_translate_psych_tags(psych_tags)}
{elem_context}

{_MATCH_ARCHETYPE_SCHEMA}"""

    return prompt, effective_mode


# ── Simple Match Report Prompt (for /generate-match-report, Tab D) ───────────

_MATCH_REPORT_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "title": "這段關係的標題（8字以內）",
  "one_liner": "一句話描述這段關係的本質（詩意但直白，≤30字）",
  "sparks": ["🌟 現實相處的閃光點1（≤20字）", "🌟 閃光點2", "🌟 閃光點3"],
  "landmines": ["💣 必須跨越的現實雷區1（包裝成機會，≤20字）", "💣 雷區2"],
  "advice": "約100字的相處建議。請根據他們的權力動態與五行能量，給出非常具體、世俗可操作的建議（如：吵架時誰該先低頭）。",
  "core": "給兩人的療癒金句（≤40字）"
}"""


def get_simple_report_prompt(
    match_data: dict,
    mode: str = "auto",
    person_a: str = "A",
    person_b: str = "B",
) -> str:
    """
    Build prompt for Tab D structured relationship report.

    Uses the same worldview + track instruction, but outputs a simpler schema
    (title / one_liner / sparks / landmines / advice / core) for Tab D rendering.
    """
    effective_mode = _pick_mode(match_data, mode)
    instruction = _INSTRUCTION_MAP.get(effective_mode, _SOUL_INSTRUCTION)

    tracks = match_data.get("tracks", {})
    power  = match_data.get("power", {})
    zwds   = match_data.get("zwds") or {}
    psych_tags   = match_data.get("psychological_tags", [])
    high_voltage = match_data.get("high_voltage", False)
    ep_a = match_data.get("element_profile_a")
    ep_b = match_data.get("element_profile_b")

    elem_context = ""
    if ep_a or ep_b:
        elem_context = (
            f"\n[八字與五行能量場]"
            f"\n{person_a} 能量: {_element_summary(ep_a)}"
            f"\n{person_b} 能量: {_element_summary(ep_b)}"
        )

    prompt = f"""{DESTINY_WORLDVIEW}

{instruction}

【本次任務：雙人日常相處指南】
請根據以下數據，為這兩個人寫出一份「接地氣、具體可操作」的相處指南。
不需要過多玄妙的詞彙，專注於解決他們在現實生活中的「權力磨合」與「能量互補」。

【輸入數據 — {person_a} × {person_b}】
VibeScore（肉體吸引力）: {round(match_data.get('lust_score', 0), 1)}/100
ChemistryScore（靈魂深度）: {round(match_data.get('soul_score', 0), 1)}/100
四軌: 朋友={round(tracks.get('friend', 0), 1)} 激情={round(tracks.get('passion', 0), 1)} 伴侶={round(tracks.get('partner', 0), 1)} 靈魂={round(tracks.get('soul', 0), 1)}
主要連結類型: {match_data.get('primary_track', 'unknown')}
四象限: {match_data.get('quadrant', 'unknown')}
權力動態: {person_a}={power.get('viewer_role', 'Equal')}，{person_b}={power.get('target_role', 'Equal')}，RPV={power.get('rpv', 0)}
高壓警告 ⚡: {high_voltage}
紫微斗數烈度: {zwds.get('spiciness_level', 'N/A')}

【心理動力學分析結果（請將以下標籤轉譯為白話情境，禁止直接輸出原始英文標籤）】
{_translate_psych_tags(psych_tags)}
{elem_context}

{_MATCH_REPORT_SCHEMA}"""

    return prompt


# ── Profile Prompt (for /generate-profile-card, Tab C) ───────────────────────

_PROFILE_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "headline": "3-6字的靈魂標題（例：溫柔颶風、沉默的引爆器）",
  "shadow_trait": "迷人的反派特質（2-3句，點出他壓抑的野性或福德宮的焦慮，告訴他這其實是魅力來源，≤60字）",
  "avoid_types": ["❌ 絕對要避開的對象類型1（≤8字）", "❌ 類型2", "❌ 類型3", "❌ 類型4"],
  "evolution": ["👉 給你的破局心法1（結合他的南北交點或紫微命格，≤15字）", "👉 心法2", "👉 心法3"],
  "core": "一到二句療癒金句作結（≤40字）"
}"""


def get_profile_prompt(
    chart_data: dict,
    rpv_data: dict,
    attachment_style: str = "secure",
) -> str:
    """
    Build a DESTINY-worldview-enriched prompt for single-user profile (Tab C).
    整合西占(心理業力)、八字(能量驅力)、紫微(命宮與福德宮精神狀態)。
    """
    # 1. 提取西占與心理數據
    ep = chart_data.get("element_profile") or {}
    deficiency = ep.get("deficiency", [])
    dominant   = ep.get("dominant", [])

    sm_tags    = chart_data.get("sm_tags", [])
    karmic     = chart_data.get("karmic_tags", [])
    all_tags   = sm_tags + karmic

    elem_context = _element_summary(ep)

    # 2. 提取八字數據
    bazi = chart_data.get("bazi") or {}
    bazi_day_master = bazi.get("day_master", "?")
    bazi_element    = chart_data.get("bazi_element", "?")

    # 3. 提取紫微斗數數據 (命宮與福德宮)
    zwds = chart_data.get("zwds") or {}
    palaces = zwds.get("palaces", {})

    # 命宮 (外在宿命與核心人設)
    life_palace = palaces.get("ming", {})
    life_stars = ", ".join(life_palace.get("main_stars", [])) if life_palace.get("main_stars") else "無主星 (極易受環境與他人影響)"

    # 福德宮 (內在精神世界、潛意識焦慮)
    karma_palace = palaces.get("karma", {})
    karma_stars = ", ".join(karma_palace.get("main_stars", [])) if karma_palace.get("main_stars") else "無主星"
    karma_bad = ", ".join(karma_palace.get("malevolent_stars", [])) if karma_palace.get("malevolent_stars") else "無煞星"

    # 依戀風格中文轉換
    att_zh = {"secure": "安全依戀", "anxious": "焦慮依戀", "avoidant": "迴避依戀"}.get(
        attachment_style, attachment_style
    )

    prompt = f"""{DESTINY_WORLDVIEW}

【本次任務：單人靈魂深度解析】
根據以下「西占、八字、紫微」三位一體命盤數據，為這個人生成一份「撕下標籤後的自我解析」報告。
語氣要極度個人化，直接用「你...」開場，陳述那些他知道但從不承認的事。字字珠璣，短句，接地氣。

【命理系統核心定調】
1. 八字 (能量與驅力)：日主五行決定了他的行事作風與底層能量。
2. 西占 (心理與業力)：行星揭示了心理防禦機制，而「南北交點」指出了他此生的靈魂進化方向。
3. 紫微 (宿命與精神)：「命宮」是他這輩子的對外人設，而「福德宮」藏著他最深層的潛意識焦慮與精神黑洞。

【輸入數據】
[一、八字結構]
日主五行: {bazi_day_master}（{bazi_element}）

[二、西占與關係心理學]
太陽星座 (核心自我): {chart_data.get('sun_sign', 'unknown')}
月亮星座 (內在安全感): {chart_data.get('moon_sign', 'unknown') or '（無精確時間）'}
上升星座 (面具與防禦): {chart_data.get('ascendant_sign', 'unknown') or '（無精確時間）'}
火星星座 (行動與防衛): {chart_data.get('mars_sign', 'unknown')}
金星星座 (價值與愛): {chart_data.get('venus_sign', 'unknown')}
元素結構: {elem_context}
依戀風格: {att_zh}
衝突模式: {rpv_data.get('rpv_conflict', 'unknown')}
權力偏好: {rpv_data.get('rpv_power', 'unknown')}
能量模式: {rpv_data.get('rpv_energy', 'unknown')}

[三、紫微斗數精神狀態]
命宮主星 (核心人設): {life_stars}
福德宮主星 (精神世界): {karma_stars}
福德宮煞星 (精神焦慮與黑洞): {karma_bad}

【心理與業力特徵（請轉譯為白話，禁止直接輸出原始標籤）】
{_translate_psych_tags(all_tags)}

{_profile_context(deficiency, dominant, sm_tags)}

{_PROFILE_SCHEMA}"""

    return prompt


# ── Ideal Match Profile Prompt (for /generate-ideal-match, Tab C) ─────────────

_IDEAL_MATCH_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "antidote": "【靈魂解毒劑】約150字：綜合八字的相處能量與西占的陰影，他總是陷入什麼輪迴？他真正需要、能治癒他的對象是什麼特質？不說星座，說具體行為。",
  "reality_anchors": [
    "👉 現實錨點1（≤20字，例如：對方必須能在你崩潰時保持安靜）",
    "👉 現實錨點2（≤20字）",
    "👉 現實錨點3（≤20字）"
  ],
  "core_need": "一句話道出這個人最深的靈魂渴望（≤20字）"
}"""


def get_ideal_match_prompt(chart_data: dict) -> str:
    """
    Build a DESTINY-worldview-enriched prompt for ideal partner profile (Tab C).
    整合西占(吸引)、八字(相處)、紫微斗數(終局)，並完美處理紫微「空宮借對宮」機制。
    """
    # 1. 提取西占數據
    ep = chart_data.get("element_profile") or {}
    deficiency = ep.get("deficiency", [])
    dominant   = ep.get("dominant", [])

    sm_tags    = chart_data.get("sm_tags", [])
    karmic     = chart_data.get("karmic_tags", [])
    all_tags   = sm_tags + karmic

    elem_context = _element_summary(ep)
    descendant = chart_data.get("houses", {}).get("descendant") or chart_data.get("house7_sign") or "（無精確時間）"
    juno_sign = chart_data.get("juno_sign", "unknown")

    # 2. 提取八字數據
    bazi = chart_data.get("bazi") or {}
    bazi_day_master = bazi.get("day_master", "?")
    bazi_element    = bazi.get("day_master_element") or chart_data.get("bazi_element", "?")
    bazi_trait      = bazi.get("element_profile", {}).get("desc", "未知")

    # 3. 提取紫微斗數數據 (處理空宮機制)
    zwds = chart_data.get("zwds") or {}
    palaces = zwds.get("palaces", {})
    spouse_palace = palaces.get("spouse", {})
    career_palace = palaces.get("career", {})

    spouse_is_empty = spouse_palace.get("is_empty", False)
    if spouse_is_empty or not spouse_palace.get("main_stars"):
        borrowed_stars = ", ".join(career_palace.get("main_stars", [])) if career_palace.get("main_stars") else "無主星"
        spouse_main_stars = f"空宮 (感情觀如變色龍，極易受環境影響。高度投射並依附於對宮事業宮能量：{borrowed_stars})"
    else:
        spouse_main_stars = ", ".join(spouse_palace.get("main_stars", []))

    spouse_bad_stars = ", ".join(spouse_palace.get("malevolent_stars", [])) if spouse_palace.get("malevolent_stars") else "無煞星"

    prompt = f"""{DESTINY_WORLDVIEW}

【本次任務：三位一體關係導航圖與理想伴侶輪廓】
你現在是 DESTINY 系統的首席關係領航員。這不是普通的算命，而是一張「從被動宿命到主動創造」的關係導航圖。
請根據以下三大命理體系的數據，描繪出此人靈魂真正渴求的「承載者」與「解毒劑」。

【命理系統核心定調】
1. 八字 (相處的姿態)：揭示基本性格、能量流動與安全感來源。
2. 西占 (吸引與承諾)：金星揭示心動的特質；而「婚神星(Juno)」與「下降星座(伴侶宮)」揭示他真正需要的婚姻與長期承諾對象。
3. 紫微 (關係的終局)：揭示婚姻與長期關係的現實修羅場。特別注意：若夫妻宮為「空宮」，代表其婚姻觀念具備「變色龍」特質，伴侶特質將高度投射並依附於其「事業」的狀態。

【輸入數據】
[一、八字結構 (相處姿態)]
日主: {bazi_day_master} ({bazi_element})
性格定調: {bazi_trait}

[二、西占星盤 (吸引與承諾)]
太陽星座 (自我): {chart_data.get('sun_sign', 'unknown')}
月亮星座 (潛意識需求): {chart_data.get('moon_sign', 'unknown') or '（無精確時間）'}
上升星座 (面具與費洛蒙): {chart_data.get('ascendant_sign', 'unknown') or '（無精確時間）'}
下降星座 (伴侶宮頭/婚姻歸宿): {descendant}
金星星座 (戀愛吸引): {chart_data.get('venus_sign', 'unknown')}
火星星座 (慾望行動): {chart_data.get('mars_sign', 'unknown')}
婚神星 (長期承諾/婚姻型態): {juno_sign}
元素結構: {elem_context}

[三、紫微斗數 (關係終局)]
夫妻宮主星: {spouse_main_stars}
夫妻宮煞星 (現實雷區): {spouse_bad_stars}

【心理與業力特徵（請轉譯為白話，禁止直接輸出原始標籤）】
{_translate_psych_tags(all_tags)}

{_profile_context(deficiency, dominant, sm_tags)}

{_IDEAL_MATCH_SCHEMA}"""

    return prompt
