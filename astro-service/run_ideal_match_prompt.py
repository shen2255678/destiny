# -*- coding: utf-8 -*-
"""
DESTINY — Ideal Match Prompt Runner (透過 astro-service HTTP API)
呼叫本地 astro-service，組裝 Prompt，輸出可貼到 Google AI Studio。

【前置條件】astro-service 先跑起來（port 8001）

【如何改】直接修改下方 DEFAULT_* 常數，或用 CLI 參數：
  python run_ideal_match_prompt.py --date 1995-03-26 --time 14:30 --gender M

【如何跑（無 API key）】
  python run_ideal_match_prompt.py           # 印命盤速覽 + 完整 Prompt
  python run_ideal_match_prompt.py --copy-prompt   # 只印 Prompt 純文字（最適合複製）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("[ERROR] 請先安裝 requests：pip install requests")
    sys.exit(1)

from prompt_manager import get_ideal_match_prompt, get_match_report_prompt

try:
    from ideal_avatar import extract_ideal_partner_profile
    _HAS_IDEAL_AVATAR = True
except ImportError:
    _HAS_IDEAL_AVATAR = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 【修改這裡】預設測試對象的出生資料
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_DATE    = "1997-03-07"   # 出生日期 YYYY-MM-DD
DEFAULT_TIME    = "10:59"        # 出生時間 HH:MM（24小時制）
DEFAULT_GENDER  = "M"            # M = 男, F = 女
DEFAULT_LAT     = 25.033         # 出生地緯度（預設台北）
DEFAULT_LNG     = 121.565        # 出生地經度（預設台北）
DEFAULT_DATE2   = "1995-03-26"
DEFAULT_TIME2   = "14:30"
DEFAULT_GENDER2 = "F"
ASTRO_SERVICE   = "http://localhost:8001"   # astro-service 位址
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── 1. 呼叫 astro-service HTTP API ────────────────────────────────────────────

def call_api(endpoint: str, payload: dict) -> dict:
    """打 astro-service endpoint，回傳 JSON dict。"""
    url = f"{ASTRO_SERVICE}{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        print(f"\n❌ 無法連線到 {ASTRO_SERVICE}")
        print("   請先啟動 astro-service：uvicorn main:app --port 8001")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ API 呼叫失敗 {endpoint}: {e}")
        sys.exit(1)


def build_natal_report(birth_date: str, birth_time: str, gender: str,
                       lat: float, lng: float) -> tuple[dict, dict]:
    """透過 HTTP API 計算三大命理系統，整合成 full_report。"""
    y, m, d = [int(x) for x in birth_date.split("-")]

    # 西占 + 八字 + 心理標籤
    chart = call_api("/calculate-chart", {
        "birth_date": birth_date,
        "birth_time": "precise",
        "birth_time_exact": birth_time,
        "lat": lat,
        "lng": lng,
        "data_tier": 1,
    })

    # Fallback: 若服務版本較舊未回傳 house7_sign，從上升星座推算對宮（下降 = 上升對面）
    if not chart.get("house7_sign") and chart.get("ascendant_sign"):
        _OPPOSITE = {
            "aries": "libra",   "libra": "aries",
            "taurus": "scorpio", "scorpio": "taurus",
            "gemini": "sagittarius", "sagittarius": "gemini",
            "cancer": "capricorn",   "capricorn": "cancer",
            "leo": "aquarius",  "aquarius": "leo",
            "virgo": "pisces",  "pisces": "virgo",
        }
        chart["house7_sign"] = _OPPOSITE.get(chart["ascendant_sign"].lower())

    # 紫微斗數
    zwds = call_api("/compute-zwds-chart", {
        "birth_year": y, "birth_month": m, "birth_day": d,
        "birth_time": birth_time, "gender": gender,
    })

    full_report = {
        "ident": {"birth_date": birth_date, "birth_time": birth_time, "gender": gender},
        "western_astrology": {
            "planets": {k: v for k, v in chart.items()
                        if "_sign" in k or "_degree" in k or "_rx" in k},
            "houses": {
                "ascendant":  chart.get("ascendant_sign"),
                "descendant": chart.get("house7_sign"),
                "ic":         chart.get("house4_sign"),
                "house8":     chart.get("house8_sign"),
                "house12":    chart.get("house12_sign"),
            },
            "aspects": chart.get("natal_aspects", []),
        },
        "psychology": {
            "sm_tags":            chart.get("sm_tags", []),
            "karmic_tags":        chart.get("karmic_tags", []),
            "emotional_capacity": chart.get("emotional_capacity"),
            "element_profile":    chart.get("element_profile", {}),
        },
        "bazi": chart.get("bazi", {}),
        "zwds": zwds,
    }
    return full_report, chart


# ── 2. 壓平為 prompt_manager 所需格式 ────────────────────────────────────────

def flatten_to_chart_data(full_report: dict, chart: dict) -> dict:
    """把巢狀 full_report 結構轉成 get_ideal_match_prompt 期望的扁平格式。"""
    planets = full_report["western_astrology"]["planets"]
    psych   = full_report["psychology"]

    # house7_sign 可能在 planets 裡（因為 "_sign" in "house7_sign" == True）
    # 也可能在 chart (原始 API response) 裡直接讀
    house7 = planets.get("house7_sign") or chart.get("house7_sign")

    # 確保 houses dict 的 descendant 正確對應到 house7_sign
    houses = dict(full_report["western_astrology"]["houses"])
    houses["descendant"] = house7  # 強制覆蓋，確保 Tier 1 精確時間一定有值

    return {
        **{k: v for k, v in planets.items() if k.endswith("_sign")},
        **{k: v for k, v in planets.items() if k.endswith("_degree")},
        **{k: v for k, v in planets.items() if k.endswith("_rx")},
        "house7_sign":     house7,      # prompt_manager fallback 用
        "houses":          houses,      # prompt_manager 主要讀 houses.descendant
        "sm_tags":         psych["sm_tags"],
        "karmic_tags":     psych["karmic_tags"],
        "element_profile": psych["element_profile"],
        "bazi":            full_report["bazi"],
        "zwds":            full_report["zwds"],
    }


# ── 3. 合盤 Prompt 建構 ───────────────────────────────────────────────────────

def build_synastry_prompt(
    full_report_a: dict, chart_a: dict,
    full_report_b: dict, chart_b: dict,
) -> str:
    """Build enriched synastry prompt for two persons.

    Calls /compute-match for match scores, then injects individual
    psychology profiles from ideal_avatar locally (no DB required for CLI).
    """
    # Flatten both charts for /compute-match
    flat_a = flatten_to_chart_data(full_report_a, chart_a)
    flat_b = flatten_to_chart_data(full_report_b, chart_b)

    # /compute-match expects flat dicts with sign keys at top level
    match_resp = call_api("/compute-match", {"user_a": flat_a, "user_b": flat_b})

    # Compute individual profiles locally (no DB required for CLI)
    prof_a: dict = {}
    prof_b: dict = {}
    # Build complete western chart dicts that include natal_aspects so that
    # extract_ideal_partner_profile can use aspect data (Fix: natal_aspects
    # was previously silently dropped because the filtered planets sub-dict
    # only contained keys with _sign / _degree / _rx).
    western_a = {
        **full_report_a.get("western_astrology", {}).get("planets", {}),
        "natal_aspects": full_report_a.get("western_astrology", {}).get("aspects", []),
    }
    western_b = {
        **full_report_b.get("western_astrology", {}).get("planets", {}),
        "natal_aspects": full_report_b.get("western_astrology", {}).get("aspects", []),
    }
    if _HAS_IDEAL_AVATAR:
        try:
            prof_a = extract_ideal_partner_profile(
                western_a,
                full_report_a.get("bazi", {}),
                full_report_a.get("zwds", {}),
            )
        except Exception:
            pass
        try:
            prof_b = extract_ideal_partner_profile(
                western_b,
                full_report_b.get("bazi", {}),
                full_report_b.get("zwds", {}),
            )
        except Exception:
            pass

    # Build human-readable labels from birth date + gender
    ident_a = full_report_a["ident"]
    ident_b = full_report_b["ident"]
    label_a = f"{'女' if ident_a['gender'] == 'F' else '男'}({ident_a['birth_date'][5:]})"
    label_b = f"{'女' if ident_b['gender'] == 'F' else '男'}({ident_b['birth_date'][5:]})"

    prompt, mode = get_match_report_prompt(
        match_resp,
        person_a=label_a,
        person_b=label_b,
        user_a_profile=prof_a,
        user_b_profile=prof_b,
    )
    return prompt


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DESTINY Ideal Match Prompt Runner")
    parser.add_argument("--date",   default=DEFAULT_DATE,   help="出生日期 YYYY-MM-DD")
    parser.add_argument("--time",   default=DEFAULT_TIME,   help="出生時間 HH:MM")
    parser.add_argument("--gender", default=DEFAULT_GENDER, help="M / F")
    parser.add_argument("--lat",    type=float, default=DEFAULT_LAT)
    parser.add_argument("--lng",    type=float, default=DEFAULT_LNG)
    parser.add_argument("--synastry",  action="store_true",
                        help="合盤模式：計算兩人合盤並輸出 Prompt 到 synastry_output.txt")
    parser.add_argument("--date2",     default=DEFAULT_DATE2,   help="第二人出生日期 YYYY-MM-DD")
    parser.add_argument("--time2",     default=DEFAULT_TIME2,   help="第二人出生時間 HH:MM")
    parser.add_argument("--gender2",   default=DEFAULT_GENDER2, help="第二人性別 M / F")
    parser.add_argument("--show-chart",  action="store_true", help="印出完整命盤 JSON")
    parser.add_argument("--copy-prompt", action="store_true",
                        help="只輸出 Prompt 純文字（最適合整段複製）")
    args = parser.parse_args()

    SEP = "=" * 65

    # ── Step 1: 透過 API 排盤 ─────────────────────────────────────
    if not args.copy_prompt:
        print(f"\n{SEP}")
        print(f"  DESTINY 排盤中  {args.date} {args.time} {'女' if args.gender=='F' else '男'}")
        print(f"  呼叫 {ASTRO_SERVICE} ...")
        print(SEP)

    full_report, chart = build_natal_report(
        args.date, args.time, args.gender, args.lat, args.lng
    )

    if args.show_chart:
        print("\n【完整命盤 JSON】")
        print(json.dumps(full_report, ensure_ascii=False, indent=2))

    if not args.copy_prompt:
        wp      = full_report["western_astrology"]["planets"]
        bazi    = full_report["bazi"]
        palaces = full_report["zwds"].get("palaces", {})
        ming    = palaces.get("ming", {})
        spouse  = palaces.get("spouse", {})
        karma   = palaces.get("karma", {})

        print(f"\n【西占速覽】")
        print(f"  太陽 {wp.get('sun_sign')}  月亮 {wp.get('moon_sign')}  上升 {wp.get('ascendant_sign')}")
        print(f"  金星 {wp.get('venus_sign')}  火星 {wp.get('mars_sign')}  婚神 {wp.get('juno_sign')}")
        print(f"  伴侶宮(下降) {wp.get('house7_sign')}  北交 {wp.get('north_node_sign')}  南交 {wp.get('south_node_sign')}")
        print(f"\n【八字速覽】")
        print(f"  日主 {bazi.get('day_master')} ({bazi.get('day_master_element')})")
        pillars = bazi.get("four_pillars", {})
        def _pstr(p) -> str:
            return p.get("full", "") if isinstance(p, dict) else str(p or "")
        print(f"  四柱 {_pstr(pillars.get('year'))} {_pstr(pillars.get('month'))} {_pstr(pillars.get('day'))} {_pstr(pillars.get('hour'))}")
        print(f"\n【紫微速覽】")
        print(f"  命宮  {', '.join(ming.get('main_stars', []) or ['無主星'])}")
        print(f"  夫妻宮 {', '.join(spouse.get('main_stars', []) or ['空宮'])}  煞星={spouse.get('malevolent_stars', [])}")
        print(f"  福德宮 {', '.join(karma.get('main_stars', []) or ['無主星'])}")
        sm     = full_report["psychology"].get("sm_tags", [])
        karmic = full_report["psychology"].get("karmic_tags", [])
        print(f"\n【心理標籤】  SM={sm}  業力={karmic}")

    # ── Step 2: 組裝 Prompt ───────────────────────────────────────
    chart_data = flatten_to_chart_data(full_report, chart)
    prompt = get_ideal_match_prompt(chart_data)

    if args.copy_prompt:
        print(prompt)
        return

    # ── 印出完整 Prompt（手動貼到 Google AI Studio）──────────────
    print(f"\n{SEP}")
    print("  📋 完整 Prompt — 請全選複製，貼到 Google AI Studio")
    print(f"{SEP}")
    print("  🔗 https://aistudio.google.com")
    print("-" * 65)
    print(prompt)
    print("-" * 65)
    print(f"\n💡 只想要 Prompt 文字（方便全選）：")
    print(f"   py -3.12 run_ideal_match_prompt.py --copy-prompt")

    # ── Step 3 (optional): 合盤模式 ──────────────────────────────────────
    if args.synastry:
        if not args.copy_prompt:
            print(f"\n{SEP}")
            print(f"  合盤模式：排第二人 {args.date2} {args.time2} {'女' if args.gender2 == 'F' else '男'}")
            print(SEP)

        full_report_b, chart_b = build_natal_report(
            args.date2, args.time2, args.gender2, args.lat, args.lng
        )

        synastry_prompt = build_synastry_prompt(
            full_report, chart,
            full_report_b, chart_b,
        )

        # Write to file (avoids Windows cp950 encoding issues with Chinese/emoji in terminal)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synastry_output.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(synastry_prompt)

        if args.copy_prompt:
            sys.stdout.buffer.write(synastry_prompt.encode("utf-8"))
        else:
            print(f"\n合盤 Prompt 已寫入 {out_path}")
            print(f"💡 只輸出 Prompt 文字：py -3.12 run_ideal_match_prompt.py --synastry --copy-prompt")
        return


if __name__ == "__main__":
    main()
