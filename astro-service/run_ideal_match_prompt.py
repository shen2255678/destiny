"""
DESTINY — Ideal Match Prompt Runner (三位一體大師級)
計算單人完整命盤後呼叫 get_ideal_match_prompt，選擇性打 Claude API。

使用方式：
  # 只印 prompt（不打 API）
  python run_ideal_match_prompt.py

  # 打 Claude Haiku API
  ANTHROPIC_API_KEY=sk-ant-... python run_ideal_match_prompt.py

  # 指定其他出生資料
  python run_ideal_match_prompt.py --date 1990-03-15 --time 14:30 --gender M
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from chart import calculate_chart, compute_emotional_capacity
from zwds import compute_zwds_chart
from prompt_manager import get_ideal_match_prompt


# ── 1. 排盤 ──────────────────────────────────────────────────────────────────

def build_natal_report(birth_date: str, birth_time: str, gender: str,
                       lat: float = 25.033, lng: float = 121.565) -> dict:
    """合併西占 + 八字 + 紫微，輸出 full_report。"""

    # 西占 + 八字 + 心理標籤
    chart = calculate_chart(
        birth_date=birth_date,
        birth_time="precise",
        birth_time_exact=birth_time,
        lat=lat,
        lng=lng,
        data_tier=1,
    )

    # 紫微斗數
    y, m, d = [int(x) for x in birth_date.split("-")]
    zwds = compute_zwds_chart(y, m, d, birth_time, gender)

    # 情感容量 ZWDS 加權
    raw_cap = chart.get("emotional_capacity")
    enriched_cap = compute_emotional_capacity(chart, zwds)
    chart["emotional_capacity"] = enriched_cap

    # 輸出 full_report（與 run_full_natal_report.py 同結構）
    full_report = {
        "ident": {"birth_date": birth_date, "birth_time": birth_time, "gender": gender},
        "western_astrology": {
            "planets": {k: v for k, v in chart.items()
                        if "_sign" in k or "_degree" in k or "_rx" in k},
            "houses": {
                "ascendant":  chart.get("ascendant_sign"),
                "descendant": chart.get("house7_sign"),
                "ic":         chart.get("house4_sign"),
                "mc":         chart.get("house10_sign"),
                "house8":     chart.get("house8_sign"),
                "house12":    chart.get("house12_sign"),
            },
            "aspects": chart.get("natal_aspects", []),
        },
        "psychology": {
            "sm_tags":          chart.get("sm_tags", []),
            "karmic_tags":      chart.get("karmic_tags", []),
            "emotional_capacity": enriched_cap,
            "element_profile":  chart.get("element_profile", {}),
        },
        "bazi": chart.get("bazi", {}),
        "zwds": zwds,
    }
    return full_report, chart


# ── 2. 將 full_report 壓平為 chart_data（get_ideal_match_prompt 所需格式） ──────

def flatten_to_chart_data(full_report: dict, chart: dict) -> dict:
    """把 full_report 結構轉換成 prompt_manager 期望的扁平 chart_data。"""
    planets = full_report["western_astrology"]["planets"]
    psych   = full_report["psychology"]

    chart_data = {
        # 西占行星星座（直接從 planets dict 提取）
        **{k: v for k, v in planets.items() if k.endswith("_sign")},
        # 西占行星逆行
        **{k: v for k, v in planets.items() if k.endswith("_rx")},
        # 宮位（供 descendant 取用）
        "houses": full_report["western_astrology"]["houses"],
        # 心理標籤
        "sm_tags":       psych["sm_tags"],
        "karmic_tags":   psych["karmic_tags"],
        "element_profile": psych["element_profile"],
        # 八字（完整 dict，供 bazi.get("day_master") 等讀取）
        "bazi": full_report["bazi"],
        # 紫微（完整 dict，含 palaces）
        "zwds": full_report["zwds"],
    }
    return chart_data


# ── 3. 呼叫 Claude（選擇性） ──────────────────────────────────────────────────

def call_claude(prompt: str, api_key: str, max_tokens: int = 900) -> str:
    try:
        from anthropic import Anthropic
    except ImportError:
        return "[ERROR] anthropic 套件未安裝：pip install anthropic"

    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DESTINY Ideal Match Prompt Runner")
    parser.add_argument("--date",   default="1997-07-21", help="生日 YYYY-MM-DD")
    parser.add_argument("--time",   default="09:00",      help="出生時間 HH:MM")
    parser.add_argument("--gender", default="F",          help="M / F")
    parser.add_argument("--lat",    type=float, default=25.033)
    parser.add_argument("--lng",    type=float, default=121.565)
    parser.add_argument("--show-chart",  action="store_true", help="印出完整命盤 JSON")
    parser.add_argument("--show-prompt", action="store_true", help="印出完整 prompt 文字")
    args = parser.parse_args()

    SEP = "=" * 65

    # ── Step 1: 排盤 ──────────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"  DESTINY 排盤中  {args.date} {args.time} {'女' if args.gender=='F' else '男'}")
    print(SEP)
    full_report, chart = build_natal_report(
        args.date, args.time, args.gender, args.lat, args.lng
    )

    if args.show_chart:
        print("\n【完整命盤 JSON】")
        print(json.dumps(full_report, ensure_ascii=False, indent=2))

    # 快速摘要
    wp = full_report["western_astrology"]["planets"]
    bazi = full_report["bazi"]
    print(f"\n【西占速覽】")
    print(f"  太陽 {wp.get('sun_sign')}  月亮 {wp.get('moon_sign')}  上升 {wp.get('ascendant_sign')}")
    print(f"  金星 {wp.get('venus_sign')}  火星 {wp.get('mars_sign')}  婚神 {wp.get('juno_sign')}")
    print(f"  下降 {wp.get('house7_sign')}  北交 {wp.get('north_node_sign')}  南交 {wp.get('south_node_sign')}")
    print(f"\n【八字速覽】")
    print(f"  日主 {bazi.get('day_master')} ({bazi.get('day_master_element')})")
    pillars = bazi.get("pillars", {})
    print(f"  四柱 {pillars.get('year','')} {pillars.get('month','')} {pillars.get('day','')} {pillars.get('hour','')}")
    zwds = full_report["zwds"]
    spouse = zwds.get("palaces", {}).get("spouse", {})
    ming   = zwds.get("palaces", {}).get("ming", {})
    print(f"\n【紫微速覽】")
    print(f"  命宮  {', '.join(ming.get('main_stars', []) or ['無主星'])}")
    print(f"  夫妻宮 {', '.join(spouse.get('main_stars', []) or ['空宮'])}  空宮={spouse.get('is_empty', False)}")
    karmic_tags = full_report["psychology"].get("karmic_tags", [])
    print(f"\n【業力軸線標籤】  {karmic_tags or '無'}")

    # ── Step 2: 組裝 prompt ───────────────────────────────────────
    chart_data = flatten_to_chart_data(full_report, chart)
    prompt = get_ideal_match_prompt(chart_data)

    if args.show_prompt:
        print(f"\n{SEP}")
        print("【完整 Prompt】")
        print(SEP)
        print(prompt)

    # ── Step 3: 呼叫 LLM（若有 API key）─────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(f"\n{SEP}")
        print("  未偵測到 ANTHROPIC_API_KEY，略過 LLM 呼叫。")
        print("  設定後重跑：ANTHROPIC_API_KEY=sk-ant-... python run_ideal_match_prompt.py")
        print(SEP)
        print("\n[Prompt 前 300 字預覽]")
        print(prompt[:300], "...")
        return

    print(f"\n{SEP}")
    print("  呼叫 Claude Haiku 中……")
    print(SEP)
    raw = call_claude(prompt, api_key)

    print("\n【AI 原始回傳】")
    print(raw)

    # 嘗試 parse JSON
    try:
        result = json.loads(raw)
        print(f"\n{SEP}")
        print("  理想伴侶輪廓（解析後）")
        print(SEP)
        print(f"\n💊 靈魂解毒劑：\n{result.get('antidote', '')}")
        print(f"\n🔩 現實錨點：")
        for anchor in result.get("reality_anchors", []):
            print(f"   {anchor}")
        print(f"\n✨ 最深渴望：{result.get('core_need', '')}")
    except json.JSONDecodeError:
        print("\n[WARN] JSON 解析失敗，請查看上方原始回傳")


if __name__ == "__main__":
    main()
