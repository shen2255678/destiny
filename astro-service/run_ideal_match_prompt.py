# -*- coding: utf-8 -*-
"""
DESTINY — Ideal Match Prompt Runner (Pipeline 版)

【如何改】修改下方 DEFAULT_* 常數，或用 CLI 參數：
  python run_ideal_match_prompt.py --date 1995-03-26 --time 14:30 --gender M

【如何跑（無 API key）】
  python run_ideal_match_prompt.py           # 命盤速覽 + Prompt 寫檔
  python run_ideal_match_prompt.py --copy-prompt   # 只印 Prompt（方便複製）
  python run_ideal_match_prompt.py --synastry      # 加合盤模式
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from destiny_pipeline import DestinyPipeline, BirthInput

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 【修改這裡】預設測試對象
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_DATE    = "1997-03-07"
DEFAULT_TIME    = "10:59"
DEFAULT_GENDER  = "M"
DEFAULT_LAT     = 25.033
DEFAULT_LNG     = 121.565
DEFAULT_DATE2   = "1995-03-26"
DEFAULT_TIME2   = "14:30"
DEFAULT_GENDER2 = "F"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _pstr(p) -> str:
    """Extract full pillar string from dict or str."""
    if isinstance(p, dict):
        return p.get("full", p.get("stem", "") + p.get("branch", ""))
    return str(p or "")


def print_chart_summary(label: str, chart: dict, zwds: dict | None) -> None:
    """Print quick chart overview to stdout (ASCII only)."""
    bazi    = chart.get("bazi") or {}
    pillars = bazi.get("four_pillars") or {}
    palaces = (zwds or {}).get("palaces") or {}
    ming    = palaces.get("life") or palaces.get("ming") or {}
    spouse  = palaces.get("spouse") or {}
    karma   = palaces.get("karma") or {}
    SEP     = "-" * 55

    print(f"\n{SEP}")
    print(f"  {label}")
    print(SEP)
    print(f"  [Western]  Sun={chart.get('sun_sign')}  Moon={chart.get('moon_sign')}  ASC={chart.get('ascendant_sign')}")
    print(f"             Venus={chart.get('venus_sign')}  Mars={chart.get('mars_sign')}  Juno={chart.get('juno_sign')}")
    print(f"             DSC={chart.get('house7_sign')}  NNode={chart.get('north_node_sign')}")
    print(f"  [BaZi]     DayMaster={bazi.get('day_master')} ({bazi.get('day_master_element')})")
    pillars_str = " ".join(_pstr(pillars.get(k)) for k in ("year", "month", "day", "hour") if pillars.get(k))
    print(f"             Pillars={pillars_str}")
    if zwds:
        print(f"  [ZWDS]     Ming={', '.join(ming.get('main_stars') or ['?'])}")
        print(f"             Spouse={', '.join(spouse.get('main_stars') or ['empty'])}  evil={spouse.get('malevolent_stars', [])}")
        print(f"             Karma={', '.join(karma.get('main_stars') or ['?'])}")
    print(f"  [Psych]    SM={chart.get('sm_tags', [])}  Karmic={chart.get('karmic_tags', [])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DESTINY Ideal Match Prompt Runner")
    parser.add_argument("--date",        default=DEFAULT_DATE)
    parser.add_argument("--time",        default=DEFAULT_TIME)
    parser.add_argument("--gender",      default=DEFAULT_GENDER)
    parser.add_argument("--lat",         type=float, default=DEFAULT_LAT)
    parser.add_argument("--lng",         type=float, default=DEFAULT_LNG)
    parser.add_argument("--synastry",    action="store_true", help="合盤模式")
    parser.add_argument("--date2",       default=DEFAULT_DATE2)
    parser.add_argument("--time2",       default=DEFAULT_TIME2)
    parser.add_argument("--gender2",     default=DEFAULT_GENDER2)
    parser.add_argument("--show-chart",  action="store_true", help="印出完整命盤 JSON")
    parser.add_argument("--copy-prompt", action="store_true", help="只輸出 Prompt 純文字")
    args = parser.parse_args()

    # ── Build pipeline ─────────────────────────────────────────────────────
    person_a = BirthInput(args.date, args.time, args.gender, args.lat, args.lng)
    person_b = BirthInput(args.date2, args.time2, args.gender2, args.lat, args.lng) if args.synastry else None

    pipeline = DestinyPipeline(person_a, person_b)
    pipeline.compute_charts()
    if person_b:
        pipeline.compute_match()
    pipeline.extract_profiles().build_prompts()

    raw = pipeline.to_raw()

    # ── Show chart summary ─────────────────────────────────────────────────
    if not args.copy_prompt:
        label_a = f"{'F' if args.gender == 'F' else 'M'} {args.date} {args.time}"
        print_chart_summary(label_a, raw["chart_a"], raw["zwds_a"])
        if args.synastry:
            label_b = f"{'F' if args.gender2 == 'F' else 'M'} {args.date2} {args.time2}"
            print_chart_summary(label_b, raw["chart_b"], raw["zwds_b"])

    if args.show_chart:
        print("\n[Full chart JSON]")
        print(json.dumps(raw["chart_a"], ensure_ascii=False, indent=2))

    # ── Output prompt(s) ───────────────────────────────────────────────────
    base = os.path.dirname(os.path.abspath(__file__))

    if args.synastry:
        out = os.path.join(base, "synastry_output.txt")
        pipeline.to_prompt_file("synastry", out)
        if args.copy_prompt:
            sys.stdout.buffer.write(raw["prompts"]["synastry"].encode("utf-8"))
        else:
            print(f"\nDONE  synastry prompt -> {out}")
    else:
        out = os.path.join(base, "ideal_match_output.txt")
        pipeline.to_prompt_file("ideal_a", out)
        if args.copy_prompt:
            print(raw["prompts"]["ideal_a"])
        else:
            print(f"\nDONE  ideal_a prompt -> {out}")
            print(f"      {len(raw['prompts']['ideal_a'])} chars")
            print(f"\n  TIP: --copy-prompt to print only the prompt text")


if __name__ == "__main__":
    main()
