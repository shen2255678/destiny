"""
DESTINY — LLM Prompt Manager
Assembles DESTINY-worldview-enriched prompts for AI report generation.

Three public functions:
  get_match_report_prompt(match_data, mode, person_a, person_b)
      → (prompt: str, effective_mode: str)
      Used by /generate-archetype and /generate-match-report

  get_profile_prompt(chart_data, rpv_data, attachment_style)
      → prompt: str
      Used by /generate-profile-card

  get_simple_report_prompt(match_data, person_a, person_b)
      → prompt: str
      Used by /generate-match-report (Tab D, structured report format)
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
    "A_Heals_B_Moon":               "你的存在直接療癒對方最脆弱的情緒創傷核心",
    "B_Heals_A_Moon":               "對方的存在直接療癒你最脆弱的情緒創傷核心",
    "B_Triggers_A_Wound":           "對方無意間踩中你的原生創傷，既痛又上癮",
    "A_Triggers_B_Wound":           "你無意間踩中對方的原生創傷，關係帶著不可思議的張力",
    "A_Illuminates_B_Shadow":       "你照亮了對方不敢承認的陰暗面，注定是業力之緣",
    "B_Illuminates_A_Shadow":       "對方照亮了你不敢承認的陰暗面，是強迫你成長的存在",
    "Mutual_Shadow_Integration":    "你們互相照見彼此最深的陰影，這段關係是靈魂的修羅場",
    "Karmic_Love_Venus_Rx":         "總覺得自己不配被愛，吸引帶著宿命感的業力關係",
    "Suppressed_Anger_Mars_Rx":     "憤怒長期壓抑，平時溫和，壓到極限才會爆發",
    "Internal_Dialogue_Mercury_Rx": "思考極度深邃，但很難用世俗語言表達內心世界",
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
  "resonance": "一、宿命共振或致命引力（2-3句，不超過60字）",
  "shadow": "二、陰影照妖鏡或權力遊戲（2-3句，不超過60字）",
  "reality_check": ["❌ 會痛的關卡1（≤10字）", "❌ 會痛的關卡2", "❌ 會痛的關卡3"],
  "evolution": ["👉 進化心法1（≤12字）", "👉 進化心法2", "👉 進化心法3"],
  "core": "五、總結金句（一到二句，不超過40字）"
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
            f"\n{person_a} 元素: {_element_summary(ep_a)}"
            f"\n{person_b} 元素: {_element_summary(ep_b)}"
        )

    prompt = f"""{DESTINY_WORLDVIEW}

{instruction}

【輸入數據 — {person_a} × {person_b}】
VibeScore（肉體吸引力）: {round(match_data.get('lust_score', 0), 1)}/100
ChemistryScore（靈魂深度）: {round(match_data.get('soul_score', 0), 1)}/100
四軌: 朋友={round(tracks.get('friend', 0), 1)} 激情={round(tracks.get('passion', 0), 1)} 伴侶={round(tracks.get('partner', 0), 1)} 靈魂={round(tracks.get('soul', 0), 1)}
主要連結類型: {match_data.get('primary_track', 'unknown')}
四象限: {match_data.get('quadrant', 'unknown')}
權力動態: {person_a}={power.get('viewer_role', 'Equal')}，{person_b}={power.get('target_role', 'Equal')}，RPV={power.get('rpv', 0)}
框架崩潰: {power.get('frame_break', False)}
高壓警告 ⚡: {high_voltage}
ZWDS 烈度: {zwds.get('spiciness_level', 'N/A')}
系統標籤: {', '.join(match_data.get('labels', [])) or '無'}

【心理動力學分析結果（請轉譯為白話，禁止直接輸出原始標籤）】
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
  "sparks": ["閃光點1（≤20字）", "閃光點2", "閃光點3"],
  "landmines": ["成長課題1（包裝成機會，≤20字）", "成長課題2"],
  "advice": "約100字的相處建議，具體可操作，直接用你們開場",
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

    prompt = f"""{DESTINY_WORLDVIEW}

{instruction}

【輸入數據 — {person_a} × {person_b}】
VibeScore（肉體吸引力）: {round(match_data.get('lust_score', 0), 1)}/100
ChemistryScore（靈魂深度）: {round(match_data.get('soul_score', 0), 1)}/100
四軌: 朋友={round(tracks.get('friend', 0), 1)} 激情={round(tracks.get('passion', 0), 1)} 伴侶={round(tracks.get('partner', 0), 1)} 靈魂={round(tracks.get('soul', 0), 1)}
主要連結類型: {match_data.get('primary_track', 'unknown')}
四象限: {match_data.get('quadrant', 'unknown')}
權力動態: {person_a}={power.get('viewer_role', 'Equal')}，{person_b}={power.get('target_role', 'Equal')}，RPV={power.get('rpv', 0)}
高壓警告 ⚡: {high_voltage}
ZWDS 烈度: {zwds.get('spiciness_level', 'N/A')}
系統標籤: {', '.join(match_data.get('labels', [])) or '無'}

【心理動力學分析結果（請轉譯為白話，禁止直接輸出原始標籤）】
{_translate_psych_tags(psych_tags)}

{_MATCH_REPORT_SCHEMA}"""

    return prompt


# ── Profile Prompt (for /generate-profile-card, Tab C) ───────────────────────

_PROFILE_SCHEMA = """\
請只回傳以下 JSON，不要包含任何其他文字或 markdown：
{
  "headline": "3-6字的靈魂標題（例：溫柔颶風、沉默的引爆器）",
  "shadow_trait": "迷人的反派特質（2-3句，點出他壓抑的野性，告訴他這其實是魅力來源，≤60字）",
  "avoid_types": ["❌ 絕對要避開的對象類型1（≤8字）", "❌ 類型2", "❌ 類型3", "❌ 類型4"],
  "evolution": ["👉 給你的破局心法1（≤12字）", "👉 心法2", "👉 心法3"],
  "core": "一到二句療癒金句作結（≤40字）"
}"""


def get_profile_prompt(
    chart_data: dict,
    rpv_data: dict,
    attachment_style: str = "secure",
) -> str:
    """
    Build a DESTINY-worldview-enriched prompt for single-user profile (Tab C).

    chart_data : return value of /calculate-chart
    rpv_data   : {rpv_conflict, rpv_power, rpv_energy}
    """
    ep = chart_data.get("element_profile") or {}
    deficiency = ep.get("deficiency", [])
    dominant   = ep.get("dominant", [])

    sm_tags    = chart_data.get("sm_tags", [])
    karmic     = chart_data.get("karmic_tags", [])
    all_tags   = sm_tags + karmic

    bazi = chart_data.get("bazi") or {}
    bazi_day_master = bazi.get("day_master", "?")
    bazi_element    = chart_data.get("bazi_element", "?")

    elem_context = _element_summary(ep)

    # Attachment style → human-readable
    att_zh = {"secure": "安全依戀", "anxious": "焦慮依戀", "avoidant": "迴避依戀"}.get(
        attachment_style, attachment_style
    )

    prompt = f"""{DESTINY_WORLDVIEW}

【本次任務：單人靈魂深度解析】
根據以下命盤數據，為這個人生成一份「撕下標籤後的自我解析」報告。
語氣要極度個人化，直接用「你...」開場，陳述那些他知道但從不承認的事。
字字珠璣，短句，接地氣。

【輸入數據】
太陽星座: {chart_data.get('sun_sign', 'unknown')}
月亮星座: {chart_data.get('moon_sign', 'unknown') or '（無精確時間）'}
上升星座: {chart_data.get('ascendant_sign', 'unknown') or '（無精確時間）'}
火星星座: {chart_data.get('mars_sign', 'unknown')}
金星星座: {chart_data.get('venus_sign', 'unknown')}
日主五行: {bazi_day_master}（{bazi_element}）
元素結構: {elem_context}
依戀風格: {att_zh}
衝突模式: {rpv_data.get('rpv_conflict', 'unknown')}
權力偏好: {rpv_data.get('rpv_power', 'unknown')}
能量模式: {rpv_data.get('rpv_energy', 'unknown')}

【心理與業力特徵（請轉譯為白話，禁止直接輸出原始標籤）】
{_translate_psych_tags(all_tags)}

{_profile_context(deficiency, dominant, sm_tags)}

{_PROFILE_SCHEMA}"""

    return prompt


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
