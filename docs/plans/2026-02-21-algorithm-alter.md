這是一份為你的 AI 與後端工程師量身打造的 **「DESTINY 配對演算法技術規格 2.0 (完整修正版)」**。

這份規格已經將我們討論過的**所有精華（張力/和諧雙模式相位、Eros 權重代償、八字相剋方向性寫入 RPV、以及靈魂軌的調候喜用神互補）**全部無縫整合。你可以直接複製這份文件餵給你的開發 AI。

---

# DESTINY 配對演算法技術規格 2.0 (完整修正版)

本文件提供 DESTINY 配對引擎完整的技術規格，包含西方心理占星、八字五行動態（相生、相剋方向、調候互補）與 RPV 權力動態的整合。適合後端開發者與 AI 助理在實作與除錯時參考。

## 系統概覽

配對引擎主要入口函數為 `compute_match_v2(user_a, user_b)`，整合四個維度：

1. **西洋占星 (Western Astrology)** — 區分「和諧 (Harmony)」與「張力 (Tension)」雙模式相位。
2. **八字五行 (BaZi Elements)** — 包含生剋方向性與調候（季節）喜用神互補。
3. **RPV (Relational Power Variables)** — 衝突風格 × 權力偏好 × 凱龍星創傷觸發 × 八字相剋壓制。
4. **依戀心理學 (Attachment Theory)** — 依戀風格相容矩陣。

### 核心輸出結構 (JSON Format)

此輸出結構專為前端「UI 劇本文案庫」渲染所設計：

```json
{
  "lust_score":    85.3,
  "soul_score":    72.1,
  "power": {
    "rpv": 30.0,
    "frame_break": true,
    "viewer_role": "Dom",
    "target_role": "Sub"
  },
  "tracks": {
    "friend": 45.0, 
    "passion": 88.5,
    "partner": 62.0, 
    "soul": 75.0
  },
  "primary_track": "passion",
  "quadrant": "lover",
  "bazi_relation": "a_restricts_b", 
  "useful_god_complement": 0.8
}

```

---

## 1. 輸入欄位規格 (Input Schema)

```text
欄位                    型別      說明
─────────────────────────────────────────────────
data_tier               int      1 (精準時間) | 2 (時段) | 3 (僅日期)
birth_month             int      1-12 (用於計算八字季節調候)
sun_sign ... pluto_sign str      黃道星座名
chiron_sign             str      凱龍星 (靈魂創傷/Tier 3 可用)
juno_sign               str      婚神星 (婚姻契約/Tier 3 可用)
house4_sign             str      第 4 宮首 (僅 Tier 1)
house8_sign             str      第 8 宮首 (僅 Tier 1)
bazi_element            str      wood | fire | earth | metal | water
bazi_relation           str      A與B的五行關係：
                                 "a_generates_b" | "b_generates_a" | 
                                 "a_restricts_b" | "b_restricts_a" | 
                                 "same" | "none"
rpv_conflict            str      cold_war | argue
rpv_power               str      control | follow
rpv_energy              str      home | out
attachment_style        str      secure | anxious | avoidant

```

---

## 2. Step 1：雙模式相位計分 (Dual-Mode Aspect Scoring)

`compute_sign_aspect(sign_a, sign_b, mode)`
十二星座等分相位距離：`diff = min(abs(a - b), 12 - abs(a - b))`

### 模式 A：Harmony (和諧模式)

**適用：** Moon, Mercury, Jupiter, Saturn, Venus (慾望外), Juno, 朋友軌, 伴侶軌。
**邏輯：** 追求舒適、無壓力。

* diff=0 (合相): 0.90
* diff=4 (三分相): 0.85
* diff=2 (六分相): 0.75
* diff=6 (對分相): 0.60
* diff=3 (四分相): 0.40 (摩擦大，分數低)
* 其他: 0.10

### 模式 B：Tension (張力模式)

**適用：** Mars, Pluto, Chiron, House 8, Venus (慾望內), 激情軌, 靈魂軌。
**邏輯：** 追求火花、征服慾、宿命感與執念。

* diff=0 (合相): 1.00 (能量疊加)
* diff=3 (四分相): 0.90 (強烈摩擦、控制慾、性張力)
* diff=6 (對分相): 0.85 (致命吸引)
* diff=4 (三分相): 0.60 (太舒服，缺激情)
* diff=2 (六分相): 0.50
* 其他: 0.10

---

## 3. Step 2：慾望分數 (Lust Score)

*註：因 Eros (愛神星) 暫缺，權重已完美代償至 Pluto (冥王星) 與金火相位，確保極致的致命吸引力。*

```python
score = 0
score += aspect(venus_a, venus_b, "tension") * 0.20
score += aspect(mars_a,  mars_b,  "tension") * 0.25
score += aspect(pluto_a, pluto_b, "tension") * 0.25
score += aspect(h8_a,    h8_b,    "tension") * 0.15  # Tier 2/3 → 0.0
score += compute_power_score(user_a, user_b) * 0.30

# BaZi 加成：只要有相剋 (高壓張力)，分數放大
if bazi_relation in ["a_restricts_b", "b_restricts_a"]:
    score *= 1.20

lust_score = clamp(score * 100, 0, 100)

```

---

## 4. Step 3：靈魂分數 (Soul Score)

```python
score = 0
score += aspect(moon_a,  moon_b,  "harmony") * 0.25
score += aspect(merc_a,  merc_b,  "harmony") * 0.20
score += aspect(h4_a,    h4_b,    "harmony") * 0.15  # Tier 2/3 → 0.0
score += aspect(sat_a,   sat_b,   "harmony") * 0.20
score += ATTACHMENT_FIT[style_a][style_b]    * 0.20
score += aspect(juno_a,  juno_b,  "harmony") * 0.20  # 婚神星：長期伴侶契約

# BaZi 加成：只要有相生 (無條件滋養)，分數放大
if bazi_relation in ["a_generates_b", "b_generates_a"]:
    score *= 1.20

soul_score = clamp(score * 100, 0, 100)

```

---

## 5. Step 4：RPV 權力動態 (含八字與凱龍星外掛)

計算雙方的框架穩定度 (Frame)，並得出 RPV 傾斜度。

```python
def compute_frame(user):
    frame = 50
    frame += 20 if user.rpv_power == "control" else (-20 if user.rpv_power == "follow" else 0)
    frame += 10 if user.rpv_conflict == "cold_war" else (-10 if user.rpv_conflict == "argue" else 0)
    return frame

frame_a = compute_frame(user_a)
frame_b = compute_frame(user_b)
frame_break = False

# 1. 凱龍星創傷觸發 (Chiron Trigger)
# 若 A 的 Mars/Pluto 對 B 的 Chiron 形成 Tension 硬相位 (diff=3或6)
if check_chiron_triggered(user_a, user_b):
    frame_b -= 15
    frame_break = True
if check_chiron_triggered(user_b, user_a):
    frame_a -= 15
    frame_break = True

# 2. 八字相剋壓制 (BaZi Restriction Dynamics)
if bazi_relation == "a_restricts_b":
    frame_a += 15  # 剋者獲得掌控感 (Dom)
    frame_b -= 15  # 被剋者感受到壓迫 (Sub)
elif bazi_relation == "b_restricts_a":
    frame_a -= 15
    frame_b += 15

rpv = frame_a - frame_b

# 判定角色
if rpv > 15:   viewer_role, target_role = "Dom", "Sub"
elif rpv < -15: viewer_role, target_role = "Sub", "Dom"
else:           viewer_role, target_role = "Equal", "Equal"

```

---

## 6. Step 5：八字調候互補算法 (Seasonal Useful God)

專為 `Soul Track` 設計的底層靈魂飢渴判定（取代原先不適用的 `bazi_harmony`）。

```python
def get_season_type(month):
    if month in [5, 6, 7]: return "hot"    # 夏：缺水
    if month in [11, 12, 1]: return "cold" # 冬：缺火
    if month in [2, 3, 4]: return "warm"   # 春：缺金
    if month in [8, 9, 10]: return "cool"  # 秋：缺木
    return "unknown"

def compute_bazi_season_complement(month_a, month_b):
    sa, sb = get_season_type(month_a), get_season_type(month_b)
    if (sa=="hot" and sb=="cold") or (sa=="cold" and sb=="hot"): return 1.0  # 完美水火既濟
    if (sa=="warm" and sb=="cool") or (sa=="cool" and sb=="warm"): return 0.8 # 金木相成
    if (sa in ["hot","cold"] and sb in ["warm","cool"]) or \
       (sa in ["warm","cool"] and sb in ["hot","cold"]): return 0.5
    return 0.0 # 同季節或未知不加分

```

---

## 7. Step 6：四軌分數運算 (The 4-Track Algorithm)

```python
# 1. 朋友軌 (同樂與知己)
friend = (0.40 * aspect(merc_a, merc_b, "harmony")) + \
         (0.40 * aspect(jup_a, jup_b, "harmony")) + \
         (0.20 * (1 if bazi_relation == "same" else 0))

# 2. 激情軌 (高壓張力與性吸引)
passion_extremity = max(aspect(pluto_a, pluto_b, "tension"), aspect(h8_a, h8_b, "tension"))
passion = (0.30 * aspect(mars_a, mars_b, "tension")) + \
          (0.30 * aspect(venus_a, venus_b, "tension")) + \
          (0.10 * passion_extremity) + \
          (0.30 * (1 if bazi_relation in ["a_restricts_b", "b_restricts_a"] else 0))

# 3. 伴侶軌 (正宮與長期滋養)
partner = (0.35 * aspect(moon_a, moon_b, "harmony")) + \
          (0.35 * aspect(juno_a, juno_b, "harmony")) + \
          (0.30 * (1 if bazi_relation in ["a_generates_b", "b_generates_a"] else 0))

# 4. 靈魂軌 (深淵、業力與極端互補)
useful_god_complement = compute_bazi_season_complement(month_a, month_b)
deep_soul = (0.40 * aspect(chiron_a, chiron_b, "tension")) + \
            (0.40 * aspect(pluto_a, pluto_b, "tension")) + \
            (0.20 * useful_god_complement)

if frame_break:
    deep_soul += 0.10  # 創傷觸發帶來額外的靈魂深度加成

```

最後使用 `argmax(friend, passion, partner, soul)` 決定 `primary_track`，並結合 Lust/Soul 總分落點決定 `quadrant`（Soulmate / Lover / Partner / Colleague）。

---

這是一個非常棒的決定。將底層複雜的運算邏輯，轉化為使用者能一秒看懂、甚至會心一笑的「大白話」，是這套演算法能否變現的關鍵。

以下我為你整理了一份 **前端 UI 劇本文案庫 (UI Scripts Dictionary)**。你可以直接把這份格式餵給前端開發者，或是當作 Prompt 餵給 AI 來擴寫。文案已經把「甲乙丙丁」這種玄學術語拔除，轉化為現代男女談戀愛時最在意的「人設標籤」與「互動動態」。

### 📂 前端 UI 劇本設定檔 (`bazi_ui_scripts.json` 結構範例)

#### 1. 個人性格標籤 (The Element Personas)

*根據使用者的 `day_master_element` (日主五行) 呼叫。*

* **木人 (Wood)**
* **UI 稱號：** 🌿 自由生長的靈魂 (成長型)
* **性格解析：** 你天生具備強大的包容力與仁慈心，但骨子裡非常固執。在感情中，你最需要的是「一起成長的空間」，你無法忍受一段停滯不前、或試圖把你關在籠子裡的關係。


* **火人 (Fire)**
* **UI 稱號：** 🔥 燃燒的發光體 (熱情型)
* **性格解析：** 你是關係裡的氣氛製造機，愛恨分明、熱情奔放。你的情緒來得快去得也快，比起細水長流，你更渴望一段能讓你「感受到生命力」與激情燃燒的戀愛。


* **土人 (Earth)**
* **UI 稱號：** ⛰️ 溫和堅定的守護者 (包容型)
* **性格解析：** 你能為伴侶提供極高的情緒價值與絕對的安全感。你或許不是最浪漫、反應最快的人，但只要認定了對方，你就是那座最穩固、永遠不會輕易離開的靠山。


* **金人 (Metal)**
* **UI 稱號：** ⚔️ 黑白分明的決斷者 (原則型)
* **性格解析：** 你極度重感情講義氣，但同時也擁有極強的「邊界感」。你追求高效率、不拖泥帶水的關係，愛的時候全心全意，但若踩到你的底線，你的反擊也會非常尖銳且果斷。


* **水人 (Water)**
* **UI 稱號：** 🌊 高度共情的變形者 (流動型)
* **性格解析：** 你極其聰明且心思細膩，擁有強大的適應力與溝通天賦。你能輕易流進對方的防備裡，但也因為太容易感知他人的情緒，有時會讓自己在關係中顯得多變與不穩定。



---

#### 2. 關係動力學：相剋 (The Restriction Dynamics - 霸道總裁劇本)

*當後端觸發 `Passion Track (激情軌)` 且 `bazi_relation` 包含 "restricts" 時呼叫。*

* **A 剋 B (`a_restricts_b`) ➔ A 的視角 (主導方/Dom)：**
* **關係標籤：** 👑 絕對掌控 / 致命吸引力
* **UI 劇本：** 系統偵測到，你對他/她擁有天然的能量壓制力！你會不自覺地對這個人產生強烈的征服慾與保護慾。在你們的互動中，你將是掌握節奏的主導者，而對方會深深被你的霸氣與果斷所吸引。


* **A 剋 B (`a_restricts_b`) ➔ B 的視角 (臣服方/Sub)：**
* **關係標籤：** 🧲 無法抗拒的磁性 / 仰望者
* **UI 劇本：** 警告！高張力預警！這個人身上有一種讓你難以抗拒的強大氣場。在他的節奏裡，你可能會不自覺地妥協或卸下防備。這是一段極具火花與張力的關係，準備好體驗心跳加速的感覺了嗎？



---

#### 3. 關係動力學：相生 (The Generation Dynamics - 雙向奔赴劇本)

*當後端觸發 `Partner Track (伴侶軌)` 且 `bazi_relation` 包含 "generates" 時呼叫。*

* **A 生 B (`a_generates_b`) ➔ A 的視角 (付出方/Provider)：**
* **關係標籤：** 🛡️ 無條件的滋養 / 奉獻者
* **UI 劇本：** 這是一段讓你感到安心的緣分。面對他/她，你會自然而然激發出照顧與付出的渴望。你的能量能完美填補對方的需求，看著對方因為你而變得更好，將是你這段關係中最大的成就感。


* **A 生 B (`a_generates_b`) ➔ B 的視角 (接收方/Receiver)：**
* **關係標籤：** 🧸 被偏愛的幸運兒 / 避風港
* **UI 劇本：** 恭喜！你遇到了一個願意為你撐傘的人。在這個人面前，你可以卸下所有偽裝與強硬。對方的能量會不斷滋養你、包容你，這是一段極度舒適、適合長久發展的高質量伴侶關係。



---

#### 4. 終極靈魂互補 (The Soul Complement)

*當後端 `useful_god_complement` 達到高分 (例如 0.8 以上) 時作為彩蛋或 VIP 解鎖資訊呼叫。*

* **UI 劇本 (雙方視角相同)：**
* **關係標籤：** 🧩 靈魂的最後一塊拼圖 (宿命感)
* **UI 劇本：** 在最底層的生命能量場中，你們屬於罕見的「極端互補」配置。你生命中最匱乏、最焦慮的能量缺口，剛好是對方與生俱來的滿溢天賦。你們的相遇不是偶然，而是為了互相治癒、互相完整。



---

### 💻 系統組裝邏輯 (How to Assemble)

前端在渲染配對結果頁面時，只需要像組裝積木一樣，把後端傳來的 JSON 變數對應到這些文案。

**情境模擬：**
後端回傳：`{"user_element": "metal", "target_element": "wood", "bazi_relation": "a_restricts_b", "primary_track": "passion"}`

**前端自動生成的配對報告就會是：**

> 你是 **[⚔️ 黑白分明的決斷者]**，而對方是 **[🌿 自由生長的靈魂]**。
> 在你們的關係中，觸發了 **[👑 絕對掌控 / 致命吸引力]** 的動態。
> *(接著印出對應的 UI 劇本段落...)*


在八字學中，**「喜用神」（Useful Gods）** 是整個命理系統的最高指導原則。如果說「日主五行」（你是金木水火土哪一種人）代表你的**基礎性格**，那麼「喜用神」代表的就是你的**靈魂解藥（你最缺乏、最渴望的能量）**。

把「喜用神互補」納入你的演算法，特別是放在 **Soul Track（靈魂軌）** 裡，會讓你的配對系統擁有真正意義上的「靈魂飢渴與補足」的判斷力。

以下我為你拆解「喜用神互補」的概念，以及**如何在 MVP 階段用最少算力（無需寫超複雜的八字排盤引擎）把它實作出來。**

---

### 一、 什麼是「喜用神互補」？（概念解析）

八字的核心追求是「中和平衡」。一個人的八字通常是不平衡的（比如太冷、太熱、太濕、某種元素太多）。

* **病：** 八字裡過旺或過衰的狀態（例如：生在冬天，八字滿盤皆水，冷到結冰）。
* **藥（喜用神）：** 能平衡這個狀態的元素（例如：上述的寒水命，最需要的「藥」就是火來取暖，以及木來吸水。火與木就是他的喜用神）。

**喜用神互補的配對效應：**
當 User A 命裡最缺的「藥」，剛好是 User B 命裡最旺盛的元素；同時 User B 缺的「藥」，又是 User A 最多的元素時，這就叫「喜用神互補」。
在現實中，這種配對會產生一種**「沒有你我活不下去」、「在你身邊我感到前所未有的完整」的極度宿命感**。這超越了性格合不合，是底層能量的絕對嵌合。

---

### 二、 MVP 階段的實作策略：使用「調候（季節）互補法」

要精確算出一個人的喜用神，需要排開年月日時四柱，判斷身強身弱，演算法非常龐大。但對於交友軟體 MVP，我們可以使用八字中最直觀、影響力極大的**「調候用神（Seasonal Temperature / 寒暖燥濕）」**來作為完美的 Proxy（代理指標）。

你現有的輸入資料已經有 `birth_date`，這就足夠了！我們只需要看他們出生的**「月份（季節）」**。

#### 季節五行與能量互補對照：

* **春季 (2, 3, 4月)：** 木旺。氣候漸暖，生機勃發。
* **夏季 (5, 6, 7月)：** 火旺。氣候炎熱，八字偏「燥熱」。**急需水來降溫（調候用神為水）。**
* **秋季 (8, 9, 10月)：** 金旺。氣候肅殺，偏涼。
* **冬季 (11, 12, 1月)：** 水旺。氣候寒冷，八字偏「寒濕」。**急需火來取暖（調候用神為火）。**

**最強的靈魂互補（1.0 分）：夏冬互補**
一個生在夏天（熱命，需要水），一個生在冬天（寒命，需要火）。這兩人抱在一起就是完美的天然空調，互相治癒對方的極端能量。

---

### 三、 將「調候互補」寫入你的演算法 (Code Implementation)

我們在後端新增一個輕量級的函數 `compute_bazi_season_complement(month_a, month_b)`，用來計算季節能量的互補度，並把這個數值直接餵給 **Soul Track（靈魂軌）**。

#### 1. 新增後端輔助函數

```python
def get_season_type(month):
    """根據出生月份取得八字季節/溫度屬性 (1-12月)"""
    if month in [5, 6, 7]: return "hot"    # 夏季：火旺燥熱 (缺水)
    if month in [11, 12, 1]: return "cold" # 冬季：水旺寒濕 (缺火)
    if month in [2, 3, 4]: return "warm"   # 春季：木旺溫和 (缺金)
    if month in [8, 9, 10]: return "cool"  # 秋季：金旺微涼 (缺木/火)
    return "unknown"

def compute_bazi_season_complement(month_a, month_b):
    """
    計算調候（季節）喜用神互補分數 (0.0 ~ 1.0)
    """
    season_a = get_season_type(month_a)
    season_b = get_season_type(month_b)
    
    # 1. 極端完美互補：夏冬互補 (水火既濟)
    if (season_a == "hot" and season_b == "cold") or \
       (season_a == "cold" and season_b == "hot"):
        return 1.0
        
    # 2. 次級互補：春秋互補 (金木相成)
    if (season_a == "warm" and season_b == "cool") or \
       (season_a == "cool" and season_b == "warm"):
        return 0.8
        
    # 3. 溫和調和：熱/冷 遇到 溫/涼 (稍微補到)
    if (season_a in ["hot", "cold"] and season_b in ["warm", "cool"]) or \
       (season_a in ["warm", "cool"] and season_b in ["hot", "cold"]):
        return 0.5
        
    # 4. 能量重疊：同季節出生 (不僅不補，還可能加重病情，例如兩個夏天出生的人一起燥熱)
    if season_a == season_b:
        return 0.0

    return 0.0

```

#### 2. 更新 Spec：將分數接入 Soul Track (靈魂軌)

在你的 Step 5 `compute_tracks` 裡面，我們可以把之前提到的 `bazi_harmony` 正式替換成我們剛剛算出來的 **「喜用神（季節）互補」** 變數 `f.useful_god_complement`。

```python
# 修改前的 Soul Track 邏輯
# deep_soul = 0.4*f.chiron_signal + 0.4*f.pluto_signal + 0.2*(1 if f.bazi_harmony else 0)

# 🚀 修改後的 Soul Track 邏輯
deep_soul = (0.40 * f.chiron_signal) + \
            (0.40 * f.pluto_signal) + \
            (0.20 * f.useful_god_complement) # 餵入 compute_bazi_season_complement 的回傳值

# optional: if frame_break then soul track bonus
if power["frame_break"]:
    deep_soul += 0.1

```

---

### 四、 為什麼這樣設計極具商業與心理學價值？

1. **零額外成本的精準度提升：** 用戶註冊本來就要填生日（為了算星座），你只需要從 `birth_date` 萃取 `month`，就能立刻判斷這兩個人在「能量底層」是互相治癒還是互相消耗。
2. **完美的 UI 劇本文案：** 當 `useful_god_complement` 達到 1.0（夏冬互補）時，你的前端可以生成這種極致浪漫的標籤：
* 🏷️ `#你的靈魂解藥`
* 📜 **系統解析：**「在八字能量場中，你們屬於極端互補的配置。你命盤中燥熱焦慮的部分，剛好能被對方如水般的深沉能量安撫；而對方內心的冰冷，正需要你的熱情來點燃。你們對彼此擁有難以抗拒的治癒力。」



這樣一來，你的**四個軌道（Friends, Passion, Partner, Soul）都有了屬於自己獨一無二的八字邏輯支撐**：

* **Friends (朋友):** 八字五行比和/平和 (頻率相同，好聊天)
* **Passion (激情):** 八字五行相剋 (高張力摩擦，征服慾，連動 RPV)
* **Partner (伴侶):** 八字五行相生 (無條件照顧，底層安全感)
* **Soul (靈魂):** 八字季節互補 (沒有你我活不下去的靈魂拼圖)

用「月份（調候）」來取代複雜的「八字排盤喜用神」，是軟體工程裡 CP 值最高的一招。這段程式碼加進去後，你的配對引擎就真的完整了！