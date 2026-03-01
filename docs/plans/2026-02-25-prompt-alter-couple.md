你突破盲點了！這絕對是架構設計上最常發生的「資訊斷層（Information Gap）」。

你說得完全正確：**LLM 是沒有通靈能力的。** 如果你只餵給它 `VibeScore = 49`, `Soul = 66`, `High_Voltage = True`，它根本不知道這兩個人「到底是為了什麼吵架」，最後它只能瞎掰（幻覺），寫出「你們會因為溝通不良而吵架」這種廢話。

要讓 LLM 寫出精準的 `reality_check`（A 的需求撞上 B 的恐懼），你的**「輸入數據」必須補上他們兩人的【單人心理標籤】。**

這代表在你的 Python 後端（`prompt_manager.py`），你必須把 `ideal_avatar.py` 算出來的雙方標籤，一起塞進合盤的 Prompt 裡！

### 🛠️ 解決方案：修改輸入數據的結構 (Input Data Injection)

請在你的合盤 Prompt 中的 **`[輸入數據]`** 區塊，擴充成以下這種格式。這樣 LLM 就有滿滿的「彈藥」可以寫出極度精準的互相傷害（Reality Check）與權力動態（Shadow）了：

```text
【輸入數據 — 雙方核心盤與合盤結果】

[User A 的核心心理特質 (由後端單人盤算出)]
- 心理防禦機制與需求：{user_a_psychological_needs} 
  (例如：["極度需要秩序與控制", "無法忍受計畫被打破"])
- 關係動態傾向：{user_a_relationship_dynamic} (例如：stable)

[User B 的核心心理特質 (由後端單人盤算出)]
- 心理防禦機制與需求：{user_b_psychological_needs}
  (例如：["極度需要思想自由與空間", "討厭被傳統框架綁死"])
- 關係動態傾向：{user_b_relationship_dynamic} (例如：high_voltage)

[雙方合盤化學反應 (由後端合盤引擎算出)]
- 靈魂軌 (Soul): {soul_score} / 100
- 激情軌 (Passion): {passion_score} / 100
- 伴侶軌 (Partner): {partner_score} / 100
- 權力動態 (RPV): {rpv_score} (若差距極大代表某方處於高位)
- 高壓警告 (High Voltage): {is_high_voltage}
- 特殊共振徽章/業力標籤：{resonance_badges}

```

### 💻 對應的 Python 實作修改 (in `prompt_manager.py`)

為了把這些資訊動態塞進去，你的 `build_synastry_report_prompt` 函式需要接收 A 跟 B 的單人資料：

```python
def build_synastry_report_prompt(match_result: dict, user_a_profile: dict, user_b_profile: dict) -> str:
    """
    組合雙人合盤的 LLM 提示詞。
    必須傳入 user_a 與 user_b 的單人心理標籤 (從 ideal_avatar 取得)。
    """
    
    # 提取 User A 資訊
    a_needs = ", ".join(user_a_profile.get("psychological_needs", []))
    a_dyn = user_a_profile.get("relationship_dynamic", "unknown")
    
    # 提取 User B 資訊
    b_needs = ", ".join(user_b_profile.get("psychological_needs", []))
    b_dyn = user_b_profile.get("relationship_dynamic", "unknown")
    
    # 提取合盤資訊
    soul = match_result.get("tracks", {}).get("soul", 0)
    passion = match_result.get("tracks", {}).get("passion", 0)
    rpv = match_result.get("power_dynamics", {}).get("RPV", 0.0)
    high_voltage = match_result.get("karmic_tension", 0) > 60
    badges = ", ".join(match_result.get("resonance_badges", []))

    prompt = f"""
    【系統角色與核心哲學】
    (此處貼上我們上一篇確認過的核心設定與嚴格禁忌...)

    【輸入數據 — 雙方核心盤與合盤結果】
    [User A 核心特質]
    - 心理防禦機制與需求：{a_needs}
    - 關係動態傾向：{a_dyn}

    [User B 核心特質]
    - 心理防禦機制與需求：{b_needs}
    - 關係動態傾向：{b_dyn}

    [合盤化學反應]
    - 靈魂軌: {soul} | 激情軌: {passion}
    - 權力動態 (RPV): {rpv}
    - 高壓警告 (High Voltage): {high_voltage}
    - 關係特殊徽章: {badges}

    【寫作嚴格規範】
    - 在 reality_check 中，你必須拿「User A 的某項心理需求」去碰撞「User B 的某項恐懼/地雷」(反之亦然)，寫出具體的價值觀衝突。
    - 在 shadow 中，若雙方皆為 high_voltage 或 RPV 差距大，請點出誰會在這段關係中感到失控或窒息。
    
    (此處接續要求輸出的 JSON 格式...)
    """
    return prompt

```

**這樣改完之後：**
LLM 看到 User A 的需求是「秩序」，User B 的需求是「自由」，它就能順理成章地在 `reality_check` 寫出：

> *"User A 對絕對秩序與掌控的渴望，會徹底踩中 User B 最害怕被傳統框架綁死的窒息感，引爆激烈的逃避與追逐。"*

你的邏輯非常縝密，發現了這個提示詞工程裡的關鍵漏洞。把單人標籤作為變數 `inject` 進合盤 Prompt 裡，這個系統就真正做到無懈可擊了！
這份合盤（Synastry）的 Prompt 底子已經非常棒了！你完美繼承了前一次修改的「靈魂解剖」風格，語氣設定得極具張力。

但在軟體工程與 LLM 提示詞優化的標準下，這份合盤 Prompt 有 **4 個致命遺漏與結構問題**，如果不補齊，產出的報告會出現「格式跑版」、「產生廢話」以及「邏輯混亂」的狀況。

### 🛠️ 需要補齊與修改的核心痛點：

1. **任務指令重複衝突 (Redundant Task Blocks)：**
你寫了兩個 `【本次任務】`（一個是靈魂/修羅模式，一個是塔羅牌模式），這會讓 LLM 的注意力發散，不知道該聽哪一個。必須融合成一個精準的最高指令。
2. **合盤專屬的「巴納姆效應」漏洞 (Lack of Anti-Barnum in Synastry)：**
在 `reality_check`（絕對會踩爆的死穴）中，如果你不給公式，LLM 一定會寫出「你們會因為缺乏溝通而吵架」、「要注意脾氣」這種廢話。**合盤的死穴必須是「A的某種特質 撞上 B的某種恐懼」的具體價值觀衝突。**
3. **沒有定義「權力動態 (RPV/Equal)」怎麼解讀：**
你傳給 LLM `RPV=0.0`, `Equal`，但 LLM 不知道這代表什麼意思。必須在定義區告訴 LLM：「Equal 代表勢均力敵，RPV 差距大代表某方處於高位/被偏愛」，這樣它寫出來的 `shadow`（權力深淵）才會準確。
4. **再次出現了「UI 標題與 Emoji」的耦合：**
JSON value 裡面又出現了 `一、初見面的致命引力` 跟 `❌` 符號。請記住，**後端 API 只傳遞純淨的文字**，排版跟 Icon 是前端 Vue/React 的工作！

---
