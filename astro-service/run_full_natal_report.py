"""
DESTINY - Full Natal Report Integrator (Algorithm v1.9)
Combines Western Chart, BaZi, and ZWDS into one consolidated output.
"""
import json
from chart import calculate_chart, compute_emotional_capacity
from zwds import compute_zwds_chart

def generate_report(birth_date, birth_time_exact, lat=25.033, lng=121.565, gender="F"):
    # 1. Western Chart + BaZi + Psychology (v1.9)
    # ---------------------------------------------------------
    chart = calculate_chart(
        birth_date=birth_date,
        birth_time="precise",
        birth_time_exact=birth_time_exact,
        lat=lat,
        lng=lng,
        data_tier=1,
    )

    # 2. ZiWei DouShu (ZWDS)
    # ---------------------------------------------------------
    dt_parts = [int(x) for x in birth_date.split("-")]
    zwds = compute_zwds_chart(
        dt_parts[0], dt_parts[1], dt_parts[2], 
        birth_time_exact, gender
    )

    # 3. Enriched Emotional Capacity (ZWDS weighting)
    # ---------------------------------------------------------
    raw_capacity = chart["emotional_capacity"]
    enriched_capacity = compute_emotional_capacity(chart, zwds)
    chart["emotional_capacity"] = enriched_capacity
    chart["zwds_adjustment"] = enriched_capacity - raw_capacity

    # 4. Final Consolidation
    # ---------------------------------------------------------
    full_report = {
        "ident": {
            "birth_date": birth_date,
            "birth_time": birth_time_exact,
            "gender": gender
        },
        "western_astrology": {
            "planets": {k: v for k, v in chart.items() if "_sign" in k or "_degree" in k or "_rx" in k},
            "houses": {
                "ascendant": chart.get("ascendant_sign"),
                "descendant": chart.get("house7_sign"),
                "ic": chart.get("house4_sign"),
                "mc": chart.get("house10_sign"), # if available
                "house8": chart.get("house8_sign"),
                "house12": chart.get("house12_sign")
            },
            "aspects": chart.get("natal_aspects", [])
        },
        "psychology": {
            "sm_tags": chart.get("sm_tags", []),
            "karmic_tags": chart.get("karmic_tags", []),
            "emotional_capacity": chart.get("emotional_capacity"),
            "element_profile": chart.get("element_profile", {})
        },
        "bazi": chart.get("bazi", {}),
        "zwds": zwds
    }

    return full_report

if __name__ == "__main__":
    # 範例：1997-07-21 09:00 Female
    report = generate_report("1997-07-21", "09:00", gender="F")
    
    print("="*60)
    print(" DESTINY FULL NATAL REPORT (Consolidated) ")
    print("="*60)
    print(json.dumps(report, ensure_ascii=False, indent=2))
