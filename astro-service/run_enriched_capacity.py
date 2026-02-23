"""One-off script: Compute ENRICHED emotional capacity using ZWDS rules."""
import json
from chart import calculate_chart, compute_emotional_capacity
from zwds import compute_zwds_chart

# 1. 取得基本星盤
chart = calculate_chart(
    birth_date="1997-07-21",
    birth_time="precise",
    birth_time_exact="09:00",
    lat=25.033,
    lng=121.565,
    data_tier=1,
)

# 2. 取得紫微命盤
zwds = compute_zwds_chart(1997, 7, 21, "09:00", "F")

# 3. 執行紫微加權修正 (Only for Tier 1)
enriched_capacity = compute_emotional_capacity(chart, zwds)

print(f"原始西洋情緒承載力: {chart['emotional_capacity']}")
print(f"紫微加權後情緒承載力: {enriched_capacity}")
print(f"最終修正值: {enriched_capacity - chart['emotional_capacity']}")
